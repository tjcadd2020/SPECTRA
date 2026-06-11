#!/usr/bin/env python
import argparse
import pandas as pd

from utils import predict_spectra_from_abundance, save_prediction_outputs


def predict(abundance_path, mri_model_path, spectra_model_path, output_path):
    abundance = pd.read_csv(abundance_path, index_col=0)
    prediction, probability = predict_spectra_from_abundance(
        Abundance=abundance,
        MRI_model_path=mri_model_path,
        SPECTRA_model_path=spectra_model_path,
    )
    save_prediction_outputs(output_path, prediction, probability)


def main():
    parser = argparse.ArgumentParser(description="Run SPECTRA prediction from a metagenomic abundance matrix.")
    parser.add_argument("--input", default="data/example_metagenomic_abundance.csv")
    parser.add_argument("--mri-model", default="models/metagenomic/mri_calculators")
    parser.add_argument("--spectra-model", default="models/metagenomic/spectra_model.pkl")
    parser.add_argument("--output", default="results/spectra_metagenomic_predictions.csv")
    args = parser.parse_args()
    predict(args.input, args.mri_model, args.spectra_model, args.output)


if __name__ == "__main__":
    main()
