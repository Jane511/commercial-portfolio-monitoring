"""Early-warning segmentation.

Flags high-risk segments (industry x vintage x size band) whose charge-off rate
is materially above the portfolio average. Only segments with enough loans to
be statistically meaningful are eligible, so a tiny segment with one unlucky
default is not flagged. Severity tiers off the multiple of the portfolio rate.
"""
from __future__ import annotations

import pandas as pd

from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)


def flag_high_risk_segments(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Return elevated-risk (industry x vintage x size) segments, worst-first.

    Each row: the segment keys, loan count, charge-off rate, the portfolio
    average for reference, the multiple, and a severity flag.
    """
    cfg = config or load_config()
    ew = cfg["early_warning"]
    elevated = ew["elevated_multiple"]
    high = ew["high_multiple"]
    min_loans = ew["min_segment_loans"]

    # Use only fully-seasoned vintages so rates reflect (near-)final outcomes.
    seasoned = df[df["fully_seasoned"]]
    portfolio_rate = float(seasoned["is_default"].mean())
    if portfolio_rate <= 0:
        _log.warning("Portfolio charge-off rate is 0; no segments can be flagged")
        return pd.DataFrame()

    grouped = seasoned.groupby(
        ["naics_sector", "vintage", "size_band"], observed=True
    ).agg(
        loan_count=("is_default", "size"),
        defaults=("is_default", "sum"),
        exposure=("grossapproval", "sum"),
    ).reset_index()

    grouped = grouped[grouped["loan_count"] >= min_loans].copy()
    grouped["chargeoff_rate"] = (grouped["defaults"] / grouped["loan_count"]).round(4)
    grouped["portfolio_rate"] = round(portfolio_rate, 4)
    grouped["rate_multiple"] = (grouped["chargeoff_rate"] / portfolio_rate).round(2)

    flagged = grouped[grouped["rate_multiple"] >= elevated].copy()
    flagged["severity"] = flagged["rate_multiple"].apply(
        lambda m: "High" if m >= high else "Elevated"
    )
    flagged = flagged.rename(columns={"naics_sector": "industry"})
    flagged = flagged.sort_values("rate_multiple", ascending=False).reset_index(drop=True)

    _log.info(
        "Early warning: %d segments flagged (portfolio rate %.2f%%, >= %.1fx threshold, "
        "min %d loans)",
        len(flagged), portfolio_rate * 100, elevated, min_loans,
    )
    return flagged
