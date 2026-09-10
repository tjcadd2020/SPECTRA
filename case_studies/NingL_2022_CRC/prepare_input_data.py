#!/usr/bin/env python3
"""Prepare the normal-BMI NingL_2022 CRC cohort from published tables."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd


BMI_MIN = 18.5
BMI_MAX = 25.0
EXPECTED_COUNTS = {"HC": 64, "CL": 52}


def load_converter(skill_dir: Path):
    converter_file = skill_dir / "scripts/convert_species_names.py"
    spec = importlib.util.spec_from_file_location(
        "spectra_species_converter", converter_file
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load converter: {converter_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.convert_species_names, module.read_aliases, module.read_reference


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--bmi-metadata", type=Path, required=True)
    parser.add_argument("--skill-dir", type=Path, required=True)
    parser.add_argument("--project-id", default="PRJNA731589")
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    workbook = args.workbook.resolve()
    bmi_file = args.bmi_metadata.resolve()
    skill_dir = args.skill_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_metadata = pd.read_excel(workbook, sheet_name="S1|Sample Metadata")
    source_metadata = source_metadata.loc[
        source_metadata["DatasetID"].eq(args.project_id)
        & source_metadata["Category"].isin(["CRC-Control", "CRC-Disease"])
    ].copy()
    source_metadata = source_metadata.set_index("SampleName")
    source_metadata.index = source_metadata.index.astype(str)
    source_metadata.index.name = "sample_id"

    bmi_metadata = pd.read_csv(bmi_file, index_col=0)
    bmi_metadata.index = bmi_metadata.index.astype(str)
    bmi_column = "bmi" if "bmi" in bmi_metadata else "BMI"
    bmi_metadata[bmi_column] = pd.to_numeric(
        bmi_metadata[bmi_column], errors="coerce"
    )
    optional_columns = [
        column for column in ["Stage", "age", "sex"] if column in bmi_metadata
    ]
    metadata = source_metadata.join(
        bmi_metadata[[bmi_column, *optional_columns]], how="left"
    )
    metadata = metadata.rename(columns={"Category": "source_group", bmi_column: "BMI"})
    metadata["true_label"] = metadata["source_group"].map(
        {"CRC-Control": "HC", "CRC-Disease": "CL"}
    )
    metadata = metadata.loc[
        metadata["BMI"].ge(BMI_MIN) & metadata["BMI"].lt(BMI_MAX)
    ].copy()

    metadata_columns = [
        "DatasetID",
        "SRAStudy",
        "Country",
        "source_group",
        *optional_columns,
        "BMI",
        "true_label",
    ]
    metadata = metadata.loc[:, metadata_columns]
    if metadata["true_label"].value_counts().to_dict() != EXPECTED_COUNTS:
        raise ValueError(
            f"Unexpected normal-BMI class counts: "
            f"{metadata['true_label'].value_counts().to_dict()}"
        )

    profile = pd.read_excel(workbook, sheet_name="S2|Microbial profile")
    source_features = list(profile.columns[2:])
    abundance = profile.set_index("SampleName").loc[metadata.index, source_features]
    abundance = abundance.apply(pd.to_numeric, errors="raise")
    abundance.index = abundance.index.astype(str)
    abundance.index.name = "sample_id"
    if abundance.isna().any().any() or (abundance < 0).any().any():
        raise ValueError("The selected abundance matrix contains invalid values.")

    raw_relative_abundance = abundance.div(abundance.sum(axis=1), axis=0)
    raw_relative_abundance.to_csv(
        output_dir / "1. Raw relative abundance.csv", float_format="%.17g"
    )

    convert_names, read_aliases, read_reference = load_converter(skill_dir)
    reference = read_reference(skill_dir / "assets/spectra_canonical_1554.txt")
    aliases = read_aliases(skill_dir / "references/spectra_species_aliases.tsv")
    pd.DataFrame({"Taxon": source_features}).to_csv(
        output_dir / "2. Microbial features.csv", index=False
    )
    mapping = convert_names(source_features, reference, aliases)
    mapping.loc[:, ["Original taxon label", "Mapped feature name"]].to_csv(
        output_dir / "3. Taxon name mapping.csv"
    )

    converted = abundance.copy()
    converted.columns = mapping["Mapped feature name"]
    converted = converted.T.groupby(level=0, sort=False).sum().T
    # SPECTRA accepts relative abundance and performs preprocessing internally.
    prepared = converted.div(converted.sum(axis=1), axis=0)

    metadata.to_csv(output_dir / "0. metadata.csv", float_format="%.17g")
    prepared.to_csv(output_dir / "4. Name-converted relative abundance.csv", float_format="%.17g")

    print(f"Project: {args.project_id}")
    print(f"Samples: {len(metadata)}")
    print(metadata["true_label"].value_counts().to_string())
    print(f"Source species: {len(source_features)}")
    print(f"Prepared features: {prepared.shape[1]}")


if __name__ == "__main__":
    main()
