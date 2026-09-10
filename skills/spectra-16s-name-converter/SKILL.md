---
name: spectra-16s-name-converter
description: Convert 16S species labels to SPECTRA 16S MSig names using the bundled reference. Use for species-name conversion only, not abundance processing, feature completion, CLR, or prediction.
---

# SPECTRA 16S species-name converter

## Input

Accept a taxon list or table containing one source label per row. Preserve every
row and its original order. Use `assets/MSigs.csv` as the authoritative target
reference.

## Output

Save a CSV with an index and exactly two data columns. Its header must be:

```text
,Original taxon label,Corresponding Msig
```

Use the exact reference `Msig` for a unique match. Label unmatched rows as
`Unmatched_taxon_1`, `Unmatched_taxon_2`, and so on. Do not add confidence,
reason, taxonomy-rank, or summary columns.

## Matching

Match only when the normalized genus and complete species designation identify
one reference row. Normalize rank prefixes, whitespace, underscores, annotated
suffixes, and bracketed genera conservatively. Do not use fuzzy matching or
unstated biological synonyms.

Read `references/matching_spec.md` when the input contains rank-prefixed
lineages, positional taxonomy paths, separate genus and species columns, or
ambiguous annotations.

This Skill converts names only. Do not transform abundance values, combine
columns, complete model features, perform CLR, or run prediction.
