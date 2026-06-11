#!/usr/bin/env python
import argparse
import pandas as pd

from utils import load_and_predict_SPECTRA_for_phenotype, save_prediction_outputs


def predict(model_path, input_path, output_path):
    MRIfile = pd.read_csv(input_path, index_col=0)
    prediction, probability = load_and_predict_SPECTRA_for_phenotype(
        model_path=model_path,
        MRIfile=MRIfile,
    )
    save_prediction_outputs(output_path, prediction, probability)


def main():
    parser = argparse.ArgumentParser(description="Run BMI-related SPECTRA prediction from MRI features.")
    parser.add_argument("--model", default="models/spectra_high_bmi.pkl")
    parser.add_argument("--input", default="data/example_bmi_mri.csv")
    parser.add_argument("--output", default="results/bmi_predictions.csv")
    args = parser.parse_args()
    predict(args.model, args.input, args.output)


if __name__ == "__main__":
    main()
