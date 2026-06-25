"""Problem-exposure / early-warning layer (CML-1).

Default in this build is **charge-off only** (``LoanStatus == CHGOFF``) — a
*realised, lagging* write-off point. But the SBA data also carries pre-charge-off
problem statuses that are precisely the forward-looking signals APS 220 para 79
and APG 220 para 66 expect a monitor to act on early:

    DELINQ  — delinquent
    PSTDUE  — past due
    LIQUID  — in liquidation (a near-certain *future* charge-off — a leading signal)

This module surfaces that pipeline: how much exposure is sitting in a problem
state *before* it becomes a charge-off, overall and by segment. It deliberately
does **not** reclassify these loans as default — it reports them as a separate
early-warning layer that feeds the risk-appetite dashboard.

NOTE on the reference default: APS 220's reference default is 90+ days past due
or unlikely-to-pay. SBA charge-off sits *later* than that on the credit
timeline, so the charge-off rate understates how many loans have already
breached the reference-default point. The problem-exposure layer is the closest
SBA-feasible proxy for that earlier, leading definition.
"""
from __future__ import annotations

import pandas as pd

from .config import LOAN_STATUS_LABELS, load_config
from .logger import get_logger

_log = get_logger(__name__)

_EXPOSURE = "grossapproval"


def _status_signal(status: str) -> str:
    """Forward-looking signal label for a problem-exposure status."""
    if status == "LIQUID":
        return "Leading — near-certain future charge-off (in liquidation)"
    if status == "PURCH(NOT C/O)":
        return "Non-performing — SBA guaranty purchased (effective default, not yet written off)"
    return "Leading — pre-charge-off problem exposure"


def problem_exposure_overview(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Portfolio-level problem-exposure pipeline, one row per problem status.

    Columns: status code, plain-English label, loan count, exposure ($), and
    that status' share of the whole funded book (count and $). ``LIQUID`` is
    flagged as a leading (near-certain future charge-off) signal.
    """
    cfg = config or load_config()
    problem_statuses = list(cfg["universe"].get("problem_exposure_statuses", []))

    total_count = len(df)
    total_exposure = float(df[_EXPOSURE].sum())

    rows = []
    for status in problem_statuses:
        sel = df["loanstatus"] == status
        count = int(sel.sum())
        exposure = float(df.loc[sel, _EXPOSURE].sum())
        rows.append({
            "status": status,
            "status_label": LOAN_STATUS_LABELS.get(status, status),
            "loan_count": count,
            "exposure": exposure,
            "count_share": round(count / total_count, 6) if total_count else 0.0,
            "exposure_share": round(exposure / total_exposure, 6) if total_exposure else 0.0,
            "signal": _status_signal(status),
        })

    # Total problem-exposure pipeline row.
    sel_all = df["is_problem_exposure"]
    rows.append({
        "status": "ALL_PROBLEM",
        "status_label": "Total problem-exposure pipeline",
        "loan_count": int(sel_all.sum()),
        "exposure": float(df.loc[sel_all, _EXPOSURE].sum()),
        "count_share": round(float(sel_all.mean()), 6) if total_count else 0.0,
        "exposure_share": round(float(df.loc[sel_all, _EXPOSURE].sum()) / total_exposure, 6)
                          if total_exposure else 0.0,
        "signal": "Leading — pre-charge-off pipeline (vs lagging charge-off)",
    })

    out = pd.DataFrame(rows)
    _log.info(
        "Problem-exposure overview: %d loans in pipeline (%.3f%% of book) across %s",
        int(sel_all.sum()), float(sel_all.mean()) * 100, problem_statuses,
    )
    return out


def problem_exposure_by(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Problem-exposure rate by a segment dimension (industry / vintage / size).

    For each segment: loans, problem-exposure count and exposure, the segment's
    problem-exposure rate, and — for context — its realised charge-off rate.
    Sorted worst-first by problem-exposure rate. Segments are ordered so the
    forward (problem) signal sits next to the lagging (charge-off) outcome.
    """
    col = {"industry": "naics_sector", "vintage": "vintage", "size": "size_band"}.get(
        dimension, dimension
    )
    work = df.copy()
    work["_problem_exposure_amt"] = work[_EXPOSURE].where(work["is_problem_exposure"], 0.0)
    grouped = work.groupby(col, dropna=False, observed=True).agg(
        loan_count=(_EXPOSURE, "size"),
        problem_count=("is_problem_exposure", "sum"),
        problem_exposure=("_problem_exposure_amt", "sum"),
        defaults=("is_default", "sum"),
    )
    grouped["problem_rate"] = (grouped["problem_count"] / grouped["loan_count"]).round(4)
    grouped["chargeoff_rate"] = (grouped["defaults"] / grouped["loan_count"]).round(4)
    out = grouped.reset_index().rename(columns={col: dimension})
    return out.sort_values("problem_rate", ascending=False).reset_index(drop=True)
