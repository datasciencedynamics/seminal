"""Probability of azoospermia from serum FSH and clinical inputs.

Implements the two models of Tradewell et al., World J Mens Health
2022;40(4):600-607 (doi:10.5534/wjmh.210138), developed on 946 men from
the University of Miami infertility clinic and externally validated on
Milan (n=1,955) and Chicago (n=596):

* ``azoospermia_fsh``: a quadratic in serum FSH alone (Fig. 1 of the paper).
* ``azoospermia_lr``:  a logistic regression on age, FSH, LH, total
  testosterone and mean testis volume (Table 3 of the paper).

Both coefficients sets are used exactly as printed. The paper rounds the
logistic coefficients to one or two significant figures; see the README
for what that implies.
"""

import math

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Published coefficients
# ---------------------------------------------------------------------------

# Table 3. Logistic regression model coefficients (log-odds scale).
# Fit on Miami data (n=946). Units: age in years, FSH and LH in IU/L,
# total testosterone in ng/dL, mean testis volume in cm^3 (Prader orchidometer).
LR_COEFS = {
    "intercept": -1.9,
    "age": 0.02,
    "fsh": 0.13,
    "lh": 0.03,
    "testosterone": -0.002,
    "testis_volume": -0.08,
}

# Fig. 1. Quadratic fit to binned Miami probabilities, output in percent:
#     p(%) = 0.133 * FSH^2 - 0.965 * FSH + 10.1       (R^2 = 0.95)
FSH_QUAD = {"a": 0.133, "b": -0.965, "c": 10.1}

# Reference limits quoted in the paper (Methods), used only for input warnings.
REFERENCE_RANGES = {
    "fsh": (1.5, 7.6),            # IU/L
    "lh": (1.8, 8.6),             # IU/L
    "testosterone": (264, 916),   # ng/dL
    "testis_volume": (12.5, 19),  # cm^3, mean of both testes
}


# ---------------------------------------------------------------------------
# FSH-only quadratic model
# ---------------------------------------------------------------------------

def azoospermia_fsh(fsh, clip=True):
    """Probability of azoospermia from serum FSH alone (quadratic model).

    Parameters
    ----------
    fsh : float or array-like
        Serum follicle-stimulating hormone in IU/L.
    clip : bool, default True
        Clip the result to [0, 1]. The published quadratic exceeds 100%
        above roughly 30 IU/L and is unbounded; the paper's own validation
        tables carry unclipped values above 1. Set ``clip=False`` to
        reproduce that behaviour exactly.

    Returns
    -------
    float or numpy.ndarray
        Probability between 0 and 1 (a fraction, not a percent).

    Notes
    -----
    The curve is U-shaped: 10.1% at undetectable FSH, a minimum of about
    8.4% at FSH 3.6 IU/L, and 100% at about 29.9 IU/L.

    Examples
    --------
    >>> round(azoospermia_fsh(0), 3)
    0.101
    >>> round(azoospermia_fsh(20), 3)
    0.439
    """
    x = np.asarray(fsh, dtype=float)
    pct = FSH_QUAD["a"] * x**2 + FSH_QUAD["b"] * x + FSH_QUAD["c"]
    p = pct / 100.0
    if clip:
        p = np.clip(p, 0.0, 1.0)
    return float(p) if p.ndim == 0 else p


# ---------------------------------------------------------------------------
# Logistic regression model
# ---------------------------------------------------------------------------

def _lr_terms(age, fsh, lh, testosterone, testis_volume):
    b = LR_COEFS
    return {
        "age": b["age"] * age,
        "fsh": b["fsh"] * fsh,
        "lh": b["lh"] * lh,
        "testosterone": b["testosterone"] * testosterone,
        "testis_volume": b["testis_volume"] * testis_volume,
    }


def azoospermia_lr(age, fsh, lh, testosterone, testis_volume, explain=False):
    """Probability of azoospermia from the logistic regression model.

    Parameters
    ----------
    age : float
        Age in years.
    fsh : float
        Serum FSH in IU/L.
    lh : float
        Serum luteinizing hormone in IU/L.
    testosterone : float
        Total testosterone in ng/dL. (Divide nmol/L by 0.03467 to convert.)
    testis_volume : float
        Mean of left and right testis volume in cm^3 (mL), as estimated by
        Prader orchidometer in the development cohort.
    explain : bool, default False
        Return a breakdown instead of just the probability.

    Returns
    -------
    float or dict
        Probability between 0 and 1. With ``explain=True``, a dict with
        ``risk``, ``intercept``, ``linear_predictor`` (log-odds) and
        ``contributions`` (each predictor's log-odds term, largest first).

    Notes
    -----
    The paper prints the model form as ``1/exp[-(b0 + bi*Xi)]``, which is a
    typesetting error (it would exceed 1). The standard logistic form
    ``1/(1 + exp(-(b0 + sum(bi*Xi))))`` is used here.

    Examples
    --------
    >>> round(azoospermia_lr(age=36, fsh=5.7, lh=4.5, testosterone=429,
    ...                      testis_volume=15), 3)
    0.086
    """
    terms = _lr_terms(age, fsh, lh, testosterone, testis_volume)
    lp = LR_COEFS["intercept"] + sum(terms.values())
    risk = 1.0 / (1.0 + math.exp(-lp))
    if not explain:
        return risk
    return {
        "risk": risk,
        "intercept": LR_COEFS["intercept"],
        "linear_predictor": lp,
        "contributions": dict(sorted(terms.items(), key=lambda kv: -abs(kv[1]))),
    }


# ---------------------------------------------------------------------------
# Cohort scoring
# ---------------------------------------------------------------------------

def add_azoospermia_risk_cols(
    df,
    age_col="age",
    fsh_col="fsh",
    lh_col="lh",
    testosterone_col="testosterone",
    testis_volume_col="testis_volume",
    lr_col="azoo_lr",
    fsh_model_col="azoo_fsh",
    copy=True,
):
    """Add both azoospermia probabilities to every row of a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per semen analysis / hormone panel.
    age_col, fsh_col, lh_col, testosterone_col, testis_volume_col : str
        Column names for the five logistic-model inputs. Only ``fsh_col``
        is needed for the FSH-only model.
    lr_col : str, default "azoo_lr"
        Name of the logistic regression probability column.
    fsh_model_col : str, default "azoo_fsh"
        Name of the FSH-only quadratic probability column.
    copy : bool, default True
        Work on a copy and leave ``df`` unchanged.

    Returns
    -------
    pandas.DataFrame
        ``df`` (or a copy) with the two probability columns added. A row
        with any logistic-model input missing gets ``NaN`` in ``lr_col``;
        the FSH-only column needs only FSH.
    """
    out = df.copy() if copy else df
    b = LR_COEFS

    fsh = pd.to_numeric(out[fsh_col], errors="coerce")
    out[fsh_model_col] = azoospermia_fsh(fsh.to_numpy())

    lp = (
        b["intercept"]
        + b["age"] * pd.to_numeric(out[age_col], errors="coerce")
        + b["fsh"] * fsh
        + b["lh"] * pd.to_numeric(out[lh_col], errors="coerce")
        + b["testosterone"] * pd.to_numeric(out[testosterone_col], errors="coerce")
        + b["testis_volume"] * pd.to_numeric(out[testis_volume_col], errors="coerce")
    )
    out[lr_col] = 1.0 / (1.0 + np.exp(-lp))
    return out


__all__ = [
    "LR_COEFS",
    "FSH_QUAD",
    "REFERENCE_RANGES",
    "azoospermia_fsh",
    "azoospermia_lr",
    "add_azoospermia_risk_cols",
]
