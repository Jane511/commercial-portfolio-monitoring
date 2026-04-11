from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import weighted_average


def calculate_ecl(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate AASB 9 Expected Credit Loss per facility per scenario.

    Stage 1: ECL = PD_12m × LGD × EAD          (12-month ECL)
    Stage 2: ECL = Lifetime_PD × LGD × EAD     (lifetime ECL)
    Stage 3: ECL = 1.0 × LGD × EAD             (credit-impaired, PD = 1)

    If the DataFrame contains a 'scenario' column, PD/LGD scenario adjustments
    are used; otherwise, the base PD/LGD values are used.
    """
    out = df.copy()

    pd_col = "pd_scenario" if "pd_scenario" in out.columns else "lifetime_pd"
    lgd_col = "lgd_scenario" if "lgd_scenario" in out.columns else "lgd_final"

    out["ecl_scenario"] = np.where(
        out["aasb9_stage"] == 3,
        1.0 * out[lgd_col] * out["ead"],
        out[pd_col] * out[lgd_col] * out["ead"],
    )
    out["ecl_scenario"] = out["ecl_scenario"].round(2)

    return out


def summarise_ecl_by_stage(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate ECL by AASB 9 stage."""
    records: list[dict] = []
    total_ead = float(df["ead"].sum())
    total_ecl = float(df["ecl_probability_weighted"].sum()) if "ecl_probability_weighted" in df.columns else float(df["ecl_scenario"].sum())

    ecl_col = "ecl_probability_weighted" if "ecl_probability_weighted" in df.columns else "ecl_scenario"

    for stage, group in df.groupby("aasb9_stage", sort=True):
        stage_ead = float(group["ead"].sum())
        stage_ecl = float(group[ecl_col].sum())
        records.append({
            "aasb9_stage": int(stage),
            "facility_count": len(group),
            "total_ead": round(stage_ead, 2),
            "ead_share": round(stage_ead / max(total_ead, 1), 4),
            "total_ecl": round(stage_ecl, 2),
            "ecl_share": round(stage_ecl / max(total_ecl, 1), 4),
            "coverage_ratio": round(stage_ecl / max(stage_ead, 1), 6),
        })
    return pd.DataFrame.from_records(records)


def summarise_ecl_by_segment(
    df: pd.DataFrame,
    group_fields: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate ECL by segment (default: product_type, industry)."""
    fields = group_fields or ["product_type"]
    ecl_col = "ecl_probability_weighted" if "ecl_probability_weighted" in df.columns else "ecl_scenario"

    records: list[dict] = []
    for keys, group in df.groupby(fields, sort=True):
        if isinstance(keys, str):
            keys = (keys,)
        entry: dict = dict(zip(fields, keys, strict=False))
        stage_ead = float(group["ead"].sum())
        stage_ecl = float(group[ecl_col].sum())
        entry.update({
            "facility_count": len(group),
            "total_ead": round(stage_ead, 2),
            "total_ecl": round(stage_ecl, 2),
            "coverage_ratio": round(stage_ecl / max(stage_ead, 1), 6),
            "avg_pd": round(float(group["pd_final"].mean()), 4),
            "avg_lgd": round(float(group["lgd_final"].mean()), 4),
            "stage1_count": int((group["aasb9_stage"] == 1).sum()),
            "stage2_count": int((group["aasb9_stage"] == 2).sum()),
            "stage3_count": int((group["aasb9_stage"] == 3).sum()),
        })
        records.append(entry)
    return pd.DataFrame.from_records(records)
