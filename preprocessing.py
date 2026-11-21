"""Build analysis-ready tables from the raw files saved by data_gen.py.

Two outputs:

* data/processed/tradewell_2022.parquet from the Tradewell et al. 2022 sheets
  (azoospermia cohorts), described below.
* data/processed/fertile_man_2020.parquet from Fertile_Man_2020.xlsx (the
  Campbell et al. 2021 / WHO 2021 reference men): the nine semen parameters
  renamed to the names used by ``seminal.semen``, "NO RESULT" and other
  non-numeric entries set to missing, and the contributing study kept as
  ``study``. Nothing is excluded or imputed; the paper used every value present.

Tradewell et al. 2022
---------------------

Reads the per-site Parquet files saved by data_gen.py, harmonizes column
names across sites, derives the azoospermia outcome and mean testis volume,
applies exclusion criteria as an ``included`` flag, and median-imputes LH,
testosterone and testis volume within site as the paper did.
Output: data/processed/tradewell_2022.parquet (one row per sample).

Two exclusion rules are available:

* ``reproduced`` (default): the rule that reproduces the paper's sample sizes
  exactly (Miami 946/131, Milan 1955/465, Chicago 596/191). Reverse-engineered
  from the deposit: Y microdeletion is NOT excluded; Miami absent-testis codes
  1-3 are excluded (code 4 kept); Chicago absent testis is a zero volume; and
  Chicago sperm concentration below 0.01 million/mL counts as azoospermia.
* ``stated``: the criteria as written in the Methods (vasectomy, Y
  microdeletion, solitary testis, testosterone or steroid use), with
  azoospermia = sperm concentration of exactly 0. Gives 943 / 1955 / 614.

Usage:
    python preprocessing.py
    python preprocessing.py --exclusions stated
    python preprocessing.py --csv --no-impute
"""

from pathlib import Path

import numpy as np
import pandas as pd
import typer

app = typer.Typer(add_completion=False)

SITES = {"site_1": "miami", "site_2": "milan", "site_3": "chicago"}

# Fertile_Man_2020.xlsx column -> seminal.semen parameter name
FERTILE_MAN_RENAME = {
    "PI": "study",
    "Semen Volume (ml)": "volume",
    "Sperm Concentration (106/ml)": "concentration",
    "Total Number (106)": "total_number",
    "Total Motility (%)": "total_motility",
    "Progressive Motility (%)": "progressive_motility",
    "Non-progressive Motility (%)": "nonprogressive_motility",
    "Immotile Spermatozoa (%)": "immotile",
    "Vitality (%)": "vitality",
    "Normal Forms (%)": "normal_forms",
}


def load_fertile_man(path: Path) -> pd.DataFrame:
    """Harmonize the Campbell et al. 2021 reference men to the library's names."""
    df = pd.read_parquet(path).rename(columns=FERTILE_MAN_RENAME)
    params = [c for c in FERTILE_MAN_RENAME.values() if c != "study"]
    for c in params:
        df[c] = pd.to_numeric(df[c], errors="coerce")   # "NO RESULT" -> NaN
    return df[["study"] + params]

# Columns common to Site 1 (Miami) and Site 3 (Chicago)
US_RENAME = {
    "Age": "age",
    "SC": "sperm_concentration",
    "SM": "sperm_motility",
    "FSH": "fsh",
    "LH": "lh",
    "T_T": "testosterone",
    "L_Tvol": "testis_volume_left",
    "R_Tvol": "testis_volume_right",
    "Why_Abs": "absent_testis_reason",
    "Chemo": "chemo_history",
    "Kline": "klinefelter",
    "YCMD": "y_microdeletion",
    "HH": "hypogonadotropic_hypogonadism",
    "OA": "obstructive_azoospermia",
    "P_Vas": "prior_vasectomy",
    "M_CC": "med_clomiphene",
    "M_HCG": "med_hcg",
    "M_Ari": "med_anastrozole",
    "M_T": "med_testosterone",
    "M_S": "med_anabolic_steroid",
}

# Site 2 (Milan) uses its own layout
MILAN_RENAME = {
    "Age": "age",
    "S_CONCENTRATION": "sperm_concentration",
    "S_MOTILITY": "sperm_motility",
    "FSH": "fsh",
    "LH": "lh",
    "T_T": "testosterone",
    "AZOO_Type": "azoospermia_type",
    "R_Tvol": "testis_volume_right",
    "L_Tvol": "testis_volume_left",
    "M_Tvol": "testis_volume",
    "P_F_Azo": "paper_fsh_model_pct",
    "clomiphene": "med_clomiphene",
    "gonadotropins_ok": "med_hcg",
}

IMPUTE_COLS = ["lh", "testosterone", "testis_volume"]

# Reference limits used to build the paper's Table 1 (Methods p. 601; Table 1 p. 602).
# The Methods quote LH 1.8-8.6 but Table 1 bins on 1.7-8.6; the table's cutpoint is used.
REFERENCE_BINS = {
    "fsh": ("fsh_cat", [1.5, 7.6], ["Low (<1.5)", "Normal (1.5-7.6)", "High (>7.6)"]),
    "lh": ("lh_cat", [1.7, 8.6], ["Low (<1.7)", "Normal (1.7-8.6)", "High (>8.6)"]),
    "testosterone": ("tt_cat", [300, 1000], ["Low (<300)", "Normal (300-1,000)", "High (>1,000)"]),
    "testis_volume": ("vol_cat", [12.5, 19], ["Small (<12.5)", "Normal (12.5-19)", "Large (>19)"]),
}


