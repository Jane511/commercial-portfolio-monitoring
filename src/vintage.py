"""Vintage cohort charge-off curves.

For each approval-year cohort, the cumulative charge-off rate at months-on-book
(MOB) checkpoint *m* is:

    (loans in cohort charged off within m months of approval) / (cohort size)

using months_to_chargeoff = ChargeOffDate - ApprovalDate. A cohort is only
observable out to the time elapsed between its loans being approved and the
data as-of date; checkpoints beyond that window are left blank (NaN) so an
immature cohort is never shown as having a deceptively low charge-off rate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)

_DAYS_PER_MONTH = 30.44


def _infer_as_of(df: pd.DataFrame) -> pd.Timestamp:
    """Latest observed date in the data — the effective reporting cut-off."""
    candidates = [
        df["chargeoffdate"].max(),
        df["paidinfulldate"].max(),
        df["approvaldate"].max(),
    ]
    return max(c for c in candidates if pd.notna(c))


def compute_vintage_curves(
    df: pd.DataFrame,
    as_of: pd.Timestamp | None = None,
    config: dict | None = None,
) -> pd.DataFrame:
    """Cumulative charge-off rate by vintage (rows) and MOB checkpoint (cols).

    Returns a frame indexed by approval-year vintage with one column per MOB
    checkpoint (``MOB_012`` etc.). Cells beyond a cohort's observable horizon
    are NaN.
    """
    cfg = config or load_config()
    mob_grid = cfg["vintage"]["mob_grid"]
    as_of = as_of or _infer_as_of(df)
    _log.info("Vintage curves: as-of date %s, MOB grid %s", as_of.date(), mob_grid)

    rows = {}
    for vintage, cohort in df.groupby("vintage", observed=True):
        size = len(cohort)
        if size == 0:
            continue
        # Conservative observable horizon: the most recently approved loan in
        # the cohort has the least elapsed time; require every loan observed.
        latest_approval = cohort["approvaldate"].max()
        horizon_months = (as_of - latest_approval).days / _DAYS_PER_MONTH

        months = cohort["months_to_chargeoff"]
        curve = {}
        for m in mob_grid:
            if m > horizon_months:
                curve[f"MOB_{m:03d}"] = np.nan
            else:
                charged = int((months <= m).sum())  # NaN (non-defaults) excluded
                curve[f"MOB_{m:03d}"] = round(charged / size, 4)
        rows[int(vintage)] = curve

    out = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    out.index.name = "vintage"
    return out
