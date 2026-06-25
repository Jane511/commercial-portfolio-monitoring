"""Portfolio concentration analytics on real SBA loans.

Exposure and loan-count concentration by industry (NAICS sector), borrower
state, and lender, each with a top-N share and the Herfindahl-Hirschman Index
(HHI = sum of squared segment shares; higher = more concentrated).
"""
from __future__ import annotations

import pandas as pd

from .config import load_config
from .logger import get_logger
from .utils import herfindahl_index, top_n_share

_log = get_logger(__name__)

# Maps a friendly dimension name to the base-table column holding it.
#   industry — NAICS sector
#   state    — borrower state (geography)
#   lender   — ORIGINATING bank / channel (third-party-originator reliance,
#              APS 220 para 39), NOT the borrower
#   borrower — single-name / brand-cluster obligor concentration (APS 220 para
#              35(a); gap review G1). SBA top names are franchise brands.
DIMENSIONS = {
    "industry": "naics_sector",
    "state": "borrstate",
    "lender": "bankname",
    "borrower": "borrname",
}

_EXPOSURE = "grossapproval"


def concentration_by(df: pd.DataFrame, dimension: str, top_n: int | None = None) -> pd.DataFrame:
    """Top-N segments for *dimension* by exposure, with shares and charge-off rate.

    Returns one row per segment (largest first) with: loan count, total gross
    approval (exposure), exposure share, count share, and the segment's
    charge-off rate (count and $).
    """
    cfg = load_config()
    n = top_n or cfg["concentration"]["top_n"]
    col = DIMENSIONS.get(dimension, dimension)

    total_exposure = float(df[_EXPOSURE].sum())
    total_count = len(df)

    grouped = df.groupby(col, dropna=False).agg(
        loan_count=(_EXPOSURE, "size"),
        exposure=(_EXPOSURE, "sum"),
        defaults=("is_default", "sum"),
        chargeoff_amount=("grosschargeoffamount", "sum"),
    )
    grouped["exposure_share"] = (grouped["exposure"] / total_exposure).round(4)
    grouped["count_share"] = (grouped["loan_count"] / total_count).round(4)
    grouped["chargeoff_rate_count"] = (grouped["defaults"] / grouped["loan_count"]).round(4)
    grouped["chargeoff_rate_dollar"] = (grouped["chargeoff_amount"] / grouped["exposure"]).round(4)

    out = (
        grouped.sort_values("exposure", ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={col: dimension})
    )
    return out


def hhi_summary(df: pd.DataFrame) -> pd.DataFrame:
    """HHI and top-N exposure share for each concentration dimension."""
    cfg = load_config()
    n = cfg["concentration"]["top_n"]
    moderate = cfg["concentration"]["hhi_moderate_threshold"]
    high = cfg["concentration"]["hhi_high_threshold"]

    records = []
    for dimension, col in DIMENSIONS.items():
        exposure_by_seg = df.groupby(col, dropna=False)[_EXPOSURE].sum()
        hhi = herfindahl_index(exposure_by_seg)
        level = "High" if hhi >= high else "Moderate" if hhi >= moderate else "Low"
        records.append({
            "dimension": dimension,
            "segments": int(exposure_by_seg.shape[0]),
            "hhi": hhi,
            "concentration_level": level,
            f"top{n}_exposure_share": top_n_share(exposure_by_seg, n),
        })
        _log.info("Concentration %s: HHI=%.4f (%s), %d segments",
                  dimension, hhi, level, exposure_by_seg.shape[0])

    return pd.DataFrame.from_records(records)


def originator_performance(df: pd.DataFrame, top_n: int = 15,
                           min_loans: int = 500) -> pd.DataFrame:
    """Charge-off performance by ORIGINATING lender — third-party oversight.

    APS 220 para 39 / APG 220 paras 307-308: third-party-originated exposures
    warrant enhanced monitoring. SBA 7(a) loans are written by originating
    lenders (``bankname``); this surfaces each material originator's realised
    charge-off rate (count and $) so a poorly-performing channel is visible, not
    just its volume. Restricted to lenders with at least ``min_loans`` loans so a
    tiny originator with one default does not top the table, and returned
    worst-first by count charge-off rate.
    """
    grouped = df.groupby("bankname", dropna=False).agg(
        loan_count=(_EXPOSURE, "size"),
        exposure=(_EXPOSURE, "sum"),
        defaults=("is_default", "sum"),
        nonperforming=("is_nonperforming", "sum"),
        chargeoff_amount=("grosschargeoffamount", "sum"),
    )
    total_exposure = float(df[_EXPOSURE].sum())
    grouped = grouped[grouped["loan_count"] >= min_loans].copy()
    grouped["exposure_share"] = (grouped["exposure"] / total_exposure).round(4)
    grouped["chargeoff_rate_count"] = (grouped["defaults"] / grouped["loan_count"]).round(4)
    grouped["chargeoff_rate_dollar"] = (grouped["chargeoff_amount"] / grouped["exposure"]).round(4)
    grouped["nonperforming_rate"] = (grouped["nonperforming"] / grouped["loan_count"]).round(4)

    out = (
        grouped.sort_values("chargeoff_rate_count", ascending=False)
        .head(top_n)
        .reset_index()
        .rename(columns={"bankname": "originating_lender"})
    )
    _log.info(
        "Originator performance: %d lenders with >=%d loans; worst count rate %.1f%%",
        int((df.groupby('bankname')[_EXPOSURE].size() >= min_loans).sum()),
        min_loans, (out['chargeoff_rate_count'].iloc[0] * 100) if len(out) else float('nan'),
    )
    return out
