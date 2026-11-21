import numpy as np
import pandas as pd
import pytest

from seminal import (
    add_semen_percentile_cols,
    below_reference,
    lower_reference_limit,
    semen_percentile,
    semen_reference,
)
from seminal.semen import CENTILES, PARAMETERS, _2010_2020, _WHO2020

# Campbell et al. 2021, Table 3, as printed (n, centiles, 95% CI of the 5th)
PAPER_TABLE_3 = {
    "volume": (3586, (1.0, 1.4, 1.8, 2.3, 3.0, 4.2, 5.5, 6.2, 6.9), (1.3, 1.5)),
    "concentration": (3587, (11, 16, 22, 36, 66, 110, 166, 208, 254), (15, 18)),
    "total_number": (3584, (29, 39, 58, 108, 210, 363, 561, 701, 865), (35, 40)),
    "total_motility": (3488, (35, 42, 47, 55, 64, 73, 83, 90, 92), (40, 43)),
    "progressive_motility": (3389, (24, 30, 36, 45, 55, 63, 71, 77, 81), (29, 31)),
    "nonprogressive_motility": (3387, (1, 1, 2, 4, 8, 15, 26, 32, 38), (1, 1)),
    "immotile": (2800, (15, 20, 23, 30, 37, 45, 53, 58, 65), (19, 20)),
    "vitality": (1337, (45, 54, 60, 69, 78, 88, 95, 97, 98), (50, 56)),
    "normal_forms": (3335, (3, 4, 5, 8, 14, 23, 32, 39, 45), (3.9, 4.0)),
}


def test_table_3_matches_paper():
    assert _WHO2020 == PAPER_TABLE_3
    assert set(PARAMETERS) == set(PAPER_TABLE_3)


def test_centiles_are_nondecreasing_in_both_tables():
    for tab in (_WHO2020, _2010_2020):
        for n, vals, ci in tab.values():
            assert list(vals) == sorted(vals)
            assert ci[0] <= vals[1] <= ci[1] or ci == (1, 1)


def test_sixth_edition_lower_reference_limits():
    # The WHO 6th edition headline limits
    assert lower_reference_limit("volume") == 1.4
    assert lower_reference_limit("concentration") == 16
    assert lower_reference_limit("total_number") == 39
    assert lower_reference_limit("total_motility") == 42
    assert lower_reference_limit("progressive_motility") == 30
    assert lower_reference_limit("vitality") == 54
    assert lower_reference_limit("normal_forms") == 4


def test_fifth_edition_limits():
    assert lower_reference_limit("concentration", "who2010") == 15
    assert lower_reference_limit("progressive_motility", "who2010") == 32
    with pytest.raises(ValueError):
        lower_reference_limit("immotile", "who2010")


@pytest.mark.parametrize("parameter", list(PARAMETERS))
def test_percentile_exact_at_published_points(parameter):
    _, vals, _ = PAPER_TABLE_3[parameter]
    for c, v in zip(CENTILES, vals):
        got = semen_percentile(parameter, v)
        # ties (NP 1, 1) resolve to the upper centile
        assert got == c or (vals.count(v) > 1 and got == max(cc for cc, vv in zip(CENTILES, vals) if vv == v))


def test_percentile_interpolates_and_clips():
    assert semen_percentile("concentration", 51) == pytest.approx(37.5)   # midway 36 -> 66
    assert semen_percentile("concentration", 0) == 2.5
    assert semen_percentile("concentration", 1000) == 97.5
    out = semen_percentile("volume", np.array([1.0, 6.9, np.nan]))
    assert out[0] == 2.5 and out[1] == 97.5 and np.isnan(out[2])


def test_below_reference():
    assert below_reference("concentration", 15.9) is True
    assert below_reference("concentration", 16) is False
    assert below_reference("concentration", 14.9, "who2010") is True
    assert below_reference("concentration", 15, "who2010") is False


def test_cohort_columns():
    df = pd.DataFrame({"conc": [10, 66, None, "x"], "pr": [20, 55, 80, 30]})
    out = add_semen_percentile_cols(df, {"concentration": "conc", "progressive_motility": "pr"})
    assert list(out.columns) == ["conc", "pr", "conc_pct", "conc_below_lrl", "pr_pct", "pr_below_lrl"]
    assert out["conc_pct"].tolist()[:2] == [2.5, 50.0]
    assert out["conc_pct"].isna().tolist() == [False, False, True, True]
    assert out["conc_below_lrl"].tolist()[:2] == [True, False]
    assert pd.isna(out["conc_below_lrl"].iloc[2])
    assert "conc_pct" not in df.columns


def test_reference_table_shape():
    t = semen_reference()
    assert t.shape == (9, 13)
    assert t.loc["concentration", "p50"] == 66
    assert semen_reference("volume", "2010_2020").loc["volume", "p5"] == 1.2
    with pytest.raises(ValueError):
        semen_reference("ph")
