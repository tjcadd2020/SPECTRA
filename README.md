# SPECTRA model usage package

This repository provides a code-first package for running trained SPECTRA models on user data or on the included example files.

Web application: https://www.biosino.org/iMAC/xmicare/

For the web interface workflow, see [xMICARE_Tutorial.md](xMICARE_Tutorial.md). The screenshot assets used by that tutorial are included in `tutorial_images/`.

## Included Workflows

- MRI -> SPECTRA phenotype prediction
- 16S abundance -> MRI -> SPECTRA phenotype prediction
- MRI -> high-BMI SPECTRA prediction

The package is for model use and reproducible inference. It does not describe model development or training.

## Directory

```text
SPECTRA_GitHub_resource/
├── README.md
├── xMICARE_Tutorial.md
├── environment.yml
├── requirements.txt
├── data/
│   ├── example_mri.csv
│   ├── example_bmi_mri.csv
│   ├── example_16s_abundance.csv
│   └── example_metadata.csv
├── models/
│   ├── spectra_latest_tuned.pkl
│   ├── spectra_high_bmi.pkl
│   └── 16S/
│       ├── mri_models_all.pkl
│       └── spectra_16s_model.pkl
├── scripts/
│   ├── utils.py
│   ├── predict_spectra.py
│   ├── predict_bmi.py
│   └── predict_16s.py
├── tutorial_images/
└── results/
```
## Environment

Recommended Python version: `3.12`.

Create the environment with conda or micromamba:

```bash
conda env create -f environment.yml
conda activate spectra-env
```

Or install with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Pinned package versions:

- `numpy==1.26.4`
- `pandas==2.2.1`
- `scikit-learn==1.4.1.post1`
- `scipy==1.11.4`
- `imbalanced-learn==0.12.2`
- `scikit-bio==0.6.2`
- `shap==0.47.0`

## Data Format

All CSV files use sample IDs in the first column.

MRI feature files should use one row per sample and the following columns:

```text
ACVD, AS, BPA, CL, IBD, IGT, T2D, CI, HC, FL, ME, SC
```

Use the same MRI columns for `example_mri.csv` and `example_bmi_mri.csv`. Existing long-name MRI files are also handled internally by `scripts/utils.py`.

16S abundance files should be CLR-transformed abundance matrices with taxa/features in columns. See:

```text
data/example_16s_abundance.csv
```

The 16S pipeline aligns input taxa columns to the feature names saved in the MRI model bundle. Missing model features are filled with `0.0`, and extra columns are ignored.

The example metadata file is intentionally minimal:

```text
sample_id, phenotype
```

## Run MRI -> SPECTRA

```bash
python scripts/predict_spectra.py \
  --model models/spectra_latest_tuned.pkl \
  --input data/example_mri.csv \
  --output results/spectra_predictions.csv
```

Outputs:

- `results/spectra_predictions.csv`: predicted label plus class probabilities
- `results/spectra_predictions_probability.csv`: class probabilities only

## Run 16S -> MRI -> SPECTRA

```bash
python scripts/predict_16s.py \
  --input data/example_16s_abundance.csv \
  --mri-model models/16S/mri_models_all.pkl \
  --spectra-model models/16S/spectra_16s_model.pkl \
  --output results/16s_predictions.csv
```

Outputs:

- `results/16s_predictions_mri.csv`: intermediate MRI values
- `results/16s_predictions.csv`: predicted label plus class probabilities
- `results/16s_predictions_probability.csv`: class probabilities only

Main utility functions:

- `load_MRIcf_and_predict_all_phenotypes`: abundance matrix -> MRI matrix
- `load_and_predict_SPECTRA_for_phenotype`: MRI matrix -> SPECTRA probabilities
- `predict_from_abundance_to_phenotype`: one-step abundance -> MRI -> prediction

## Run High-BMI SPECTRA

```bash
python scripts/predict_bmi.py \
  --model models/spectra_high_bmi.pkl \
  --input data/example_bmi_mri.csv \
  --output results/bmi_predictions.csv
```

Outputs:

- `results/bmi_predictions.csv`: predicted label plus class probabilities
- `results/bmi_predictions_probability.csv`: class probabilities only

## Tested Workflow

The three commands below were tested with the pinned environment in `environment.yml`:

```bash
python scripts/predict_spectra.py
python scripts/predict_bmi.py
python scripts/predict_16s.py
```

Validation summary:

- `predict_spectra.py`: generated sample predictions and 12 SPECTRA probability columns.
- `predict_bmi.py`: generated sample predictions and 6 high-BMI probability columns.
- `predict_16s.py`: generated sample predictions, 6 intermediate MRI columns, and 6 SPECTRA probability columns.
- For all probability outputs, each sample-level probability row summed to `1.0`.

## Use Your Own Data

```bash
python scripts/predict_spectra.py \
  --input path/to/your_mri.csv \
  --output results/your_spectra_predictions.csv

python scripts/predict_bmi.py \
  --input path/to/your_bmi_mri.csv \
  --output results/your_bmi_predictions.csv

python scripts/predict_16s.py \
  --input path/to/your_16s_abundance_clr.csv \
  --output results/your_16s_predictions.csv
```

## GitHub Notes

The included model files are below GitHub's single-file size limit and can be committed directly with standard Git.
