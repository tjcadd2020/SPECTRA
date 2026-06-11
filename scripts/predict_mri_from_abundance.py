#!/usr/bin/env python
import argparse
from pathlib import Path

import pandas as pd

from utils import load_MRIcf_and_predict_all_phenotypes, shorten_probability_labels


def predict(abundance_path, mri_model_path, output_path):
    abundance = pd.read_csv(abundance_path, index_col=0)
    mri = load_MRIcf_and_predict_all_phenotypes(
        MRIcf_path=mri_model_path,
        Abundance=abundance,
    )
    mri = shorten_probability_labels(mri)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mri.to_csv(output_path)
    print(f"Saved MRI values to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Calculate MRI values from a metagenomic abundance matrix.")
    parser.add_argument("--input", default="data/example_metagenomic_abundance.csv")
    parser.add_argument("--mri-model", default="models/metagenomic/mri_calculators")
    parser.add_argument("--output", default="results/metagenomic_mri.csv")
    args = parser.parse_args()
    predict(args.input, args.mri_model, args.output)


if __name__ == "__main__":
    main()
