#!/usr/bin/env python3
"""Download and prepare the normal-BMI YachidaS_2019 cohort."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


RESOURCE = "2021-10-14.YachidaS_2019.relative_abundance"
BMI_MIN = 18.5
BMI_MAX = 25.0


def download_data(
    rscript: str, cache_dir: Path, abundance_file: Path, metadata_file: Path
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    r_code = f"""
    suppressWarnings(suppressPackageStartupMessages(library(ExperimentHub)))
    setExperimentHubOption("CACHE", {json.dumps(str(cache_dir))})
    invisible(ExperimentHub(localHub=FALSE))
    suppressWarnings(suppressPackageStartupMessages(library(curatedMetagenomicData)))
    obj <- suppressMessages(curatedMetagenomicData({json.dumps(RESOURCE)}, dryrun=FALSE))[[1]]
    abundance <- SummarizedExperiment::assay(obj)
    abundance <- abundance[grepl("|s__", rownames(abundance), fixed=TRUE), , drop=FALSE]
    metadata <- as.data.frame(SummarizedExperiment::colData(obj))
    metadata$sample_id <- rownames(metadata)
    write.csv(abundance, {json.dumps(str(abundance_file))}, quote=FALSE)
    write.csv(metadata, {json.dumps(str(metadata_file))}, row.names=FALSE)
    """
    subprocess.run([rscript, "-e", r_code], check=True)


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
    parser.add_argument("--skill-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument(
        "--cache-dir", type=Path, default=Path(".cache/ExperimentHub")
    )
    parser.add_argument("--rscript", default="Rscript")
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = args.cache_dir.resolve()
    abundance_download = cache_dir.parent / "YachidaS_2019_relative_abundance.csv"
    metadata_download = cache_dir.parent / "YachidaS_2019_metadata.csv"
    download_data(args.rscript, cache_dir, abundance_download, metadata_download)

    abundance_all = pd.read_csv(abundance_download, index_col=0).T
    abundance_all.index = abundance_all.index.astype(str)
    abundance_all.index.name = "sample_id"
    metadata_all = pd.read_csv(metadata_download, index_col="sample_id")
    metadata_all.index = metadata_all.index.astype(str)
    metadata_all["BMI"] = pd.to_numeric(metadata_all["BMI"], errors="coerce")

    label_map = {
        "CRC": "CL",
        "adenoma": "HC",
        "few_polyps": "HC",
        "healthy": "HC",
    }
    metadata = metadata_all.loc[metadata_all["disease"].isin(label_map)].copy()
    metadata = metadata.loc[
        metadata["BMI"].ge(BMI_MIN) & metadata["BMI"].lt(BMI_MAX)
    ].copy()
    metadata["true_label"] = metadata["disease"].map(label_map)
    metadata = metadata.loc[
        :, [
            "subject_id",
            "study_condition",
            "disease",
            "age",
            "gender",
            "BMI",
            "true_label",
        ]
    ]

    abundance = abundance_all.reindex(metadata.index)
    if abundance.isna().any().any() or (abundance < 0).any().any():
        raise ValueError("The selected abundance matrix contains invalid values.")
    if len(metadata) != 417 or metadata["true_label"].value_counts().to_dict() != {
        "HC": 235,
        "CL": 182,
    }:
        raise ValueError("Unexpected normal-BMI sample counts.")

    raw_relative_abundance = abundance.div(abundance.sum(axis=1), axis=0)
    raw_relative_abundance.to_csv(
        output_dir / "1. Raw relative abundance.csv", float_format="%.17g"
    )

    convert_names, read_aliases, read_reference = load_converter(skill_dir)
    reference = read_reference(skill_dir / "assets/spectra_canonical_1554.txt")
    aliases = read_aliases(skill_dir / "references/spectra_species_aliases.tsv")
    pd.DataFrame({"Taxon": abundance.columns}).to_csv(
        output_dir / "2. Microbial features.csv", index=False
    )
    mapping = convert_names(list(abundance.columns), reference, aliases)
    mapping_output = mapping.loc[
        :, ["Original taxon label", "Mapped feature name"]
    ]
    mapping_output.to_csv(output_dir / "3. Taxon name mapping.csv")

    converted = abundance.copy()
    converted.columns = mapping["Mapped feature name"]
    converted = converted.T.groupby(level=0, sort=False).sum().T
    # SPECTRA accepts relative abundance and performs preprocessing internally.
    prepared = converted.div(converted.sum(axis=1), axis=0)

    prepared.to_csv(output_dir / "4. Name-converted relative abundance.csv", float_format="%.17g")
    metadata.to_csv(output_dir / "0. metadata.csv", float_format="%.17g")

    print(f"Samples: {len(metadata)}")
    print(metadata["true_label"].value_counts().to_string())
    print(f"Source species: {abundance.shape[1]}")
    print(f"Prepared features: {prepared.shape[1]}")


if __name__ == "__main__":
    main()
