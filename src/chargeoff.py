"""Charge-off rate analytics by industry, loan-size band, and vintage.

Charge-off rate = charged-off count (or $) / total in the segment. The dollar
rate uses GrossChargeOffAmount over GrossApproval (exposure at approval).
"""
from __future__ import annotations

import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)

_EXPOSURE = "grossapproval"


def _rate_table(df: pd.DataFrame, group_col: str, label: str) -> pd.DataFrame:
    """Charge-off rates for one grouping column."""
    grouped = df.groupby(group_col, dropna=False, observed=True).agg(
        loan_count=(_EXPOSURE, "size"),
        defaults=("is_default", "sum"),
        exposure=(_EXPOSURE, "sum"),
        chargeoff_amount=("grosschargeoffamount", "sum"),
    )
    grouped["chargeoff_rate_count"] = (grouped["defaults"] / grouped["loan_count"]).round(4)
    grouped["chargeoff_rate_dollar"] = (grouped["chargeoff_amount"] / grouped["exposure"]).round(4)
    out = grouped.reset_index().rename(columns={group_col: label})
    return out


def chargeoff_by_industry(df: pd.DataFrame) -> pd.DataFrame:
    """Charge-off rate by NAICS sector, sorted worst-first by count rate."""
    out = _rate_table(df, "naics_sector", "industry")
    return out.sort_values("chargeoff_rate_count", ascending=False).reset_index(drop=True)


def chargeoff_by_size_band(df: pd.DataFrame) -> pd.DataFrame:
    """Charge-off rate by loan-size band, in natural band order."""
    out = _rate_table(df, "size_band", "size_band")
    # Preserve the categorical order defined in config (small -> large).
    if isinstance(df["size_band"].dtype, pd.CategoricalDtype):
        order = list(df["size_band"].cat.categories)
        out["size_band"] = pd.Categorical(out["size_band"], categories=order, ordered=True)
        out = out.sort_values("size_band").reset_index(drop=True)
    return out


def chargeoff_by_vintage(df: pd.DataFrame) -> pd.DataFrame:
    """Charge-off rate by approval-year vintage, oldest-first.

    The ``fully_seasoned`` flag warns that recent vintages under-report their
    ultimate charge-off rate (some loans have not yet failed).
    """
    out = _rate_table(df, "vintage", "vintage")
    seasoned = df.groupby("vintage", observed=True)["fully_seasoned"].first()
    out = out.merge(seasoned.rename("fully_seasoned"), left_on="vintage", right_index=True)
    return out.sort_values("vintage").reset_index(drop=True)
