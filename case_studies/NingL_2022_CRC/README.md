# NingL 2022 CRC WGS case study

This example applies the metagenomic SPECTRA workflow to the independent
PRJNA731589 colorectal cancer cohort. It starts from a published MetaPhlAn3
species relative-abundance matrix and does not process raw sequencing reads.

## Cohort

The source cohort contains 163 samples. This example uses the prespecified
normal-BMI range `18.5 <= BMI < 25`, leaving 116 samples:

- 52 colorectal cancer samples (`CL`)
- 64 healthy controls (`HC`)

`0. metadata.csv` retains the project ID, source group, age, sex, BMI, and final
SPECTRA label.

## Inputs

- `SuppTables_241010.xlsx`: published metadata and the 1,685-species
  MetaPhlAn3 relative-abundance matrix.
- `source_sample_metadata_163.csv`: accession-aligned clinical metadata used
  for BMI selection.
- `41564_2021_1030_MOESM3_ESM.xlsx`: supplementary information from the
  biological cohort publication.

The biological cohort is described by Liu et al., *Nature Microbiology*
(2022), DOI: https://doi.org/10.1038/s41564-021-01030-7. The published
MetaPhlAn3 matrix is provided with Wang et al. (2024), DOI:
https://doi.org/10.3390/microorganisms12102086.

## Run the example

Prepare the normal-BMI cohort and standardize WGS species names:

```bash
python prepare_input_data.py \
  --workbook SuppTables_241010.xlsx \
  --bmi-metadata source_sample_metadata_163.csv \
  --skill-dir ../../skills/spectra-wgs-name-converter \
  --project-id PRJNA731589 \
  --output-dir .
```

Run `SPECTRA_process.ipynb` from this directory. The notebook supplies
`4. Name-converted relative abundance.csv` to the models, which include preprocessing, and
calls `predict_from_abundance_to_phenotype` to write MRI scores and final
probabilities. Input feature names use the
MetaPhlAn3 convention; the mapped input retains unmatched source species.

## Results

Metrics are displayed in the notebook and are not exported as separate metric
files.

| Metric | Result |
|---|---:|
| SPECTRA CRC AUC | 0.7115 |
| CRC Top1 | 42.31% |
| CRC Top2 | 71.15% |
| CRC Top3 | 80.77% |

## Main files

- `prepare_input_data.py`: extracts the project, selects normal BMI, converts
  species names, and writes metadata and relative abundance.
- `0. metadata.csv`: sample metadata and SPECTRA labels.
- `1. Raw relative abundance.csv`: relative abundance with original taxon labels.
- `2. Microbial features.csv`: source species-name list.
- `3. Taxon name mapping.csv`: source-to-feature name mapping.
- `4. Name-converted relative abundance.csv`: relative abundance with converted taxon names, used as model input.
- `SPECTRA_process.ipynb`: relative-abundance input, prediction, and evaluation.
- `5. MRI scores.csv` and `6. Probability.csv`: prediction outputs used in
  the notebook.
