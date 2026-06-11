#!/usr/bin/env python
import argparse
import pandas as pd

from utils import predict_from_abundance_to_phenotype, save_prediction_outputs


def predict(abundance_path, mri_model_path, spectra_model_path, output_path):
    abundance = pd.read_csv(abundance_path, index_col=0)
    res = predict_from_abundance_to_phenotype(
        Abundance=abundance,
        MRI_model_path=mri_model_path,
        SPECTRA_model_path=spectra_model_path,
    )
    save_prediction_outputs(output_path, res["prediction"], res["probability"], MRI=res["MRI"])


def main():
    parser = argparse.ArgumentParser(description="Run SPECTRA prediction from a microbial abundance matrix.")
    parser.add_argument("--input", default="data/example_16s_abundance.csv")
    parser.add_argument("--mri-model", default="models/16S/mri_models_all.pkl")
    parser.add_argument("--spectra-model", default="models/16S/spectra_16s_model.pkl")
    parser.add_argument("--output", default="results/spectra_from_abundance_predictions.csv")
    args = parser.parse_args()
    predict(args.input, args.mri_model, args.spectra_model, args.output)


if __name__ == "__main__":
    main()
