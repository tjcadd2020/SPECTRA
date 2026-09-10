# SPECTRA

SPECTRA predicts sample-level microbiome-associated phenotype patterns from metagenomic abundance data. You can run the local example files in this repository, or use the online xMICARE web server:

https://www.biosino.org/iMAC/xmicare/

For the web interface workflow, see [xMICARE_Tutorial.md](xMICARE_Tutorial.md).

## Citation

Yin W., Liu L., Zhu R. et al. **Gut Microbiome-derived Disease-associated Indices for Non-Invasive Detection of Chronic Diseases.** Journal, Year.

## What Is Included

- Main SPECTRA workflow for metagenomic abundance data
- Main metagenomic MRI calculators and SPECTRA model
- Example metagenomic abundance, MRI, BMI-MRI, 16S abundance, and metadata files
- Extension application: 16S abundance workflow
- Extension application: high-BMI SPECTRA workflow
- 16S and WGS taxon name-conversion Skills
- A reproducible normal-BMI WGS case study
- Command-line scripts and shared utility functions

## Directory

```text
.
├── README.md
├── xMICARE_Tutorial.md
├── environment.yml
├── requirements.txt
├── data/
│   ├── example_metagenomic_abundance.csv
│   ├── example_mri.csv
│   ├── example_bmi_mri.csv
│   ├── example_16s_abundance.csv
│   └── example_metadata.csv
├── models/
│   ├── metagenomic/
│   │   ├── spectra_model.pkl
│   │   └── mri_calculators/
│   └── extensions/
│       ├── 16S/
│       └── high_bmi/
├── skills/
│   ├── spectra-16s-name-converter/
│   └── spectra-wgs-name-converter/
├── case_studies/
│   └── NingL_2022_CRC/
├── scripts/
│   ├── utils.py
│   ├── predict_spectra_from_abundance.py
│   ├── predict_mri_from_abundance.py
│   ├── predict_spectra.py
│   ├── predict_16s.py
│   └── predict_bmi.py
├── tutorial_images/
└── results/
```

## Environment

Recommended Python version: `3.10`.

```bash
conda env create -f environment.yml
conda activate spectra-env
```

Or install the Python packages directly:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Main package versions:

- `numpy==1.26.4`
- `pandas==2.2.1`
- `scikit-learn==1.4.1.post1`
- `scipy==1.11.4`
- `imbalanced-learn==0.12.2`
- `scikit-bio==0.6.2`
- `shap==0.47.0`

## Input Data

Provide relative abundance as a CSV matrix with samples in rows, microbial
features in columns, and sample IDs in the first column. Values may be
proportions (row totals approximately 1) or percentages (approximately 100).
The models include the required preprocessing.
MSig name-format or incomplete-coverage checks issue advisory warnings and allow
prediction to continue.

MGS/WGS feature names must follow the **MetaPhlAn3** version. For **16S**, names
must match the **MPA annotation** labels used by the supplied 16S reference.
If source names differ, use the name-conversion Skills in [`skills/`](skills/)
and review the mapping before prediction.