def add_reference_bins(df: pd.DataFrame) -> pd.DataFrame:
    """Categorize each hormone and testis volume by the paper's reference limits.

    Boundary values belong to the normal range: Low is strictly below the lower
    limit, High strictly above the upper limit (matches the paper's counts).
    """
    for col, (name, (lo, hi), labels) in REFERENCE_BINS.items():
        x = df[col]
        df[name] = pd.Categorical(
            np.select([x < lo, x > hi], [labels[0], labels[2]], default=labels[1]),
            categories=labels,
        )
        df.loc[x.isna(), name] = np.nan
    return df


AZOO_CUTOFF = 0.01  # million/mL; Chicago records cryptozoospermia as 1e-5 to 1e-3


def load_us_site(path: Path, site: str, exclusions: str) -> pd.DataFrame:
    df = pd.read_parquet(path).rename(columns=US_RENAME)
    df["site"] = site
    df["testis_volume"] = df[["testis_volume_left", "testis_volume_right"]].mean(axis=1)

    vasectomy = df["prior_vasectomy"] == 1
    on_androgens = (df["med_testosterone"] == 1) | (df["med_anabolic_steroid"] == 1)

    if exclusions == "stated":
        df["azoospermia"] = (df["sperm_concentration"] == 0).astype(int)
        excluded = (
            vasectomy
            | (df["y_microdeletion"] == 1)
            | (df["absent_testis_reason"] > 0)
            | on_androgens
        )
    else:  # reproduced
        df["azoospermia"] = (df["sperm_concentration"] < AZOO_CUTOFF).astype(int)
        if site == "chicago":
            # No absent-testis column; a missing testis is recorded as volume 0
            absent = (df["testis_volume_left"] == 0) | (df["testis_volume_right"] == 0)
        else:
            absent = df["absent_testis_reason"].isin([1, 2, 3])
        excluded = vasectomy | absent | on_androgens
    df["included"] = ~excluded
    # Chicago measured testes by ultrasound long axis (cm), not orchidometer (mL)
    df["testis_volume_method"] = "ultrasound_cm" if site == "chicago" else "orchidometer_ml"
    return df


def load_milan(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path).rename(columns=MILAN_RENAME)
    df["site"] = "milan"
    df["azoospermia"] = (df["B_Azo"] == "AZO").astype(int)
    df["obstructive_azoospermia"] = (df["azoospermia_type"] == "OA").astype(int)
    df["included"] = True  # Milan was deposited post-exclusion (n matches the paper)
    df["testis_volume_method"] = "orchidometer_ml"
    return df


@app.command()
def main(
    raw_dir: Path = typer.Option(Path("data/raw"), help="Folder written by data_gen.py."),
    out_dir: Path = typer.Option(Path("data/processed"), help="Where to save the output."),
    csv: bool = typer.Option(False, "--csv", help="Also save a CSV copy."),
    impute: bool = typer.Option(True, help="Median-impute LH, testosterone, testis volume within site."),
    exclusions: str = typer.Option("reproduced", help="'reproduced' (matches the paper's n) or 'stated' (as written)."),
):
    if exclusions not in ("reproduced", "stated"):
        raise typer.BadParameter("exclusions must be 'reproduced' or 'stated'")
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = [
        load_us_site(raw_dir / "site_1.parquet", "miami", exclusions),
        load_milan(raw_dir / "site_2.parquet"),
        load_us_site(raw_dir / "site_3.parquet", "chicago", exclusions),
    ]
    df = pd.concat(frames, ignore_index=True, sort=False)

    if impute:
        for col in IMPUTE_COLS:
            df[col] = df.groupby("site")[col].transform(lambda s: s.fillna(s.median()))

    df = add_reference_bins(df)

    front = ["site", "included", "azoospermia", "age", "fsh", "lh", "testosterone",
             "testis_volume", "testis_volume_method", "sperm_concentration", "sperm_motility",
             "fsh_cat", "lh_cat", "tt_cat", "vol_cat"]
    df = df[front + [c for c in df.columns if c not in front]]

    out = out_dir / "tradewell_2022.parquet"
    df.to_parquet(out, index=False)
    if csv:
        df.to_csv(out.with_suffix(".csv"), index=False)

    typer.echo(f"saved  {out} ({len(df):,} rows, exclusions={exclusions})")

    fm_raw = raw_dir / "fertile_man_2020.parquet"
    if fm_raw.exists():
        fm = load_fertile_man(fm_raw)
        fm_out = out_dir / "fertile_man_2020.parquet"
        fm.to_parquet(fm_out, index=False)
        if csv:
            fm.to_csv(fm_out.with_suffix(".csv"), index=False)
        typer.echo(f"saved  {fm_out} ({len(fm):,} men, {fm['study'].nunique()} studies); "
                   f"non-missing per parameter: {fm.drop(columns='study').notna().sum().to_dict()}")

    summary = (
        df.groupby("site")
        .agg(n_raw=("azoospermia", "size"),
             n_included=("included", "sum"),
             n_azoo_included=("azoospermia", lambda s: int(s[df.loc[s.index, "included"]].sum())))
    )
    summary = summary.loc[["miami", "milan", "chicago"]]
    summary.loc["total"] = summary.sum()
    typer.echo(summary.to_string())


if __name__ == "__main__":
    app()
