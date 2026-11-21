"""WHO 2021 (6th edition) semen reference distributions.

Implements the distribution of semen examination results in fertile men from
Campbell MJ, Lotti F, Baldi E, et al. Distribution of semen examination
results 2020 - A follow up of data collated for the WHO semen analysis manual
2010. Andrology 2021;9(4):817-822 (doi:10.1111/andr.12983), which the WHO
laboratory manual, 6th edition (2021) adopted as its reference distribution.

The men are partners of women who conceived within 12 months of trying
(time to pregnancy <= 12 months). The 5th centile of each parameter is the
conventional "lower reference limit"; the paper is explicit that it is not a
threshold between fertile and infertile.

Two tables are carried, exactly as printed:

* ``"who2020"`` (default): Table 3, Analysis 2, the 2010 reference data
  combined with studies published 2010-2020 (3,586 men, 12 countries).
* ``"2010_2020"``: Table 2, Analysis 1, the 2010-2020 studies alone.

The 5th-edition (WHO 2010, Cooper et al. 2010) lower reference limits are
included under ``"who2010"`` for labs that still report against them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Published tables
# ---------------------------------------------------------------------------

CENTILES = (2.5, 5, 10, 25, 50, 75, 90, 95, 97.5)

PARAMETERS = {
    "volume": "Semen volume (mL)",
    "concentration": "Sperm concentration (10^6/mL)",
    "total_number": "Total sperm number (10^6/ejaculate)",
    "total_motility": "Total motility, PR + NP (%)",
    "progressive_motility": "Progressive motility, PR (%)",
    "nonprogressive_motility": "Non-progressive motility, NP (%)",
    "immotile": "Immotile spermatozoa, IM (%)",
    "vitality": "Vitality, live spermatozoa (%)",
    "normal_forms": "Normal forms (%)",
}

# Campbell et al. 2021, Table 3 ("Analysis 2: WHO 2020").
# n, then the nine centiles in CENTILES order, then the 95% CI of the 5th.
_WHO2020 = {
    "volume":                  (3586, (1.0, 1.4, 1.8, 2.3, 3.0, 4.2, 5.5, 6.2, 6.9), (1.3, 1.5)),
    "concentration":           (3587, (11, 16, 22, 36, 66, 110, 166, 208, 254), (15, 18)),
    "total_number":            (3584, (29, 39, 58, 108, 210, 363, 561, 701, 865), (35, 40)),
    "total_motility":          (3488, (35, 42, 47, 55, 64, 73, 83, 90, 92), (40, 43)),
    "progressive_motility":    (3389, (24, 30, 36, 45, 55, 63, 71, 77, 81), (29, 31)),
    "nonprogressive_motility": (3387, (1, 1, 2, 4, 8, 15, 26, 32, 38), (1, 1)),
    "immotile":                (2800, (15, 20, 23, 30, 37, 45, 53, 58, 65), (19, 20)),
    "vitality":                (1337, (45, 54, 60, 69, 78, 88, 95, 97, 98), (50, 56)),
    "normal_forms":            (3335, (3, 4, 5, 8, 14, 23, 32, 39, 45), (3.9, 4.0)),
}

# Campbell et al. 2021, Table 2 ("Analysis 1: 2010-2020 data").
_2010_2020 = {
    "volume":                  (1789, (1.0, 1.2, 1.5, 2.0, 2.8, 3.8, 5.0, 5.5, 6.0), (1.1, 1.4)),
    "concentration":           (1789, (14, 18, 22, 31, 60, 104, 157, 203, 243), (15, 20)),
    "total_number":            (1789, (30, 36, 50, 88, 168, 288, 467, 573, 679), (33, 40)),
    "total_motility":          (1789, (35, 43, 50, 59, 67, 78, 90, 92, 94), (40, 45)),
    "progressive_motility":    (1789, (22, 27, 34, 44, 54, 64, 75, 80, 84), (26, 30)),
    "nonprogressive_motility": (1789, (0, 1, 2, 6, 12, 20, 32, 37, 40), (1, 1)),
    "immotile":                (1101, (10, 15, 20, 27, 35, 43, 50, 57, 66), (12, 17)),
    "vitality":                (1337, (45, 54, 60, 69, 78, 88, 95, 97, 98), (50, 56)),
    "normal_forms":            (1621, (3, 4, 5, 7, 12, 19, 30, 32, 34), (3.1, 4.0)),
}

# WHO 2010 (5th edition; Cooper et al., Hum Reprod Update 2010) lower reference
# limits (5th centile). Only the limits are carried, not the full distribution.
_WHO2010_LRL = {
    "volume": 1.5,
    "concentration": 15,
    "total_number": 39,
    "total_motility": 40,
    "progressive_motility": 32,
    "vitality": 58,
    "normal_forms": 4,
}

_TABLES = {"who2020": _WHO2020, "2010_2020": _2010_2020}


def _table(edition: str) -> dict:
    try:
        return _TABLES[edition]
    except KeyError:
        raise ValueError(f"edition must be one of {sorted(_TABLES)} or 'who2010'") from None


def _check_parameter(parameter: str) -> None:
    if parameter not in PARAMETERS:
        raise ValueError(f"parameter must be one of {sorted(PARAMETERS)}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def semen_reference(parameter: str | None = None, edition: str = "who2020") -> pd.DataFrame:
    """The published reference distribution as a DataFrame.

    Parameters
    ----------
    parameter : str, optional
        One of ``PARAMETERS``; omit for every parameter.
    edition : {"who2020", "2010_2020"}, default "who2020"
        Table 3 (WHO 2020 combined data) or Table 2 (2010-2020 studies only)
        of Campbell et al. 2021.

    Returns
    -------
    pandas.DataFrame
        One row per parameter: ``label``, ``n``, the nine centile columns
        (``p2.5`` ... ``p97.5``) and ``p5_ci_low`` / ``p5_ci_high``.
    """
    tab = _table(edition)
    keys = [parameter] if parameter else list(PARAMETERS)
    for k in keys:
        _check_parameter(k)
    rows = []
    for k in keys:
        n, vals, ci = tab[k]
        row = {"parameter": k, "label": PARAMETERS[k], "n": n}
        row.update({f"p{c:g}": v for c, v in zip(CENTILES, vals)})
        row["p5_ci_low"], row["p5_ci_high"] = ci
        rows.append(row)
    return pd.DataFrame(rows).set_index("parameter")


def lower_reference_limit(parameter: str, edition: str = "who2020") -> float:
    """The 5th centile ("lower reference limit") for one parameter.

    ``edition="who2010"`` returns the 5th-edition limit (Cooper et al. 2010).
    """
    _check_parameter(parameter)
    if edition == "who2010":
        try:
            return float(_WHO2010_LRL[parameter])
        except KeyError:
            raise ValueError(f"WHO 2010 did not publish a limit for {parameter!r}") from None
    return float(_table(edition)[parameter][1][CENTILES.index(5)])


def semen_percentile(parameter: str, value, edition: str = "who2020"):
    """Where a value sits in the fertile-man distribution, in percent.

    Linear interpolation between the published centiles. Values below the
    2.5th centile return 2.5 and values above the 97.5th return 97.5, since
    the tails are not published. The result is therefore an approximation
    of the empirical percentile, exact only at the nine published points.

    Parameters
    ----------
    parameter : str
        One of ``PARAMETERS``.
    value : float or array-like
        The measured value, in the parameter's published units.
    edition : {"who2020", "2010_2020"}, default "who2020"

    Returns
    -------
    float or numpy.ndarray
        Percentile between 2.5 and 97.5; NaN for NaN input.

    Examples
    --------
    >>> semen_percentile("concentration", 16)
    5.0
    >>> round(semen_percentile("concentration", 66), 1)
    50.0
    """
    _check_parameter(parameter)
    _, vals, _ = _table(edition)[parameter]
    x = np.asarray(value, dtype=float)
    xp = np.asarray(vals, dtype=float)
    fp = np.asarray(CENTILES, dtype=float)
    # np.interp needs strictly increasing xp; collapse ties (e.g. NP 1, 1) by
    # keeping the last occurrence so a value at the tie maps to the upper centile.
    keep = np.r_[xp[1:] != xp[:-1], True]
    out = np.interp(x, xp[keep], fp[keep])
    out = np.where(np.isnan(x), np.nan, out)
    return float(out) if out.ndim == 0 else out


def below_reference(parameter: str, value, edition: str = "who2020"):
    """True where ``value`` is below the lower reference limit (5th centile).

    Returns a bool, or a boolean/object array for array input (NaN stays NaN).
    """
    lrl = lower_reference_limit(parameter, edition)
    x = np.asarray(value, dtype=float)
    out = x < lrl
    if np.isnan(x).any():
        out = np.where(np.isnan(x), np.nan, out)
    return bool(out) if out.ndim == 0 else out


def add_semen_percentile_cols(
    df,
    columns: dict | None = None,
    edition: str = "who2020",
    suffix: str = "_pct",
    flag_suffix: str | None = "_below_lrl",
    copy: bool = True,
):
    """Add percentile (and optional below-limit flag) columns to a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per semen analysis.
    columns : dict, optional
        Mapping of parameter name to column name, e.g.
        ``{"concentration": "conc", "progressive_motility": "pr"}``. Defaults
        to the parameter names themselves for any that are present in ``df``.
    edition : {"who2020", "2010_2020"}, default "who2020"
    suffix : str, default "_pct"
        Appended to the column name for the percentile column.
    flag_suffix : str or None, default "_below_lrl"
        Appended for the boolean below-5th-centile column; ``None`` to skip.
    copy : bool, default True
        Work on a copy and leave ``df`` unchanged.

    Returns
    -------
    pandas.DataFrame
    """
    out = df.copy() if copy else df
    if columns is None:
        columns = {k: k for k in PARAMETERS if k in out.columns}
    for parameter, col in columns.items():
        _check_parameter(parameter)
        vals = pd.to_numeric(out[col], errors="coerce").to_numpy()
        out[f"{col}{suffix}"] = semen_percentile(parameter, vals, edition)
        if flag_suffix:
            out[f"{col}{flag_suffix}"] = pd.array(below_reference(parameter, vals, edition), dtype="boolean")
    return out


__all__ = [
    "CENTILES",
    "PARAMETERS",
    "semen_reference",
    "lower_reference_limit",
    "semen_percentile",
    "below_reference",
    "add_semen_percentile_cols",
]