For guidance starting from sequencing reads, see the
[WGS and 16S processing workflows](#preparing-relative-abundance-from-raw-reads).

### Metagenomic relative abundance matrix

Use `data/example_metagenomic_abundance.csv` for the main SPECTRA workflow.

### MRI matrix

If MRI values have already been calculated, SPECTRA can also start from an MRI table:

```text
data/example_mri.csv
```

This example MRI file is generated from `data/example_metagenomic_abundance.csv` with `scripts/predict_mri_from_abundance.py`, so the one-step and two-step example workflows produce the same SPECTRA probabilities.

Expected MRI columns:

```text
ACVD, AS, BPA, CL, IBD, IGT, T2D, CI, HC, FL, ME, SC
```

### Extension inputs

The 16S extension takes relative abundance and uses:

```text
data/example_16s_abundance.csv
```

The high-BMI extension uses:

```text
data/example_bmi_mri.csv
```

The example metadata file contains only sample IDs and phenotype labels:

```text
data/example_metadata.csv
```

## Preparing relative abundance from raw reads

Complete sequencing-read processing before uploading a relative-abundance table.
The models apply their own preprocessing internally.

### WGS: curatedMetagenomicData v3 taxonomic profiling

Please process WGS metagenomic sequencing data as follows. For initial read quality
control, we recommend assessing read quality using FastQC and removing sequencing
adapters, low-quality bases, and host-derived reads using
[KneadData](https://github.com/biobakery/kneaddata), which combines Trimmomatic and
Bowtie2. Then follow the taxonomic-profiling workflow used by curatedMetagenomicData
v3: run MetaPhlAn v3.0 with the `mpa_v30_CHOCOPhlAn_201901` database and default
profiling parameters. For paired-end data, supply both read files to MetaPhlAn.
Extract species-level relative abundances for each sample/run, retain the full
MetaPhlAn3 taxonomic lineage names and all profiled species, combine the profiles
into a sample-by-species matrix, and normalize each sample to sum to 1. See the
[curatedMetagenomicData pipeline documentation](https://waldronlab.io/curatedMetagenomicData/articles/our-pipeline.html)
and [MetaPhlAn3 documentation](https://github.com/biobakery/MetaPhlAn/wiki/MetaPhlAn-3.0)
for details.

The initial quality-control steps above are recommendations for new raw reads.
curatedMetagenomicData v3 relied on study-specific preprocessing, as explained in
the [maintainer's processing and database notes](https://support.bioconductor.org/p/9154295/).

### 16S: GMrepo processing

Please process the 16S sequencing data according to the
[GMrepo pipeline](https://doi.org/10.1093/nar/gkz764) (Nucleic Acids Research, 2020),
as follows: assess read quality using FastQC v0.11.8, remove sequencing vector
sequences and low-quality bases using Trimmomatic (alternatively, use Cutadapt for
primer removal, e.g., for Illumina data), and discard reads shorter than two-thirds
of their original length. Merge paired-end reads using Casper and process
single-end reads directly. Convert FASTQ to FASTA using Seqtk if needed. Assign
taxonomy using MAPseq v1.2, retaining reads with a genus-level combined score >0.4.
Calculate species-level relative abundances for each sample/run and normalize the
abundances to sum to 1.

### If you used another processing workflow

Check species-name compatibility before prediction, especially if you used a
different profiling tool or taxonomy database. WGS names should follow MetaPhlAn3;
16S names should match the MPA annotation labels used by the supplied 16S reference.
If names differ, you can use `spectra-wgs-name-converter` for WGS or
`spectra-16s-name-converter` for 16S, then review the mapped and unmatched names.
Keep all source species in the relative-abundance table. Name conversion
standardizes labels; abundance estimates can still differ between processing
workflows.

## Main Workflow: Metagenomic Abundance -> SPECTRA Prediction

This one-step command starts from a metagenomic abundance matrix and directly writes SPECTRA prediction outputs.

```bash
python scripts/predict_spectra_from_abundance.py \
  --input data/example_metagenomic_abundance.csv \
  --mri-model models/metagenomic/mri_calculators \
  --spectra-model models/metagenomic/spectra_model.pkl \
  --output results/spectra_metagenomic_predictions.csv
```

Outputs:

- `results/spectra_metagenomic_predictions.csv`: predicted label plus class probabilities
- `results/spectra_metagenomic_predictions_probability.csv`: class probabilities only


## Optional: Metagenomic Abundance -> MRI

Use this command only if you want to inspect or reuse the intermediate MRI values.

```bash
python scripts/predict_mri_from_abundance.py \
  --input data/example_metagenomic_abundance.csv \
  --mri-model models/metagenomic/mri_calculators \
  --output results/metagenomic_mri.csv
```

## Optional: MRI -> SPECTRA Prediction

Use this command only when MRI values have already been calculated.

```bash
python scripts/predict_spectra.py \
  --model models/metagenomic/spectra_model.pkl \
  --input data/example_mri.csv \
  --output results/spectra_predictions.csv
```

## Extension: 16S Abundance -> SPECTRA

```bash
python scripts/predict_16s.py \
  --input data/example_16s_abundance.csv \
  --mri-model models/extensions/16S/mri_models_all.pkl \
  --spectra-model models/extensions/16S/spectra_16s_model.pkl \
  --output results/16s_predictions.csv
```

## Extension: High-BMI Prediction

```bash
python scripts/predict_bmi.py \
  --model models/extensions/high_bmi/spectra_high_bmi.pkl \
  --input data/example_bmi_mri.csv \
  --output results/bmi_predictions.csv
```

## Use Your Own Data

```bash
python scripts/predict_spectra_from_abundance.py \
  --input path/to/your_metagenomic_abundance.csv \
  --output results/your_spectra_predictions.csv

python scripts/predict_mri_from_abundance.py \
  --input path/to/your_metagenomic_abundance.csv \
  --output results/your_mri.csv

python scripts/predict_spectra.py \
  --input path/to/your_mri.csv \
  --output results/your_mri_based_predictions.csv

python scripts/predict_16s.py \
  --input path/to/your_16s_abundance.csv \
  --output results/your_16s_predictions.csv

python scripts/predict_bmi.py \
  --input path/to/your_bmi_mri.csv \
  --output results/your_bmi_predictions.csv
```

## Worked WGS Case Study

[`case_studies/NingL_2022_CRC/`](case_studies/NingL_2022_CRC/) provides a
complete example starting from a published MetaPhlAn3 matrix. It includes
normal-BMI cohort selection, name conversion, relative-abundance input,
built-in preprocessing, MRI calculation, SPECTRA probabilities, and evaluation.

## Quick Check

After installing the environment, run:

```bash
python scripts/predict_spectra_from_abundance.py
python scripts/predict_mri_from_abundance.py
python scripts/predict_spectra.py
python scripts/predict_16s.py
python scripts/predict_bmi.py
```

The output CSV files will be written to `results/`.
