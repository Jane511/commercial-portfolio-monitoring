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

from . import credit_parameters as cp
from . import risk_appetite as ra
from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)

_EXPOSURE = "grossapproval"


def _limit(cfg: dict, limit_id: str) -> dict:
    """Return the risk-appetite limit dict with id == *limit_id* (or raise)."""
    limit = next((l for l in cfg["risk_appetite"]["limits"] if l["id"] == limit_id), None)
    if limit is None:
        raise KeyError(f"stress limit id '{limit_id}' not in risk_appetite.limits")
    return limit


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
    """Run the stress ladder and re-test the charge-off AND dollar-EL limits.

    Four scenarios (gap review G18/G19), each tested against TWO appetite limits:

      * **Baseline** — current seasoned book.
      * **Adverse** — historical crisis replay: the 2006-08 charge-off multiplier
        applied to the baseline.
      * **Severe** — the single worst observed vintage's charge-off rate.
      * **Hypothetical overlay** — a forward management severity beyond the
        historical replay (``stress.hypothetical_overlay_multiplier`` on severe).

    Each row carries the charge-off rate and its RAG vs the charge-off-rate
    limit, the dollar EL rate and its RAG vs the EL-rate limit (so stressed
    LGD/EAD severity is bounded by appetite), the implied charge-off exposure ($)
    and the additional ($) vs baseline. ``breaches_appetite`` is true if either
    limit is amber/red.
    """
    cfg = config or load_config()
    mult = crisis_multiplier(base, config=cfg)

    # Two appetite limits the stress is read against.
    co_limit = _limit(cfg, cfg["stress"].get("chargeoff_limit_id", "portfolio_chargeoff_rate"))
    el_limit = _limit(cfg, cfg["stress"].get("el_limit_id", "el_rate"))
    co_amber, co_red = float(co_limit["amber"]), float(co_limit["red"])
    el_amber, el_red = float(el_limit["amber"]), float(el_limit["red"])

    # EL-rate ladder, taken from the parameter stress so §9 and §10d reconcile.
    cps = cp.credit_risk_parameters_stress(base, config=cfg).set_index("metric_key")
    el_ttc = float(cps.loc["el_rate", "through_the_cycle"])
    el_adverse = float(cps.loc["el_rate", "adverse_downturn"])
    el_severe = float(cps.loc["el_rate", "severe"])

    # Charge-off-rate ladder.
    baseline_rate = mult["baseline_chargeoff_rate"]
    multiplier = mult["multiplier"]
    adverse_rate = round(baseline_rate * multiplier, 4) if pd.notna(multiplier) else float("nan")
    seasoned = base[base["fully_seasoned"]]
    severe_rate = round(float(seasoned.groupby("vintage", observed=True)["is_default"].mean().max()), 4) \
        if len(seasoned) else float("nan")
    overlay = float(cfg["stress"].get("hypothetical_overlay_multiplier", 1.25))
    hypo_rate = round(severe_rate * overlay, 4) if pd.notna(severe_rate) else float("nan")
    el_hypo = round(el_severe * overlay, 4)

    total_exposure = float(base[_EXPOSURE].sum())
    baseline_co_dollars = baseline_rate * total_exposure

    specs = [
        ("Baseline (current book)", baseline_rate, el_ttc),
        (f"Adverse — historical crisis ({multiplier:.2f}x, {mult['crisis_vintages']})",
         adverse_rate, el_adverse),
        (f"Severe — worst vintage ({int(cps['severe_vintage'].iloc[0])})", severe_rate, el_severe),
        (f"Hypothetical overlay ({overlay:.2f}x severe)", hypo_rate, el_hypo),
    ]
    rows = []
    for name, co_rate, el_rate in specs:
        co_dollars = co_rate * total_exposure if pd.notna(co_rate) else float("nan")
        rag_co = ra._rag(co_rate, co_amber, co_red, "upper")
        rag_el = ra._rag(el_rate, el_amber, el_red, "upper")
        rows.append({
            "scenario": name,
            "chargeoff_rate": co_rate,
            "rag_vs_chargeoff_limit": rag_co,
            "el_rate": el_rate,
            "rag_vs_el_limit": rag_el,
            "implied_chargeoff_exposure": round(co_dollars, 0) if pd.notna(co_dollars) else np.nan,
            "additional_vs_baseline": round(co_dollars - baseline_co_dollars, 0) if pd.notna(co_dollars) else np.nan,
            "breaches_appetite": rag_co in ("AMBER", "RED") or rag_el in ("AMBER", "RED"),
        })

    out = pd.DataFrame(rows)
    out["chargeoff_limit_amber"] = co_amber
    out["chargeoff_limit_red"] = co_red
    out["el_limit_amber"] = el_amber
    out["el_limit_red"] = el_red

    _log.info(
        "Stress ladder: baseline CO %.1f%%/EL %.1f%% -> adverse %.1f%%/%.1f%% -> "
        "severe %.1f%%/%.1f%% -> hypothetical %.1f%%/%.1f%%",
        baseline_rate * 100, el_ttc * 100, adverse_rate * 100, el_adverse * 100,
        severe_rate * 100, el_severe * 100, hypo_rate * 100, el_hypo * 100,
    )
    return out
