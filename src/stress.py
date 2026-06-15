"""Stress scenario that feeds the risk-appetite limits (CML-5).

APS 220 para 73 / APG 220 para 76 — stress testing should connect to the limit
framework, not sit beside it. This module runs one simple, data-grounded
scenario:

  1. Derive a **crisis multiplier** from the financial-crisis cohorts the data
     already contains (2006-08 charged off well above the book average).
  2. Apply it to the *current* portfolio charge-off rate to get a stressed rate
     and the implied additional charge-off exposure ($).
  3. Re-test the stressed rate against the CML-2 charge-off-rate appetite limit
     and report whether the stress **breaches appetite** — which would trigger
     that limit's breach action (tighter origination / pricing).

The output is deliberately a small table: baseline vs stressed value, each with
its RAG, so the read-across to the dashboard is immediate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import risk_appetite as ra
from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)

_EXPOSURE = "grossapproval"


def crisis_multiplier(base: pd.DataFrame, config: dict | None = None) -> dict:
    """Charge-off multiplier implied by the crisis cohorts vs the book average.

    Uses fully-seasoned loans only (so both rates reflect near-final outcomes).
    Returns the baseline rate, the crisis-cohort rate and their ratio.
    """
    cfg = config or load_config()
    crisis_vintages = set(cfg["stress"]["crisis_vintages"])

    seasoned = base[base["fully_seasoned"]]
    baseline = float(seasoned["is_default"].mean()) if len(seasoned) else float("nan")

    crisis = seasoned[seasoned["vintage"].isin(crisis_vintages)]
    crisis_rate = float(crisis["is_default"].mean()) if len(crisis) else float("nan")

    multiplier = (crisis_rate / baseline) if baseline and baseline > 0 else float("nan")
    return {
        "crisis_vintages": sorted(crisis_vintages),
        "baseline_chargeoff_rate": round(baseline, 4),
        "crisis_chargeoff_rate": round(crisis_rate, 4),
        "multiplier": round(multiplier, 2) if pd.notna(multiplier) else float("nan"),
    }


def stress_scenario(base: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Apply the crisis multiplier to the book and re-test the charge-off limit.

    Returns a one/two-row scenario table: the baseline charge-off rate and its
    RAG vs the appetite limit, then the stressed rate and its RAG, plus the
    implied additional charge-off exposure ($) and whether appetite is breached.
    """
    cfg = config or load_config()
    mult = crisis_multiplier(base, config=cfg)

    # Look up the charge-off-rate appetite limit (amber/red bounds).
    limit_id = cfg["stress"].get("chargeoff_limit_id", "portfolio_chargeoff_rate")
    limit = next((l for l in cfg["risk_appetite"]["limits"] if l["id"] == limit_id), None)
    if limit is None:
        raise KeyError(f"stress.chargeoff_limit_id '{limit_id}' not in risk_appetite.limits")
    amber, red, direction = float(limit["amber"]), float(limit["red"]), limit.get("direction", "upper")

    baseline_rate = mult["baseline_chargeoff_rate"]
    multiplier = mult["multiplier"]
    stressed_rate = round(baseline_rate * multiplier, 4) if pd.notna(multiplier) else float("nan")

    total_exposure = float(base[_EXPOSURE].sum())
    baseline_co_dollars = baseline_rate * total_exposure
    stressed_co_dollars = stressed_rate * total_exposure if pd.notna(stressed_rate) else float("nan")
    additional_dollars = (stressed_co_dollars - baseline_co_dollars
                          if pd.notna(stressed_rate) else float("nan"))

    rows = [
        {
            "scenario": "Baseline (current book)",
            "chargeoff_rate": baseline_rate,
            "rag_vs_limit": ra._rag(baseline_rate, amber, red, direction),
            "implied_chargeoff_exposure": round(baseline_co_dollars, 0),
            "additional_vs_baseline": 0.0,
        },
        {
            "scenario": f"Crisis stress ({multiplier:.2f}x, {mult['crisis_vintages']})",
            "chargeoff_rate": stressed_rate,
            "rag_vs_limit": ra._rag(stressed_rate, amber, red, direction),
            "implied_chargeoff_exposure": round(stressed_co_dollars, 0) if pd.notna(stressed_co_dollars) else np.nan,
            "additional_vs_baseline": round(additional_dollars, 0) if pd.notna(additional_dollars) else np.nan,
        },
    ]
    out = pd.DataFrame(rows)
    out["limit_amber"] = amber
    out["limit_red"] = red
    out["breaches_appetite"] = out["rag_vs_limit"].isin(["AMBER", "RED"])

    _log.info(
        "Stress scenario: baseline %.2f%% (%s) -> stressed %.2f%% (%s), "
        "+$%.0f charge-off exposure",
        baseline_rate * 100, rows[0]["rag_vs_limit"],
        (stressed_rate * 100) if pd.notna(stressed_rate) else float("nan"),
        rows[1]["rag_vs_limit"], additional_dollars if pd.notna(additional_dollars) else float("nan"),
    )
    return out
