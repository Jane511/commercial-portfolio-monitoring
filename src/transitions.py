"""Loan-age status transition view.

SBA is outcome-level data, not a monthly grade panel, so a true monthly
migration matrix is not possible here (see the companion Freddie Mac monitor
for that). The SBA-feasible substitute: bucket charged-off loans by the loan
age at which they charged off, showing how the cumulative charged-off share
builds with loan age — the shape of when commercial defaults actually occur.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)

# Loan-age (months-on-book) bands for the transition view.
_AGE_EDGES = [0, 12, 24, 36, 48, 60, 84, 120, np.inf]
_AGE_LABELS = ["0-12m", "12-24m", "24-36m", "36-48m", "48-60m", "60-84m", "84-120m", "120m+"]


def loan_age_transition(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of charge-offs by loan age, with cumulative share.

    Restricted to fully-seasoned vintages so the age profile is not distorted
    by young cohorts whose later-age defaults have not yet occurred.
    """
    seasoned = df[df["fully_seasoned"]]
    total_loans = len(seasoned)
    defaults = seasoned[seasoned["is_default"] & seasoned["months_to_chargeoff"].notna()]
    total_defaults = len(defaults)

    age_band = pd.cut(defaults["months_to_chargeoff"], bins=_AGE_EDGES, labels=_AGE_LABELS, right=True)
    by_band = age_band.value_counts().reindex(_AGE_LABELS).fillna(0).astype(int)

    out = pd.DataFrame({
        "loan_age_band": _AGE_LABELS,
        "chargeoffs": by_band.values,
    })
    out["pct_of_chargeoffs"] = (out["chargeoffs"] / max(total_defaults, 1)).round(4)
    out["cumulative_pct_of_chargeoffs"] = out["pct_of_chargeoffs"].cumsum().round(4)
    # Charge-offs at this age as a share of the whole seasoned book.
    out["pct_of_portfolio"] = (out["chargeoffs"] / max(total_loans, 1)).round(4)

    _log.info(
        "Loan-age transition view: %d charge-offs across %d seasoned loans",
        total_defaults, total_loans,
    )
    return out
