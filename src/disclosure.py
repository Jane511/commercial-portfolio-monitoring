from __future__ import annotations

import pandas as pd


def generate_stage_movement_table(
    current_df: pd.DataFrame,
    prior_df: pd.DataFrame,
) -> pd.DataFrame:
    """APS 330 Stage movement table: opening → transfers → closing balance.

    Shows ECL movement between stages from prior period to current period,
    formatted for regulatory disclosure.
    """
    ecl_col_current = "ecl_probability_weighted" if "ecl_probability_weighted" in current_df.columns else "ecl_scenario"
    ecl_col_prior = "ecl_probability_weighted" if "ecl_probability_weighted" in prior_df.columns else "ecl_scenario"

    # If prior doesn't have ECL, estimate from simple EL
    if ecl_col_prior not in prior_df.columns:
        prior_df = prior_df.copy()
        prior_df[ecl_col_prior] = prior_df["pd_final"] * prior_df["lgd_final"] * prior_df["ead"]

    records: list[dict] = []
    for stage in [1, 2, 3]:
        prior_stage = prior_df[prior_df["aasb9_stage"] == stage]
        current_stage = current_df[current_df["aasb9_stage"] == stage]

        opening_ecl = float(prior_stage[ecl_col_prior].sum())
        closing_ecl = float(current_stage[ecl_col_current].sum())

        # Transfers: facilities that moved into this stage
        merged = prior_df[["facility_id", "aasb9_stage"]].merge(
            current_df[["facility_id", "aasb9_stage", ecl_col_current]],
            on="facility_id",
            how="inner",
            suffixes=("_prior", "_current"),
        )
        transfers_in = merged[
            (merged["aasb9_stage_current"] == stage) & (merged["aasb9_stage_prior"] != stage)
        ]
        transfers_out = merged[
            (merged["aasb9_stage_prior"] == stage) & (merged["aasb9_stage_current"] != stage)
        ]

        records.append({
            "stage": f"Stage {stage}",
            "opening_ecl": round(opening_ecl, 2),
            "transfers_in": round(float(transfers_in[ecl_col_current].sum()), 2),
            "transfers_out": round(-float(transfers_out[ecl_col_current].sum()), 2),
            "net_remeasurement": round(closing_ecl - opening_ecl - float(transfers_in[ecl_col_current].sum()) + float(transfers_out[ecl_col_current].sum()), 2),
            "closing_ecl": round(closing_ecl, 2),
        })

    # Total row
    total = {
        "stage": "Total",
        "opening_ecl": round(sum(r["opening_ecl"] for r in records), 2),
        "transfers_in": 0.0,
        "transfers_out": 0.0,
        "net_remeasurement": round(sum(r["net_remeasurement"] for r in records), 2),
        "closing_ecl": round(sum(r["closing_ecl"] for r in records), 2),
    }
    records.append(total)

    return pd.DataFrame.from_records(records)


def generate_credit_quality_table(df: pd.DataFrame) -> pd.DataFrame:
    """APS 330 Credit quality table: exposure by internal rating and stage.

    Formatted for Table 11-style disclosure showing EAD and ECL
    cross-tabulated by risk grade and AASB 9 stage.
    """
    ecl_col = "ecl_probability_weighted" if "ecl_probability_weighted" in df.columns else "ecl_scenario"

    records: list[dict] = []
    for grade, grade_group in df.groupby("internal_risk_grade", sort=True):
        entry = {"internal_risk_grade": grade}
        for stage in [1, 2, 3]:
            stage_group = grade_group[grade_group["aasb9_stage"] == stage]
            entry[f"stage{stage}_count"] = len(stage_group)
            entry[f"stage{stage}_ead"] = round(float(stage_group["ead"].sum()), 2)
            entry[f"stage{stage}_ecl"] = round(float(stage_group[ecl_col].sum()), 2)

        entry["total_count"] = len(grade_group)
        entry["total_ead"] = round(float(grade_group["ead"].sum()), 2)
        entry["total_ecl"] = round(float(grade_group[ecl_col].sum()), 2)
        entry["coverage_ratio"] = round(
            entry["total_ecl"] / max(entry["total_ead"], 1), 6
        )
        records.append(entry)

    return pd.DataFrame.from_records(records)
