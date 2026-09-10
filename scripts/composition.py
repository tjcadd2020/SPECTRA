"""Small compositional-data transforms used by xMICARE.

The project only needs multiplicative zero replacement followed by a centred
log-ratio (CLR) transform.  Keeping these two operations local avoids importing
the much larger scikit-bio package (and its unrelated sequence modules) when
the Streamlit application starts.

The formulas and default ``delta`` match scikit-bio 0.6.2.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import re


def closure(values) -> np.ndarray:
    """Normalize each composition (row) so that it sums to one."""
    matrix = np.atleast_2d(np.asarray(values, dtype=float))
    if matrix.ndim > 2:
        raise ValueError("Input matrix can only have two dimensions or less")
    if not np.isfinite(matrix).all():
        raise ValueError("Compositions must contain only finite values")
    if np.any(matrix < 0):
        raise ValueError("Cannot have negative proportions")
    if np.any(np.all(matrix == 0, axis=1)):
        raise ValueError("Input matrix cannot have rows with all zeros")
    return (matrix / matrix.sum(axis=1, keepdims=True)).squeeze()


def multi_replace(values, delta: float | None = None) -> np.ndarray:
    """Replace zeros multiplicatively while keeping every row sum equal to one."""
    matrix = np.atleast_2d(closure(values))
    zero_mask = matrix == 0
    feature_count = matrix.shape[-1]
    zero_count = zero_mask.sum(axis=-1, keepdims=True)

    if delta is None:
        delta = (1.0 / feature_count) ** 2
    if not np.isfinite(delta) or delta <= 0:
        raise ValueError("delta must be a finite positive number")

    nonzero_scale = 1 - zero_count * delta
    if np.any(nonzero_scale < 0):
        raise ValueError(
            "The multiplicative replacement created negative proportions. "
            "Consider using a smaller delta."
        )

    return np.where(zero_mask, delta, nonzero_scale * matrix).squeeze()


def clr(values) -> np.ndarray:
    """Apply the centred log-ratio transform to one or more compositions."""
    matrix = np.atleast_2d(closure(values))
    if np.any(matrix <= 0):
        raise ValueError("CLR requires strictly positive values")
    log_matrix = np.log(matrix)
    return (log_matrix - log_matrix.mean(axis=-1, keepdims=True)).squeeze()


def clr_with_zero_replacement(values) -> np.ndarray:
    """Run xMICARE's complete abundance preprocessing transformation."""
    return clr(multi_replace(values))


def validate_relative_abundance(abundance: pd.DataFrame) -> pd.DataFrame:
    """Validate sample-by-feature proportions or percentages and merge collisions."""
    if abundance.empty:
        raise ValueError("Relative abundance must contain samples and features.")
    matrix = abundance.apply(pd.to_numeric, errors="raise").astype(float)
    matrix.index = matrix.index.astype(str)
    if not matrix.index.is_unique:
        raise ValueError("Sample IDs must be unique.")
    if not np.isfinite(matrix.to_numpy()).all() or (matrix < 0).any().any():
        raise ValueError("Relative abundance must contain finite, non-negative values.")
    if matrix.columns.has_duplicates:
        matrix = matrix.T.groupby(level=0, sort=False).sum().T
    totals = matrix.sum(axis=1)
    valid = totals.between(0.7, 1.05) | totals.between(70, 105)
    if not valid.all():
        raise ValueError(
            "Input must be relative abundance (row totals approximately 1 or 100); "
            "invalid samples: " + ", ".join(matrix.index[~valid])
        )
    return matrix


def check_metaphlan_format(name: str) -> bool:
    return bool(re.fullmatch(
        r"k__[^|;]+(?:\|p__[^|;]+)?(?:\|c__[^|;]+)?(?:\|o__[^|;]+)?"
        r"(?:\|f__[^|;]+)?(?:\|g__[^|;]+)?(?:\|s__[^|;]+)?", str(name)
    ))


def _terminal_taxon_name(name):
    """Recognize a literal MSig taxon for diagnostics, without changing input."""
    leaf = re.split(r"[|;]", str(name).strip())[-1].strip()
    leaf = re.sub(r"^[sg]__", "", leaf)
    return re.sub(r"\s+", "_", leaf)


def msig_input_diagnostics(input_features, msig_features, check_names=True):
    """Describe MSig name format and input-column coverage without blocking.

    Pass the original uploaded columns, before reference completion, and the
    MSig features used by the selected models. Coverage measures feature-name
    availability, not nonzero abundance. Short or partial names with the same
    literal terminal taxon as a selected MSig are checked for format only; they
    are not renamed or counted as exact matches. Other taxa are not checked.
    Coverage advice mentions formatting only when a malformed input name
    corresponds to a missing MSig taxon.
    """
    required = list(dict.fromkeys(msig_features))
    input_names = list(dict.fromkeys(input_features))
    supplied = set(input_names)
    missing = [name for name in required if name not in supplied]
    invalid = []
    format_may_reduce_coverage = False
    if check_names:
        msig_taxa = {_terminal_taxon_name(name) for name in required}
        related_inputs = [
            name for name in input_names
            if _terminal_taxon_name(name) in msig_taxa
        ]
        invalid = [
            name for name in dict.fromkeys(related_inputs + required)
            if not check_metaphlan_format(name)
        ]
        missing_taxa = {_terminal_taxon_name(name) for name in missing}
        format_may_reduce_coverage = any(
            name in supplied and _terminal_taxon_name(name) in missing_taxa
            for name in invalid
        )
    total = len(required)
    matched = total - len(missing)
    messages = []
    if invalid:
        examples = ", ".join(map(str, invalid[:3]))
        if len(invalid) > 3:
            examples += f", ... ({len(invalid)} names in total)"
        messages.append(
            "MSig-related names should use the full MetaPhlAn-style format: "
            f"{examples}."
        )
    if missing:
        coverage_message = (
            f"Input feature names cover {matched}/{total} MSig taxa "
            f"({matched / total:.1%}). More complete coverage may better support "
            "the model's predictions."
        )
        if format_may_reduce_coverage:
            coverage_message += (
                " Please also check the format of input taxa names, "
                "as name formatting may affect coverage."
            )
        messages.append(coverage_message)
    return {
        "matched": matched, "total": total, "missing": missing,
        "invalid_names": invalid, "messages": messages,
    }


def prepare_abundance(abundance, reference_features=None):
    """Prepare relative abundance for models, preserving the full CLR basis.

    MGS uses reference features followed by extra input features. For 16S, pass
    no reference: CLR uses only the supplied features. Model-specific selection
    and neutral-coordinate filling happen separately, after this transformation.
    """
    matrix = validate_relative_abundance(abundance)
    if reference_features is not None:
        reference = list(reference_features)
        if not reference or len(set(reference)) != len(reference):
            raise ValueError("Reference features must be non-empty and unique.")
        reference_set = set(reference)
        extras = [name for name in matrix if name not in reference_set]
        matrix = matrix.reindex(columns=reference + extras, fill_value=0.0)
    # The extra closure matches the published notebooks, followed by the
    # scikit-bio 0.6.2 multiplicative replacement and CLR formulas above.
    relative = matrix.div(matrix.sum(axis=1), axis=0)
    transformed = np.asarray(clr_with_zero_replacement(relative)).reshape(matrix.shape)
    result = pd.DataFrame(transformed, index=matrix.index, columns=matrix.columns)
    return result
