"""Risk appetite & limit framework (CML-2) — the governance layer.

APS 220 para 20 (a risk appetite statement) and para 35 (concentration limits by
industry, geography and **single name / lender**). This module turns the
descriptive thresholds in ``config.yaml`` into an appetite framework: for each
limit it computes the live portfolio metric, compares it to an amber
(early-warning) and red (breach) bound, and attaches an owner, a breach action
and a review cycle.

The output table is the spine of the board RAG dashboard (CML-3) and is reused,
under stress, by the scenario in CML-5 (stress -> limit review -> action).

Limits covered:
  * industry concentration (HHI + top-industry share)
  * single-lender AND top-20-lender concentration (added per CML-2 — the build
    previously showed lender HHI only, with no single-name/top-N limit)
  * portfolio charge-off rate
  * a vintage-deterioration trigger (a young cohort's early-MOB charge-off
    running above its predecessors')
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import concentration as conc
from . import vintage as vint
from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)

_EXPOSURE = "grossapproval"


def vintage_early_mob_multiple(
    base: pd.DataFrame, config: dict | None = None
) -> tuple[float, dict]:
    """Leading vintage-deterioration metric.

    At the early-MOB reference checkpoint (default 24 months), compare the most
    recent cohort that is *observable* at that age to the median of its
    predecessors at the same age. A multiple > 1 means the young cohort is
    charging off faster than older cohorts did when they were equally young — a
    forward signal that lands well before the final charge-off rate does.

    Returns ``(multiple, detail)``; ``multiple`` is NaN when fewer than two
    cohorts are observable at the checkpoint.
    """
    cfg = config or load_config()
    ref = int(cfg["vintage"].get("early_mob_reference", 24))
    curves = vint.compute_vintage_curves(base, config=cfg)
    col = f"MOB_{ref:03d}"
    detail = {"reference_mob": ref}
    if curves.empty or col not in curves.columns:
        return float("nan"), detail

    series = curves[col].dropna()
    if series.shape[0] < 2:
        return float("nan"), detail

    latest = int(series.index.max())
    latest_val = float(series.loc[latest])
    predecessors = series.drop(latest)
    pred_median = float(predecessors.median())
    multiple = latest_val / pred_median if pred_median > 0 else float("nan")

    detail.update({
        "latest_vintage": latest,
        "latest_early_mob_rate": round(latest_val, 4),
        "predecessor_median_rate": round(pred_median, 4),
    })
    return (round(multiple, 2) if pred_median > 0 else float("nan")), detail


def _metric_values(base: pd.DataFrame, config: dict | None = None) -> dict[str, float]:
    """Compute every appetite-limit ``basis`` metric from the live book."""
    cfg = config or load_config()

    hhi = conc.hhi_summary(base).set_index("dimension")
    ind = conc.concentration_by(base, "industry")
    lenders = conc.concentration_by(base, "lender", top_n=20)

    seasoned = base[base["fully_seasoned"]]
    portfolio_co = float(seasoned["is_default"].mean()) if len(seasoned) else float("nan")

    vd_multiple, _ = vintage_early_mob_multiple(base, config=cfg)

    return {
        "hhi_industry": float(hhi.loc["industry", "hhi"]),
        "top_industry_share": float(ind.iloc[0]["exposure_share"]) if len(ind) else float("nan"),
        "top1_lender_share": float(lenders.iloc[0]["exposure_share"]) if len(lenders) else float("nan"),
        "top20_lender_share": round(float(lenders["exposure_share"].sum()), 4),
        "portfolio_chargeoff_rate": round(portfolio_co, 4),
        "vintage_early_mob_multiple": vd_multiple,
    }


def _rag(value: float, amber: float, red: float, direction: str) -> str:
    """Classify a metric into GREEN / AMBER / RED against its limit bounds."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    if direction == "lower":  # breach when value is low (e.g. coverage ratios)
        if value <= red:
            return "RED"
        if value <= amber:
            return "AMBER"
        return "GREEN"
    # default: upper — breach when value is high
    if value >= red:
        return "RED"
    if value >= amber:
        return "AMBER"
    return "GREEN"


def appetite_dashboard(base: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Risk-appetite limit table with live values and RAG status.

    One row per configured limit: metric, live value, amber/red thresholds, RAG
    status, owner, breach action and review cycle. ``utilisation`` expresses the
    value as a fraction of its red limit (for upper-direction limits) so limits
    on different scales can be compared at a glance.
    """
    cfg = config or load_config()
    ra = cfg["risk_appetite"]
    default_owner = ra.get("default_owner", "Head of Credit Risk")
    default_cycle = ra.get("default_review_cycle", "Quarterly")

    values = _metric_values(base, config=cfg)

    rows = []
    for lim in ra["limits"]:
        basis = lim["basis"]
        value = values.get(basis, float("nan"))
        direction = lim.get("direction", "upper")
        amber, red = float(lim["amber"]), float(lim["red"])
        rag = _rag(value, amber, red, direction)
        utilisation = (round(value / red, 3)
                       if direction == "upper" and red and pd.notna(value) else np.nan)
        rows.append({
            "id": lim["id"],
            "metric": lim["metric"],
            "basis": basis,
            "value": round(float(value), 4) if pd.notna(value) else np.nan,
            "amber": amber,
            "red": red,
            "direction": direction,
            "rag": rag,
            "utilisation_vs_red": utilisation,
            "owner": lim.get("owner", default_owner),
            "breach_action": lim["breach_action"],
            "review_cycle": lim.get("review_cycle", default_cycle),
        })

    out = pd.DataFrame(rows)
    breaches = out[out["rag"].isin(["AMBER", "RED"])]
    _log.info(
        "Appetite dashboard: %d limits, %d within appetite, %d amber/red",
        len(out), int((out["rag"] == "GREEN").sum()), len(breaches),
    )
    return out


def appetite_actions(dashboard: pd.DataFrame) -> pd.DataFrame:
    """Actions table for amber/red limits: action, owner, due (review cycle)."""
    flagged = dashboard[dashboard["rag"].isin(["AMBER", "RED"])].copy()
    if flagged.empty:
        return pd.DataFrame(columns=["metric", "rag", "action", "owner", "due"])
    out = flagged.rename(columns={
        "breach_action": "action", "review_cycle": "due",
    })[["metric", "rag", "action", "owner", "due"]]
    # Red items first, then amber.
    order = {"RED": 0, "AMBER": 1}
    out = out.assign(_o=out["rag"].map(order)).sort_values("_o").drop(columns="_o")
    return out.reset_index(drop=True)
