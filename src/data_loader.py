"""Load and clean the real SBA 7(a) FOIA loan-level data.

The raw CSVs (one row per approved loan) are read from ``data/input/`` and
cleaned into a single tidy frame: parsed dates, normalised LoanStatus codes,
NAICS mapped to a 2-digit sector name, and never-funded loans dropped.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import (
    DEFAULT_INPUT_GLOB,
    INPUT_DIR,
    LOAN_STATUS_LABELS,
    NAICS_SECTOR_NAMES,
    RAW_COLUMNS,
    load_config,
)
from .logger import get_logger

_log = get_logger(__name__)

_DATE_COLS = ["approvaldate", "paidinfulldate", "chargeoffdate"]


def find_input_files(input_dir: str | Path | None = None) -> list[Path]:
    """Return the SBA FOIA CSVs in *input_dir*, sorted by name."""
    inp = Path(input_dir) if input_dir is not None else INPUT_DIR
    files = sorted(inp.glob(DEFAULT_INPUT_GLOB))
    if not files:
        raise FileNotFoundError(
            f"No SBA input files matching '{DEFAULT_INPUT_GLOB}' found in {inp}. "
            "Download the 7(a) FOIA CSVs from https://data.sba.gov and place "
            "them in data/input/ (see README -> Data sources & provenance)."
        )
    return files


def _clean_status(series: pd.Series) -> pd.Series:
    """Collapse internal whitespace in LoanStatus codes ('P I F' -> 'P I F').

    The codes are kept verbatim (still 'P I F' with single spaces) but trimmed
    and upper-cased so stray formatting does not create spurious categories.
    """
    return (
        series.astype("string")
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )


def load_raw(input_dir: str | Path | None = None) -> pd.DataFrame:
    """Read and concatenate the raw SBA CSVs (only the columns we use)."""
    files = find_input_files(input_dir)
    _log.info("Loading %d SBA input file(s): %s", len(files), [f.name for f in files])

    frames = []
    for f in files:
        df = pd.read_csv(
            f,
            usecols=lambda c: c in RAW_COLUMNS,
            dtype={"naicscode": "string"},
            low_memory=False,
        )
        df["source_file"] = f.name
        frames.append(df)
        _log.info("  %s -> %d rows", f.name, len(df))

    raw = pd.concat(frames, ignore_index=True)
    _log.info("Combined raw frame: %d rows", len(raw))
    return raw


def clean(raw: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Clean the raw SBA frame into the analysis-ready loan table.

    Steps: parse dates, normalise status codes, map NAICS -> sector, derive a
    plain-English status label, and drop never-funded loans (CANCLD/COMMIT).
    """
    cfg = config or load_config()
    df = raw.copy()

    # --- dates (MM/DD/YYYY in the source) -------------------------------- #
    for col in _DATE_COLS:
        df[col] = pd.to_datetime(df[col], format="%m/%d/%Y", errors="coerce")

    # --- numeric coercions ----------------------------------------------- #
    for col in ("grossapproval", "sbaguaranteedapproval", "grosschargeoffamount",
                "terminmonths", "approvalfy", "jobssupported"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["grosschargeoffamount"] = df["grosschargeoffamount"].fillna(0.0)

    # --- status normalisation + label ------------------------------------ #
    df["loanstatus"] = _clean_status(df["loanstatus"])
    df["status_label"] = df["loanstatus"].map(LOAN_STATUS_LABELS).fillna("Other")

    # --- NAICS -> 2-digit sector ----------------------------------------- #
    # naicscode arrives as a string that may carry a trailing ".0" from float
    # parsing in some extracts; take the leading 2 digits of the integer part.
    sector2 = (
        df["naicscode"].astype("string").str.strip().str.split(".").str[0].str[:2]
    )
    df["naics_sector_code"] = sector2
    df["naics_sector"] = sector2.map(NAICS_SECTOR_NAMES).fillna("Unknown / Unclassified")

    # --- drop never-funded loans ----------------------------------------- #
    exclude = set(cfg["universe"]["exclude_statuses"])
    n_before = len(df)
    df = df[~df["loanstatus"].isin(exclude)].reset_index(drop=True)
    _log.info(
        "Dropped %d never-funded loans (%s); %d funded loans remain",
        n_before - len(df), sorted(exclude), len(df),
    )
    return df


def load_clean(input_dir: str | Path | None = None,
               config: dict | None = None) -> pd.DataFrame:
    """Convenience: ``load_raw`` then ``clean``."""
    return clean(load_raw(input_dir), config=config)


def data_quality_summary(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """One-table data-quality / coverage snapshot of the cleaned portfolio."""
    cfg = config or load_config()
    default_statuses = set(cfg["universe"]["default_statuses"])

    is_default = df["loanstatus"].isin(default_statuses)
    total = len(df)
    rows = [
        ("Funded loans", f"{total:,}"),
        ("Approval FY range", f"{int(df['approvalfy'].min())}-{int(df['approvalfy'].max())}"),
        ("Total gross approval ($)", f"{df['grossapproval'].sum():,.0f}"),
        ("Charged-off loans (count)", f"{int(is_default.sum()):,}"),
        ("Charge-off rate (count)", f"{is_default.mean():.2%}"),
        ("Charge-off rate ($)",
         f"{df.loc[is_default, 'grosschargeoffamount'].sum() / df['grossapproval'].sum():.2%}"),
        ("Distinct NAICS sectors", f"{df['naics_sector'].nunique()}"),
        ("Distinct borrower states", f"{df['borrstate'].nunique()}"),
        ("Distinct lenders", f"{df['bankname'].nunique():,}"),
        ("Missing NAICS sector", f"{(df['naics_sector'] == 'Unknown / Unclassified').sum():,}"),
        ("Missing approval date", f"{df['approvaldate'].isna().sum():,}"),
        ("Charge-offs missing charge-off date", f"{(is_default & df['chargeoffdate'].isna()).sum():,}"),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])
