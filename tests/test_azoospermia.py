import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from seminal import (
    FSH_QUAD,
    LR_COEFS,
    add_azoospermia_risk_cols,
    azoospermia_fsh,
    azoospermia_lr,
)

# Tradewell et al. 2022, Table 3, exactly as printed
PAPER_TABLE_3 = {
    "intercept": -1.9,
    "age": 0.02,
    "fsh": 0.13,
    "lh": 0.03,
    "testosterone": -0.002,
    "testis_volume": -0.08,
}


def test_lr_coefficients_match_table_3():
    assert LR_COEFS == PAPER_TABLE_3


def test_fsh_quadratic_matches_fig_1():
    assert FSH_QUAD == {"a": 0.133, "b": -0.965, "c": 10.1}


# ---- FSH-only model: anchors quoted in the paper's Results and Discussion ----

def test_fsh_undetectable_is_10_percent():
    # "at undetectable FSH there is a 10.1% chance of being azoospermic"
    assert azoospermia_fsh(0) == pytest.approx(0.101)


def test_fsh_nadir_at_3_6():
    # "the probability of azoospermia is lowest in men with FSH values of 3.6 IU/L"
    nadir = -FSH_QUAD["b"] / (2 * FSH_QUAD["a"])
    assert nadir == pytest.approx(3.6, abs=0.05)
    grid = np.arange(0, 20, 0.01)
    assert grid[np.argmin(azoospermia_fsh(grid))] == pytest.approx(3.63, abs=0.01)


def test_fsh_reaches_certainty_near_30():
    # "after an FSH of 30 IU/L the majority of men will be azoospermic"
    assert azoospermia_fsh(29) < 1.0
    assert azoospermia_fsh(30) == 1.0
    assert azoospermia_fsh(30, clip=False) > 1.0


def test_fsh_vectorized_and_clipped():
    out = azoospermia_fsh([0, 3.6, 20, 80])
    assert isinstance(out, np.ndarray)
    assert out.min() >= 0 and out.max() <= 1
    assert out[-1] == 1.0


# ---- Logistic model ----

def test_lr_hand_computed_median_patient():
    # Median Miami-ish patient from Table 1
    lp = -1.9 + 0.02 * 36 + 0.13 * 5.7 + 0.03 * 4.5 - 0.002 * 429 - 0.08 * 15
    expected = 1 / (1 + math.exp(-lp))
    got = azoospermia_lr(age=36, fsh=5.7, lh=4.5, testosterone=429, testis_volume=15)
    assert got == pytest.approx(expected)
    assert round(got, 3) == 0.086


def test_lr_monotone_in_fsh():
    base = dict(age=36, lh=4.5, testosterone=429, testis_volume=15)
    assert azoospermia_lr(fsh=5, **base) < azoospermia_lr(fsh=15, **base) < azoospermia_lr(fsh=30, **base)


def test_lr_explain_breakdown_sums_to_linear_predictor():
    out = azoospermia_lr(age=40, fsh=12, lh=6, testosterone=300, testis_volume=10, explain=True)
    assert set(out) == {"risk", "intercept", "linear_predictor", "contributions"}
    assert out["intercept"] + sum(out["contributions"].values()) == pytest.approx(out["linear_predictor"])
    assert out["risk"] == pytest.approx(1 / (1 + math.exp(-out["linear_predictor"])))
    # largest absolute contribution first
    vals = [abs(v) for v in out["contributions"].values()]
    assert vals == sorted(vals, reverse=True)


# ---- Cohort scoring ----

def test_add_cols_matches_scalar_functions_and_handles_missing():
    df = pd.DataFrame({
        "age": [36, 50, 30],
        "fsh": [5.7, 25.0, 2.0],
        "lh": [4.5, 10.0, np.nan],
        "testosterone": [429, 250, 600],
        "testis_volume": [15, 8, 20],
    })
    out = add_azoospermia_risk_cols(df)
    assert "azoo_lr" in out and "azoo_fsh" in out
    assert out.loc[0, "azoo_lr"] == pytest.approx(
        azoospermia_lr(age=36, fsh=5.7, lh=4.5, testosterone=429, testis_volume=15))
    assert out.loc[1, "azoo_fsh"] == pytest.approx(azoospermia_fsh(25.0))
    assert np.isnan(out.loc[2, "azoo_lr"])        # LH missing -> NaN
    assert not np.isnan(out.loc[2, "azoo_fsh"])   # FSH-only model still scores
    assert "azoo_lr" not in df                    # copy=True leaves input alone


# ---- External validation against the CC0 Dataverse file (optional) ----

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed" / "tradewell_2022.parquet"


def _auc(y, p):
    """Rank-based AUC without sklearn."""
    y = np.asarray(y, bool)
    p = np.asarray(p, float)
    r = pd.Series(p).rank().to_numpy()
    n_pos, n_neg = y.sum(), (~y).sum()
    return (r[y].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


@pytest.mark.skipif(not PROCESSED.exists(), reason="run `make data_gen preprocess` first")
@pytest.mark.parametrize("site,paper_lr,paper_fsh", [
    ("milan", 0.79, 0.78),
    ("chicago", 0.72, 0.71),
])
def test_external_validation_auc_matches_paper(site, paper_lr, paper_fsh):
    df = pd.read_parquet(PROCESSED)
    df = df[(df["site"] == site) & df["included"]]
    df = add_azoospermia_risk_cols(df)
    ok = df["azoo_lr"].notna()
    assert _auc(df.loc[ok, "azoospermia"], df.loc[ok, "azoo_lr"]) == pytest.approx(paper_lr, abs=0.03)
    assert _auc(df["azoospermia"], df["azoo_fsh"]) == pytest.approx(paper_fsh, abs=0.03)
