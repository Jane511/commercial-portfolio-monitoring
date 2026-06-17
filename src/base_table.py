"""Build the monitoring base table: one row per funded loan + derived fields.

Derived fields: vintage (approval-year cohort), default flag, size band, and
loan age in months at the point of charge-off (ChargeOffDate - ApprovalDate),
which feeds the vintage cohort curves and the loan-age transition view.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import EXPORT_SUBPROGRAMS, RE_TERM_MONTHS_MIN, load_config
from .logger import get_logger

_log = get_logger(__name__)


def _size_band(amounts: pd.Series, edges: list[float], labels: list[str]) -> pd.Series:
    """Bucket gross-approval amounts into labelled size bands.

    ``edges`` are the (n-1) upper bounds; ``labels`` has n entries, the last of
    which is the open-ended top band.
    """
    bins = [-np.inf, *edges, np.inf]
    return pd.cut(amounts, bins=bins, labels=labels, right=True)


def build_base_table(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Return the monitoring base table from the cleaned loan frame."""
    cfg = config or load_config()
    default_statuses = set(cfg["universe"]["default_statuses"])
    problem_statuses = set(cfg["universe"].get("problem_exposure_statuses", []))
    seasoned_max_fy = int(cfg["universe"]["fully_seasoned_max_fy"])
    bands = cfg["size_bands"]

    out = df.copy()

    # Vintage = approval fiscal-year cohort.
    out["vintage"] = out["approvalfy"].astype("Int64")

    # Default flag (charge-off) — the realised, *lagging* loss point.
    out["is_default"] = out["loanstatus"].isin(default_statuses)

    # Problem-exposure flag (DELINQ / PSTDUE / LIQUID) — the *leading*,
    # pre-charge-off early-warning pipeline (APS 220 para 79).
    out["is_problem_exposure"] = out["loanstatus"].isin(problem_statuses)

    # Size band on gross approval.
    out["size_band"] = _size_band(out["grossapproval"], bands["edges"], bands["labels"])

    # Product taxonomy. SBA 7(a) is small-business lending throughout — there is
    # NO residential or labelled commercial-property mortgage product here. We
    # derive an intuitive use-of-proceeds *facility type* from the fields that
    # are present. Defensive on column presence so older extracts / test
    # fixtures without these fields still run.
    for col in ("subprogram", "revolverstatus", "collateralind"):
        if col not in out.columns:
            out[col] = pd.NA

    _bool = {"TRUE": True, "FALSE": False, "T": True, "F": False,
             "1": True, "0": False, "YES": True, "NO": False}
    rev = out["revolverstatus"].astype("string").str.strip().str.upper().map(_bool)
    sec = out["collateralind"].astype("string").str.strip().str.upper().map(_bool)
    out["loan_structure"] = rev.map(
        {True: "Revolving line of credit", False: "Term loan"}).fillna("Unknown")
    out["collateral_status"] = sec.map(
        {True: "Secured", False: "Unsecured"}).fillna("Unknown")

    # Facility-type product. Precedence: trade/export first (a distinct product),
    # then revolving working-capital lines, then long-dated term loans (only
    # real estate carries SBA maturities beyond ~15y → commercial-property
    # PROXY), else a general SME term loan.
    sub = out["subprogram"].astype("string").str.strip()
    term = pd.to_numeric(out["terminmonths"], errors="coerce")
    out["product_type"] = np.select(
        [sub.isin(EXPORT_SUBPROGRAMS).to_numpy(dtype=bool),
         rev.eq(True).to_numpy(dtype=bool),
         (term > RE_TERM_MONTHS_MIN).to_numpy(dtype=bool)],
        ["Trade & export finance",
         "Working-capital line (revolving)",
         "Commercial property / real-estate term loan (proxy)"],
        default="General SME term loan",
    )

    # Loan age (months) at charge-off — only meaningful for charged-off loans
    # that have both an approval and a charge-off date.
    delta_days = (out["chargeoffdate"] - out["approvaldate"]).dt.days
    months = delta_days / 30.44  # average days per month
    # Guard against rare negative/zero deltas from data-entry noise.
    out["months_to_chargeoff"] = months.where(out["is_default"] & (months > 0)).round(1)

    # Seasoning flag — recent vintages under-report ultimate charge-offs.
    out["fully_seasoned"] = out["vintage"] <= seasoned_max_fy

    _log.info(
        "Base table built: %d loans, %d vintages (%s-%s), %d defaults, "
        "%d problem exposures",
        len(out), out["vintage"].nunique(),
        int(out["vintage"].min()), int(out["vintage"].max()),
        int(out["is_default"].sum()), int(out["is_problem_exposure"].sum()),
    )
    return out
