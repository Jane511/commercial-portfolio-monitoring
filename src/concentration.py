from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CONCENTRATION_LIMITS


def calculate_hhi(df: pd.DataFrame, group_field: str) -> float:
    """Herfindahl-Hirschman Index by the specified grouping field.

    HHI = sum(share_i^2) where share_i = EAD_i / total_EAD.
    HHI ranges from ~0 (diversified) to 1.0 (single concentration).
    """
    total_ead = float(df["ead"].sum())
    if total_ead <= 0:
        return 0.0
    shares = df.groupby(group_field)["ead"].sum() / total_ead
    return round(float((shares ** 2).sum()), 6)


def _classify_hhi(hhi: float, limits: dict | None = None) -> str:
    lim = limits or CONCENTRATION_LIMITS
    if hhi >= lim["hhi_high_threshold"]:
        return "High"
    if hhi >= lim["hhi_moderate_threshold"]:
        return "Moderate"
    return "Low"


def check_single_name_concentration(
    df: pd.DataFrame,
    limit_pct: float | None = None,
) -> pd.DataFrame:
    """Flag borrowers whose EAD exceeds the single-name limit."""
    limit = limit_pct or CONCENTRATION_LIMITS["single_name_pct"]
    total_ead = float(df["ead"].sum())
    threshold = total_ead * limit

    borrower_ead = df.groupby("borrower_id", as_index=False).agg(
        total_ead=("ead", "sum"),
        facility_count=("facility_id", "count"),
    )
    borrower_ead["ead_share"] = (borrower_ead["total_ead"] / max(total_ead, 1)).round(4)
    borrower_ead["breach"] = borrower_ead["total_ead"] > threshold
    borrower_ead["limit_pct"] = limit

    return borrower_ead.sort_values("total_ead", ascending=False).reset_index(drop=True)


def check_sector_concentration(
    df: pd.DataFrame,
    limit_pct: float | None = None,
) -> pd.DataFrame:
    """Flag industries exceeding the sector concentration limit."""
    limit = limit_pct or CONCENTRATION_LIMITS["sector_pct"]
    total_ead = float(df["ead"].sum())
    threshold = total_ead * limit

    sector_ead = df.groupby("industry", as_index=False).agg(
        total_ead=("ead", "sum"),
        facility_count=("facility_id", "count"),
    )
    sector_ead["ead_share"] = (sector_ead["total_ead"] / max(total_ead, 1)).round(4)
    sector_ead["breach"] = sector_ead["total_ead"] > threshold
    sector_ead["limit_pct"] = limit

    return sector_ead.sort_values("total_ead", ascending=False).reset_index(drop=True)


def generate_concentration_report(df: pd.DataFrame) -> pd.DataFrame:
    """Comprehensive concentration metrics across all dimensions."""
    records: list[dict] = []

    for dimension in ("industry", "region", "product_type", "borrower_id"):
        hhi = calculate_hhi(df, dimension)
        records.append({
            "dimension": dimension,
            "hhi": hhi,
            "concentration_level": _classify_hhi(hhi),
            "unique_values": int(df[dimension].nunique()),
        })

    return pd.DataFrame.from_records(records)
