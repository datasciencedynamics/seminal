"""Fetch the Tradewell et al. 2022 azoospermia dataset for seminal.

Downloads the CC0 Excel file deposited on Harvard Dataverse
(doi:10.7910/DVN/EQFMCM) and saves each sheet unchanged as Parquet
(optionally CSV) in data/raw/. No filtering or recoding here; that
lives in preprocessing.py.

Usage:
    python data_gen.py
    python data_gen.py --csv
    python data_gen.py --from-file ~/Downloads/FSH_DeI_Data_WJMH.xlsx
"""

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


@app.command()
def main(
    out_dir: Path = typer.Option(Path("data/raw"), help="Where to save raw files."),
    csv: bool = typer.Option(False, "--csv", help="Also save a CSV backup."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Re-download existing files."),
    from_file: Path = typer.Option(
        None, "--from-file", help="Use a locally downloaded copy instead of Dataverse."
    ),
):
    out_dir.mkdir(parents=True, exist_ok=True)
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


if __name__ == "__main__":
    app()
