import pickle
from pathlib import Path

import numpy as np
import pandas as pd


PHENOTYPE_NAME_MAP = {
    "BloodPressureAbnormalities": "BPA",
    "ColorectalLesions": "CL",
    "cirrhosis": "CI",
    "fatty_liver": "FL",
    "control": "HC",
    "melanoma": "ME",
    "schizophrenia": "SC",
}

SHORT_TO_PHENOTYPE_NAME = {v: k for k, v in PHENOTYPE_NAME_MAP.items()}
SHORT_TO_PHENOTYPE_NAME.update(
    {
        "ACVD": "ACVD",
        "AS": "AS",
        "IBD": "IBD",
        "IGT": "IGT",
        "T2D": "T2D",
    }
)


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def clean_matrix(x):
    x = x.copy()
    x.index = x.index.astype(str)
    x = x.loc[:, ~x.columns.duplicated(keep="first")]
    x = x.replace([np.inf, -np.inf], np.nan)
    x = x.apply(pd.to_numeric, errors="coerce")
    return x.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def normalize_mri_columns(mri):
    mri = mri.copy()
    mri.columns = [_canonical_mri_name(c) for c in mri.columns]
    return mri


def _strip_mri_wrapper(name):
    name = str(name)
    if name.startswith("MRI(") and name.endswith(")"):
        return name[4:-1]
    return name


def _canonical_mri_name(name):
    name = _strip_mri_wrapper(name)
    return SHORT_TO_PHENOTYPE_NAME.get(name, name)


def _feature_aliases(feature):
    feature = str(feature)
    aliases = {feature}
    inner = _strip_mri_wrapper(feature)
    canonical = _canonical_mri_name(inner)
    short = PHENOTYPE_NAME_MAP.get(canonical, canonical)

    aliases.update({inner, canonical, short, f"MRI({inner})", f"MRI({canonical})", f"MRI({short})"})
    return aliases


def align_to_features(x, features):
    x = x.copy()
    aligned = pd.DataFrame(index=x.index)
    for feature in features:
        source = next((alias for alias in _feature_aliases(feature) if alias in x.columns), None)
        aligned[feature] = x[source] if source is not None else 0.0
    return aligned


def predict_MRI_for_phenotype(MRIcf, Abundance, phenotype):
    pred_MRI = MRIcf.predict_proba(Abundance)[:, 1]
    return pd.DataFrame(pred_MRI, index=Abundance.index, columns=[phenotype])


def load_MRIcf_and_predict_all_phenotypes(MRIcf_path, Abundance, phenotypes=None):
    Abundance = clean_matrix(Abundance)
    MRIcf_path = Path(MRIcf_path)

    if MRIcf_path.is_file():
        bundle = load_pickle(MRIcf_path)
    else:
        bundle = None

    if isinstance(bundle, dict) and {"models", "feature_map"}.issubset(bundle):
        MRI_models = bundle["models"]
        MRI_feature_map = bundle["feature_map"]
        if phenotypes is None:
            phenotypes = list(MRI_models.keys())

        MRI_res = pd.DataFrame(index=Abundance.index)
        for p in phenotypes:
            MRIcf = MRI_models[p]
            features = list(MRI_feature_map[p])
            X_sub = Abundance.reindex(columns=features, fill_value=0.0)
            X_sub = clean_matrix(X_sub)
            MRI_res = pd.concat(
                [MRI_res, predict_MRI_for_phenotype(MRIcf, X_sub, p)],
                axis=1,
            )
        return MRI_res

    if phenotypes is None:
        raise ValueError("phenotypes is required when MRIcf_path is a directory of per-phenotype models.")

    MRI_res = pd.DataFrame(index=Abundance.index)
    for p in phenotypes:
        MRIcf = load_pickle(MRIcf_path / f"MRIfor{p}.pkl")
        features = list(MRIcf.feature_names_in_)
        X_sub = Abundance.reindex(columns=features, fill_value=0.0)
        X_sub = clean_matrix(X_sub)
        MRI_res = pd.concat(
            [MRI_res, predict_MRI_for_phenotype(MRIcf, X_sub, p)],
            axis=1,
        )
    return MRI_res


def format_mri_for_16s_spectra(MRI):
    MRI = MRI.rename(columns=PHENOTYPE_NAME_MAP)
    MRI.columns = [c if str(c).startswith("MRI(") else f"MRI({c})" for c in MRI.columns]
    return MRI


def _predict_probability(model, X):
    probability = pd.DataFrame(
        model.predict_proba(X),
        index=X.index,
        columns=list(model.classes_),
    )
    probability = shorten_probability_labels(probability)
    prediction = probability.copy()
    prediction.insert(0, "pred_label", probability.idxmax(axis=1))
    return probability, prediction


def shorten_label(label):
    return PHENOTYPE_NAME_MAP.get(str(label), str(label))


def shorten_probability_labels(probability):
    probability = probability.copy()
    probability.columns = [shorten_label(c) for c in probability.columns]
    probability = probability.T.groupby(level=0, sort=False).sum().T
    return probability


def load_and_predict_SPECTRA_for_phenotype(model_path, MRIfile, phenotypes=None, explain=False):
    model_obj = load_pickle(model_path)
    MRIfile = normalize_mri_columns(MRIfile)
    MRIfile = clean_matrix(MRIfile)

    if isinstance(model_obj, dict) and {"model", "features", "classes"}.issubset(model_obj):
        model = model_obj["model"]
        features = list(model_obj["features"])
        classes = list(model_obj["classes"])
        X = align_to_features(MRIfile, features)
        X = clean_matrix(X)
        probability = pd.DataFrame(model.predict_proba(X), index=X.index, columns=list(model.classes_))
        for c in classes:
            if c not in probability.columns:
                probability[c] = 0.0
        probability = probability.loc[:, classes]
        prediction = probability.copy()
        prediction.insert(0, "pred_label", probability.idxmax(axis=1))
        return prediction, probability

    model = model_obj
    if hasattr(model, "feature_names_in_"):
        MRIfile = align_to_features(MRIfile, list(model.feature_names_in_))
    MRIfile = clean_matrix(MRIfile)
    probability, prediction = _predict_probability(model, MRIfile)
    return prediction, probability


def predict_from_abundance_to_phenotype(Abundance, MRI_model_path, SPECTRA_model_path):
    MRI = load_MRIcf_and_predict_all_phenotypes(
        MRIcf_path=MRI_model_path,
        Abundance=Abundance,
    )
    MRI_for_spectra = format_mri_for_16s_spectra(MRI)
    prediction, probability = load_and_predict_SPECTRA_for_phenotype(
        model_path=SPECTRA_model_path,
        MRIfile=MRI_for_spectra,
    )
    return {"MRI": MRI, "probability": probability, "prediction": prediction}


def save_prediction_outputs(output_path, prediction, probability, MRI=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if MRI is not None:
        MRI.to_csv(output_path.with_name(output_path.stem + "_mri.csv"))
    prediction.to_csv(output_path)
    probability.to_csv(output_path.with_name(output_path.stem + "_probability.csv"))
    print(f"Saved predictions to {output_path}")
