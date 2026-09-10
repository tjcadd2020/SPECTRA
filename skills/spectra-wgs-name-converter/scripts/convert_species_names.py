#!/usr/bin/env python3
"""Convert species labels to SPECTRA MetaPhlAn3 feature names."""

from __future__ import annotations

import argparse
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = SKILL_ROOT / "assets/spectra_canonical_1554.txt"
DEFAULT_ALIASES = SKILL_ROOT / "references/spectra_species_aliases.tsv"


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value)).strip().replace("_", " ")
    return re.sub(r"\s+", " ", value)


def species_leaf(feature: str) -> str | None:
    feature = unicodedata.normalize("NFKC", str(feature)).strip()
    if "|" in feature:
        parts = [part for part in feature.split("|") if part.startswith("s__")]
        if not parts:
            return None
        feature = parts[-1]
    if feature.startswith("s__"):
        feature = feature[3:]
    return normalize_name(feature)


def read_reference(path: Path = DEFAULT_REFERENCE) -> list[str]:
    features = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not features or len(features) != len(set(features)):
        raise ValueError("Reference features must be non-empty and unique.")
    return features


def read_aliases(path: Path = DEFAULT_ALIASES) -> dict[str, str]:
    table = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    return {
        normalize_name(row.source_species): normalize_name(row.target_species)
        for row in table.itertuples(index=False)
    }


def convert_species_names(
    source_names: list[str],
    reference_features: list[str],
    aliases: dict[str, str] | None = None,
) -> pd.DataFrame:
    reference_set = set(reference_features)
    leaf_to_features: dict[str, list[str]] = defaultdict(list)
    for feature in reference_features:
        leaf = species_leaf(feature)
        if leaf is not None:
            leaf_to_features[leaf].append(feature)

    aliases = aliases or {}
    rows = []
    for source in source_names:
        leaf = species_leaf(source)
        converted = source
        if source in reference_set:
            converted = source
        elif leaf is not None and len(leaf_to_features.get(leaf, [])) == 1:
            converted = leaf_to_features[leaf][0]
        elif leaf is not None and leaf in aliases:
            targets = leaf_to_features.get(aliases[leaf], [])
            if len(targets) == 1:
                converted = targets[0]
        rows.append(
            {
                "Original taxon label": source,
                "Corresponding Msig": converted,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Text file with one species label per line")
    parser.add_argument("output", type=Path, help="Output mapping CSV")
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    args = parser.parse_args()

    source_names = [line.strip() for line in args.input.read_text().splitlines() if line.strip()]
    mapping = convert_species_names(
        source_names,
        read_reference(args.reference),
        read_aliases(args.aliases),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(args.output, index=True)


if __name__ == "__main__":
    main()
