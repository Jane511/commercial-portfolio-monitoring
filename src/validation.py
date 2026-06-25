"""Predictiveness validation of the leading indicators (CML-6).

APG 113 para 140 element 3 (*performance* — is the metric actually predictive of
subsequent loss?) and APG 220 para 66 (forward-looking indicators must earn
their place). The monitor *labels* several metrics "leading"; this module
**tests** that claim empirically against the realised outcomes the SBA data
already holds (gap review G11/G20).

Method: across fully-seasoned approval-year cohorts, line up each leading
indicator measured *early* in a cohort's life against that cohort's *final*
realised charge-off rate, and measure the Spearman rank correlation. A leading
indicator that ranks cohorts the same way their eventual losses do (positive
rank correlation) is predictive; one that does not is not earning its place.

Indicators tested:
  * early-MOB charge-off rate (cumulative charge-off at the reference MOB, e.g.
    24 months) — the core forward signal behind CML-2's vintage-deterioration
    limit and CML-4's vintage-over-vintage view;
  * large-ticket origination share — a mix signal from CML-4;
  * top-sector origination share — a mix signal from CML-4.
"""
from __future__ import annotations

import pandas as pd

from . import chargeoff as co
from . import leading
from . import vintage as vint
from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)

# A |rank-correlation| at/above this is treated as a usable predictive signal.
_PREDICTIVE_THRESHOLD = 0.3


def cohort_leading_vs_final(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Per seasoned cohort: each early leading indicator vs the final loss rate.

    One row per fully-seasoned approval-year vintage with the early-MOB
    charge-off rate, the origination mix signals (large-ticket / top-sector
    share), and the cohort's final realised charge-off rate.
    """
    cfg = config or load_config()
    ref = int(cfg["vintage"].get("early_mob_reference", 24))

    # Early-MOB charge-off rate per vintage (observable at the reference age).
    curves = vint.compute_vintage_curves(df, config=cfg)
    col = f"MOB_{ref:03d}"
    early = (curves[col].rename("early_mob_chargeoff").reset_index()
             if col in curves.columns else
             pd.DataFrame(columns=["vintage", "early_mob_chargeoff"]))

    # Final realised charge-off rate per vintage.
    final = (co.chargeoff_by_vintage(df)[["vintage", "chargeoff_rate_count", "fully_seasoned"]]
             .rename(columns={"chargeoff_rate_count": "final_chargeoff_rate"}))

    # Origination mix signals per vintage.
    mix = leading.origination_trend(df, config=cfg)[
        ["vintage", "large_ticket_share", "top_sector_share"]]

    out = (final.merge(early, on="vintage", how="left")
                .merge(mix, on="vintage", how="left"))
    # Restrict to seasoned cohorts with an observable early-MOB reading.
    out = out[out["fully_seasoned"] & out["early_mob_chargeoff"].notna()].copy()
    out["reference_mob"] = ref
    return out.sort_values("vintage").reset_index(drop=True)


def leading_indicator_predictiveness(df: pd.DataFrame,
                                     config: dict | None = None) -> pd.DataFrame:
    """Spearman rank correlation of each leading indicator vs the final loss rate.

    Returns one row per indicator: the number of cohorts, the rank correlation
    with the final charge-off rate, and a verdict. A positive correlation at or
    above the predictive threshold confirms the indicator ranks cohorts the way
    their eventual losses do.
    """
    panel = cohort_leading_vs_final(df, config=config)
    indicators = [
        ("early_mob_chargeoff", "Early-MOB charge-off rate"),
        ("large_ticket_share", "Large-ticket origination share"),
        ("top_sector_share", "Top-sector origination share"),
    ]
    rows = []
    for key, label in indicators:
        n = int(panel[key].notna().sum())
        corr = (round(float(panel[key].corr(panel["final_chargeoff_rate"], method="spearman")), 3)
                if n >= 3 and panel[key].nunique() > 1 else float("nan"))
        if pd.isna(corr):
            verdict = "Insufficient data"
        elif corr >= _PREDICTIVE_THRESHOLD:
            verdict = "Predictive (confirmed leading)"
        elif corr <= -_PREDICTIVE_THRESHOLD:
            verdict = "Inverse — investigate"
        else:
            verdict = "Weak / not predictive"
        rows.append({
            "indicator": label,
            "cohorts": n,
            "spearman_vs_final_chargeoff": corr,
            "verdict": verdict,
        })
    out = pd.DataFrame(rows)
    _log.info(
        "Predictiveness: %s",
        "; ".join(f"{r['indicator']}={r['spearman_vs_final_chargeoff']} ({r['verdict']})"
                  for _, r in out.iterrows()),
    )
    return out
