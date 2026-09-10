# SPECTRA species-name conversion Skills

These two Skills standardize species names before a SPECTRA workflow. They
convert names only; they do not modify abundances, add model features, perform
CLR, or run prediction.

## Common usage

Provide a taxon list or a table containing one taxon label per row, then invoke
the appropriate Skill:

```text
Use $spectra-16s-name-converter to convert this 16S taxon list and save mapping.csv.
Use $spectra-wgs-name-converter to convert this WGS taxon list and save mapping.csv.
```

Both Skills preserve input order and write the same mapping-table structure:

```text
,Original taxon label,Corresponding Msig
```

Review the mapping before applying it to an abundance matrix. The calling
workflow is responsible for combining duplicate mapped columns and all later
abundance processing.

## 16S Skill

`spectra-16s-name-converter/` converts heterogeneous 16S species annotations to the
SPECTRA 16S MSig labels in the bundled `MSigs.csv` reference. It uses
conservative AI-assisted matching and assigns explicit identifiers to unmatched
taxa.

## WGS Skill

`spectra-wgs-name-converter/` converts WGS species labels to the MetaPhlAn3
feature names used by SPECTRA. It uses exact lineage, exact species, and bundled
explicit-alias matching. Unmatched source labels are retained.

For reproducible batch conversion of a text file containing one WGS species
label per line, the same Skill also provides:

```bash
python skills/spectra-wgs-name-converter/scripts/convert_species_names.py \
  taxa.txt mapping.csv
```
