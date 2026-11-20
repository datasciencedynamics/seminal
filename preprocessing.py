"""Build an analysis-ready table from the Tradewell et al. 2022 raw sheets.

Reads the per-site Parquet files saved by data_gen.py, harmonizes column
names across sites, derives the azoospermia outcome and mean testis volume,
applies the paper's exclusion criteria as an ``included`` flag, and
median-imputes LH, testosterone and testis volume within site as the paper
did. Output: data/processed/tradewell_2022.parquet (one row per sample).

Usage:
    python preprocessing.py
    python preprocessing.py --csv
    python preprocessing.py --no-impute
"""

from pathlib import Path

import numpy as np
import pandas as pd
import typer

app = typer.Typer(add_completion=False)

SITES = {"site_1": "miami", "site_2": "milan", "site_3": "chicago"}

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


def load_us_site(path: Path, site: str) -> pd.DataFrame:
    df = pd.read_parquet(path).rename(columns=US_RENAME)
    df["site"] = site
    df["azoospermia"] = (df["sperm_concentration"] == 0).astype(int)
    df["testis_volume"] = df[["testis_volume_left", "testis_volume_right"]].mean(axis=1)
    # Paper exclusions: vasectomy, Y microdeletion, solitary testis,
    # testosterone or anabolic steroid use in the prior 120 days.
    excluded = (
        (df["prior_vasectomy"] == 1)
        | (df["y_microdeletion"] == 1)
        | (df["absent_testis_reason"] > 0)
        | (df["med_testosterone"] == 1)
        | (df["med_anabolic_steroid"] == 1)
    )
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
):
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = [
        load_us_site(raw_dir / "site_1.parquet", "miami"),
        load_milan(raw_dir / "site_2.parquet"),
        load_us_site(raw_dir / "site_3.parquet", "chicago"),
    ]
    df = pd.concat(frames, ignore_index=True, sort=False)

    if impute:
        for col in IMPUTE_COLS:
            df[col] = df.groupby("site")[col].transform(lambda s: s.fillna(s.median()))

    front = ["site", "included", "azoospermia", "age", "fsh", "lh", "testosterone",
             "testis_volume", "testis_volume_method", "sperm_concentration", "sperm_motility"]
    df = df[front + [c for c in df.columns if c not in front]]

    out = out_dir / "tradewell_2022.parquet"
    df.to_parquet(out, index=False)
    if csv:
        df.to_csv(out.with_suffix(".csv"), index=False)

    typer.echo(f"saved  {out} ({len(df):,} rows)")
    summary = (
        df.groupby("site")
        .agg(n_raw=("azoospermia", "size"),
             n_included=("included", "sum"),
             n_azoo_included=("azoospermia", lambda s: int(s[df.loc[s.index, "included"]].sum())))
    )
    typer.echo(summary.to_string())


if __name__ == "__main__":
    app()
