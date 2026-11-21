"""Fetch the raw datasets behind seminal.

* ``tradewell``: the CC0 Excel file deposited on Harvard Dataverse
  (doi:10.7910/DVN/EQFMCM) behind Tradewell et al. 2022; each sheet is saved
  unchanged as Parquet (optionally CSV) in data/raw/.
* ``fertile_man``: the CC BY Fertile_Man_2020.xlsx on the University of Dundee
  research portal (doi:10.15132/10000163) behind Campbell et al. 2021 and the
  WHO 2021 reference distribution; saved as data/raw/fertile_man_2020.parquet.

No filtering or recoding here; that lives in preprocessing.py.

Usage:
    python data_gen.py                      # both datasets
    python data_gen.py --source tradewell
    python data_gen.py --source fertile_man --from-file ~/Downloads/Fertile_Man_2020.xlsx
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests
import typer

app = typer.Typer(add_completion=False)

DATAVERSE = "https://dataverse.harvard.edu"
DATASET_DOI = "doi:10.7910/DVN/EQFMCM"
RAW_NAME = "FSH_DeI_Data_WJMH.xlsx"

# Sheet -> what it holds (see the Key sheet for column definitions)
SHEETS = {
    "Site 1": "Miami (development cohort, pre-exclusion)",
    "Site 2": "Milan (external validation)",
    "Site 3": "Chicago (external validation, pre-exclusion)",
    "Key": "column definitions",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (seminal data_gen)"}

# Campbell et al. 2021 / WHO 2021 reference men (Dundee research portal, CC BY)
FERTILE_MAN_DOI = "doi:10.15132/10000163"
FERTILE_MAN_URL = "https://discovery.dundee.ac.uk/files/56864058/Fertile_Man_2020.xlsx"
FERTILE_MAN_NAME = "Fertile_Man_2020.xlsx"
FERTILE_MAN_SHEET = "Fertile Man 2020"


def fetch_xlsx() -> bytes:
    """Resolve the dataset's single file on Dataverse and download the original."""
    meta = requests.get(
        f"{DATAVERSE}/api/datasets/:persistentId/",
        params={"persistentId": DATASET_DOI},
        headers=HEADERS,
        timeout=60,
    )
    meta.raise_for_status()
    files = meta.json()["data"]["latestVersion"]["files"]
    if len(files) != 1:
        raise RuntimeError(f"expected one file in {DATASET_DOI}, found {len(files)}")
    file_id = files[0]["dataFile"]["id"]

    resp = requests.get(
        f"{DATAVERSE}/api/access/datafile/{file_id}",
        params={"format": "original"},
        headers=HEADERS,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.content


def fetch_tradewell(out_dir: Path, csv: bool, overwrite: bool, from_file: Path | None) -> None:
    xlsx_path = out_dir / RAW_NAME

    if xlsx_path.exists() and not overwrite:
        typer.echo(f"skip   {RAW_NAME} (exists)")
        content = xlsx_path.read_bytes()
    elif from_file is not None:
        typer.echo(f"copy   {from_file}")
        content = Path(from_file).read_bytes()
        xlsx_path.write_bytes(content)
    else:
        typer.echo(f"fetch  {DATASET_DOI} -> {RAW_NAME}")
        content = fetch_xlsx()
        xlsx_path.write_bytes(content)

    for sheet, desc in SHEETS.items():
        stem = sheet.lower().replace(" ", "_")
        parquet_path = out_dir / f"{stem}.parquet"
        header = None if sheet == "Key" else 0
        df = pd.read_excel(io.BytesIO(content), sheet_name=sheet, header=header)
        df.columns = [str(c) for c in df.columns]
        df.to_parquet(parquet_path, index=False)
        if csv:
            df.to_csv(out_dir / f"{stem}.csv", index=False)
        typer.echo(f"saved  {parquet_path} ({len(df):,} rows, {df.shape[1]} cols): {desc}")


def fetch_fertile_man(out_dir: Path, csv: bool, overwrite: bool, from_file: Path | None) -> None:
    xlsx_path = out_dir / FERTILE_MAN_NAME
    if xlsx_path.exists() and not overwrite:
        typer.echo(f"skip   {FERTILE_MAN_NAME} (exists)")
        content = xlsx_path.read_bytes()
    elif from_file is not None:
        typer.echo(f"copy   {from_file}")
        content = Path(from_file).read_bytes()
        xlsx_path.write_bytes(content)
    else:
        typer.echo(f"fetch  {FERTILE_MAN_DOI} -> {FERTILE_MAN_NAME}")
        resp = requests.get(FERTILE_MAN_URL, headers=HEADERS, timeout=120)
        resp.raise_for_status()
        content = resp.content
        xlsx_path.write_bytes(content)

    # One data sheet (the second sheet in the file is empty). Values are kept
    # as read, including the "NO RESULT" strings; preprocessing.py coerces them.
    df = pd.read_excel(io.BytesIO(content), sheet_name=FERTILE_MAN_SHEET)
    df.columns = [str(c) for c in df.columns]
    df = df.astype(str)
    parquet_path = out_dir / "fertile_man_2020.parquet"
    df.to_parquet(parquet_path, index=False)
    if csv:
        df.to_csv(out_dir / "fertile_man_2020.csv", index=False)
    typer.echo(f"saved  {parquet_path} ({len(df):,} rows, {df.shape[1]} cols): "
               "Campbell et al. 2021 / WHO 2021 reference men")


@app.command()
def main(
    out_dir: Path = typer.Option(Path("data/raw"), help="Where to save raw files."),
    csv: bool = typer.Option(False, "--csv", help="Also save a CSV backup."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Re-download existing files."),
    from_file: Path = typer.Option(
        None, "--from-file", help="Use a locally downloaded copy of the chosen source instead of fetching."
    ),
    source: str = typer.Option("all", help="'tradewell', 'fertile_man' or 'all'."),
):
    if source not in ("tradewell", "fertile_man", "all"):
        raise typer.BadParameter("source must be 'tradewell', 'fertile_man' or 'all'")
    if from_file is not None and source == "all":
        raise typer.BadParameter("--from-file needs --source tradewell or --source fertile_man")
    out_dir.mkdir(parents=True, exist_ok=True)
    if source in ("tradewell", "all"):
        fetch_tradewell(out_dir, csv, overwrite, from_file)
    if source in ("fertile_man", "all"):
        fetch_fertile_man(out_dir, csv, overwrite, from_file)


if __name__ == "__main__":
    app()
