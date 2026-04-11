from __future__ import annotations

import numpy as np
import pandas as pd

from .config import EARLY_WARNING_THRESHOLDS


def flag_early_warnings(
    df: pd.DataFrame,
    thresholds: dict | None = None,
) -> pd.DataFrame:
    """Add early warning signal flags to the facility dataset.

    Signals detected:
    - ew_dscr_weak: DSCR < 1.25 (approaching covenant breach)
    - ew_dscr_critical: DSCR < 1.00 (cash flow insufficient for debt service)
    - ew_arrears_trending: Arrears > 0 but < 30 DPD (not yet Stage 2)
    - ew_grade_on_watch: Watchlist flag set but not yet Stage 2/3
    - ew_pd_deterioration: PD increased >= 50% from origination
    """
    t = thresholds or EARLY_WARNING_THRESHOLDS
    out = df.copy()

    out["ew_dscr_weak"] = False
    if "dscr" in out.columns:
        out["ew_dscr_weak"] = out["dscr"] < t["dscr_weak"]
        out["ew_dscr_critical"] = out["dscr"] < t["dscr_critical"]
    else:
        out["ew_dscr_critical"] = False

    out["ew_arrears_trending"] = (
        (out["arrears_days"] > 0) & (out["arrears_days"] < t.get("arrears_trending_days", 30))
    )

    out["ew_grade_on_watch"] = (
        out.get("watchlist_flag", pd.Series(0, index=out.index)).astype(bool)
        & (out.get("aasb9_stage", pd.Series(1, index=out.index)) == 1)
    )

    if "origination_pd" in out.columns:
        pd_increase = np.where(
            out["origination_pd"] > 0,
            (out["pd_final"] - out["origination_pd"]) / out["origination_pd"],
            0.0,
        )
        out["ew_pd_deterioration"] = pd_increase >= t["pd_increase_pct"]
    else:
        out["ew_pd_deterioration"] = False

    ew_cols = [c for c in out.columns if c.startswith("ew_")]
    out["ew_signal_count"] = out[ew_cols].sum(axis=1).astype(int)

    return out


def summarise_early_warnings(df: pd.DataFrame) -> pd.DataFrame:
    """Count of each early warning signal type."""
    ew_cols = [c for c in df.columns if c.startswith("ew_") and c != "ew_signal_count"]
    records: list[dict] = []
    for col in ew_cols:
        flagged = df[df[col] == True]
        records.append({
            "signal": col.replace("ew_", ""),
            "facility_count": int(flagged[col].sum()),
            "total_ead": round(float(flagged["ead"].sum()), 2),
            "avg_pd": round(float(flagged["pd_final"].mean()), 4) if len(flagged) > 0 else 0.0,
        })

    total_any = df[df["ew_signal_count"] > 0]
    records.append({
        "signal": "any_signal",
        "facility_count": len(total_any),
        "total_ead": round(float(total_any["ead"].sum()), 2),
        "avg_pd": round(float(total_any["pd_final"].mean()), 4) if len(total_any) > 0 else 0.0,
    })

    return pd.DataFrame.from_records(records)
