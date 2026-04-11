from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RISK_GRADE_ORDER, SICR_THRESHOLDS


def _grade_distance(current: str, origination: str) -> int:
    """Number of notches between origination and current risk grade."""
    order = RISK_GRADE_ORDER
    if current not in order or origination not in order:
        return 0
    return order.index(current) - order.index(origination)


def check_sicr_triggers(
    df: pd.DataFrame,
    thresholds: dict | None = None,
) -> pd.DataFrame:
    """Add boolean columns for each SICR trigger.

    Triggers evaluated:
    - sicr_dpd: arrears >= 30 days
    - sicr_pd_increase: PD increased >= 2x origination PD (plus absolute floor)
    - sicr_grade_downgrade: risk grade worsened by >= 2 notches
    - sicr_watchlist: facility is on watchlist
    - sicr_default: facility is in default (arrears >= 90 or default_flag)
    """
    t = thresholds or SICR_THRESHOLDS
    out = df.copy()

    out["sicr_dpd"] = out["arrears_days"] >= t["dpd_stage2"]

    if "origination_pd" in out.columns:
        pd_ratio = np.where(out["origination_pd"] > 0, out["pd_final"] / out["origination_pd"], 1.0)
        pd_abs_increase = out["pd_final"] - out["origination_pd"]
        out["sicr_pd_increase"] = (pd_ratio >= t["pd_increase_relative"]) & (pd_abs_increase >= t["pd_increase_absolute"])
    else:
        out["sicr_pd_increase"] = False

    if "origination_risk_grade" in out.columns:
        out["grade_notch_change"] = [
            _grade_distance(c, o)
            for c, o in zip(out["internal_risk_grade"], out["origination_risk_grade"], strict=False)
        ]
        out["sicr_grade_downgrade"] = out["grade_notch_change"] >= t["grade_downgrade_notches"]
    else:
        out["sicr_grade_downgrade"] = False

    out["sicr_watchlist"] = out.get("watchlist_flag", pd.Series(0, index=out.index)).astype(bool)

    out["sicr_default"] = (
        (out["arrears_days"] >= t["dpd_stage3"])
        | (out.get("default_flag", pd.Series(0, index=out.index)).astype(bool))
    )

    return out


def classify_stage(
    df: pd.DataFrame,
    thresholds: dict | None = None,
) -> pd.DataFrame:
    """Assign AASB 9 stage (1, 2, or 3) based on SICR triggers.

    Stage 3: Default (arrears >= 90 DPD or default_flag)
    Stage 2: SICR triggered (any of: DPD >= 30, PD increase, grade downgrade, watchlist)
    Stage 1: Performing — no SICR triggers
    """
    out = check_sicr_triggers(df, thresholds)

    out["aasb9_stage"] = 1

    stage2_mask = (
        out["sicr_dpd"]
        | out["sicr_pd_increase"]
        | out["sicr_grade_downgrade"]
        | out["sicr_watchlist"]
    )
    out.loc[stage2_mask, "aasb9_stage"] = 2
    out.loc[out["sicr_default"], "aasb9_stage"] = 3

    return out


def summarise_staging(df: pd.DataFrame) -> pd.DataFrame:
    """Count and EAD by AASB 9 stage."""
    records: list[dict] = []
    total_ead = float(df["ead"].sum())
    for stage, group in df.groupby("aasb9_stage", sort=True):
        stage_ead = float(group["ead"].sum())
        records.append({
            "aasb9_stage": int(stage),
            "facility_count": len(group),
            "total_ead": round(stage_ead, 2),
            "ead_share": round(stage_ead / max(total_ead, 1), 4),
            "avg_pd": round(float(group["pd_final"].mean()), 4),
            "avg_lgd": round(float(group["lgd_final"].mean()), 4),
        })
    return pd.DataFrame.from_records(records)
