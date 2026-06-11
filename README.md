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

All input CSV files use sample IDs in the first column.

### Metagenomic abundance matrix

Use this input for the main SPECTRA workflow:

```text
data/example_metagenomic_abundance.csv
```

Rows are samples and columns are microbial taxa/features. Values should follow the clr transformed abundance format as the example file.

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

The 16S extension uses:

```text
data/example_16s_abundance.csv
```

The high-BMI extension uses:

```text
data/example_bmi_mri.csv
```

The example metadata file contains sample IDs and phenotype labels:

```text
data/example_metadata.csv
```

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
