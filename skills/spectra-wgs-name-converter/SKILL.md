---
name: spectra-wgs-name-converter
description: Convert WGS species labels to SPECTRA MetaPhlAn3 feature names using the bundled reference and aliases. Use for species-name conversion only, not abundance processing, feature completion, CLR, or prediction.
---

# SPECTRA WGS species-name converter

## Input

Accept a taxon list or table containing one source label per row. Preserve every
row and its original order. Use `assets/spectra_canonical_1554.txt` as the
authoritative target reference.

For a text file with one label per line, run:

```bash
python scripts/convert_species_names.py taxa.txt mapping.csv
```

## Output

Save a CSV with an index and exactly two data columns. Its header must be:

```text
,Original taxon label,Corresponding Msig
```

Keep unmatched source labels unchanged. Do not add confidence, method,
collision, taxonomy-rank, or summary columns.

## Matching

Mapping order:

1. Exact full-lineage match.
2. Unique terminal `s__` species match.
3. Explicit alias match.
4. Keep an unmatched label unchanged.

Do not use fuzzy matching. Return one mapping row for every input label and use
only aliases explicitly recorded in `references/spectra_species_aliases.tsv`.

This Skill converts names only. Do not transform abundance values, combine
columns, complete model features, perform CLR, or run prediction.
