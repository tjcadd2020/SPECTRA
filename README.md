# SPECTRA

SPECTRA predicts sample-level microbiome-associated phenotype patterns from microbial abundance data. You can run it locally with the example files in this repository, or use the online xMICARE web server:

https://www.biosino.org/iMAC/xmicare/

For the web interface workflow, see [xMICARE_Tutorial.md](xMICARE_Tutorial.md). Screenshots used by that tutorial are included in `tutorial_images/`.

## What Is Included

- Example microbial abundance, MRI, BMI-MRI, and metadata files
- SPECTRA models for local prediction
- A 16S workflow that starts from a microbial abundance matrix
- A high-BMI prediction workflow
- Command-line scripts and shared utility functions

## Directory

```text
.
├── README.md
├── xMICARE_Tutorial.md
├── environment.yml
├── requirements.txt
├── data/
│   ├── example_16s_abundance.csv
│   ├── example_mri.csv
│   ├── example_bmi_mri.csv
│   └── example_metadata.csv
├── models/
│   ├── spectra_latest_tuned.pkl
│   ├── spectra_high_bmi.pkl
│   └── 16S/
│       ├── mri_models_all.pkl
│       └── spectra_16s_model.pkl
├── scripts/
│   ├── utils.py
│   ├── predict_spectra_from_abundance.py
│   ├── predict_16s.py
│   ├── predict_spectra.py
│   └── predict_bmi.py
├── tutorial_images/
└── results/
```

## Environment

Recommended Python version: `3.12`.

Create the environment:

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

### Microbial abundance matrix

Use this input when starting from microbiome data:

```text
data/example_16s_abundance.csv
```

Rows are samples and columns are microbial taxa/features. The values should be CLR-transformed abundance values.

### MRI matrix

If MRI values have already been calculated, SPECTRA can also start from an MRI table:

```text
data/example_mri.csv
```

Expected MRI columns:

```text
ACVD, AS, BPA, CL, IBD, IGT, T2D, CI, HC, FL, ME, SC
```

The high-BMI workflow uses the same MRI column format:

```text
data/example_bmi_mri.csv
```

Long-form MRI column names from existing files are also accepted by `scripts/utils.py`.

### Metadata

The example metadata file contains only sample IDs and phenotype labels:

```text
data/example_metadata.csv
```

## Start From Microbial Abundance

This is the main local SPECTRA workflow. It calculates MRI values from the abundance matrix and then runs SPECTRA prediction.

```bash
python scripts/predict_spectra_from_abundance.py \
  --input data/example_16s_abundance.csv \
  --mri-model models/16S/mri_models_all.pkl \
  --spectra-model models/16S/spectra_16s_model.pkl \
  --output results/spectra_from_abundance_predictions.csv
```

Outputs:

- `results/spectra_from_abundance_predictions_mri.csv`: intermediate MRI values
- `results/spectra_from_abundance_predictions.csv`: predicted label plus class probabilities
- `results/spectra_from_abundance_predictions_probability.csv`: class probabilities only

`scripts/predict_16s.py` provides the same abundance-to-SPECTRA workflow with a shorter output filename.

## Start From Existing MRI Values

Use this only when MRI values have already been calculated.

```bash
python scripts/predict_spectra.py \
  --model models/spectra_latest_tuned.pkl \
  --input data/example_mri.csv \
  --output results/spectra_predictions.csv
```

Outputs:

- `results/spectra_predictions.csv`: predicted label plus class probabilities
- `results/spectra_predictions_probability.csv`: class probabilities only

## High-BMI Prediction

```bash
python scripts/predict_bmi.py \
  --model models/spectra_high_bmi.pkl \
  --input data/example_bmi_mri.csv \
  --output results/bmi_predictions.csv
```

Outputs:

- `results/bmi_predictions.csv`: predicted label plus class probabilities
- `results/bmi_predictions_probability.csv`: class probabilities only

## Use Your Own Data

```bash
python scripts/predict_spectra_from_abundance.py \
  --input path/to/your_16s_abundance_clr.csv \
  --output results/your_spectra_predictions.csv

python scripts/predict_spectra.py \
  --input path/to/your_mri.csv \
  --output results/your_mri_based_predictions.csv

python scripts/predict_bmi.py \
  --input path/to/your_bmi_mri.csv \
  --output results/your_bmi_predictions.csv
```

## Quick Check

After installing the environment, run:

```bash
python scripts/predict_spectra_from_abundance.py
python scripts/predict_spectra.py
python scripts/predict_bmi.py
```

The output CSV files will be written to `results/`.
