from __future__ import annotations

import pandas as pd

from .config import RISK_GRADE_ORDER


def build_transition_matrix(
    current_df: pd.DataFrame,
    prior_df: pd.DataFrame,
    field: str = "internal_risk_grade",
) -> pd.DataFrame:
    """Construct a transition matrix showing migration percentages.

    Each cell (i, j) shows the proportion of facilities that were in
    state i at prior period and moved to state j at current period.
    """
    merged = prior_df[["facility_id", field]].merge(
        current_df[["facility_id", field]],
        on="facility_id",
        how="inner",
        suffixes=("_prior", "_current"),
    )

    prior_col = f"{field}_prior"
    current_col = f"{field}_current"

    # Build cross-tabulation
    ct = pd.crosstab(
        merged[prior_col],
        merged[current_col],
        margins=False,
        normalize="index",
    )

    # Ensure all categories are present
    if field == "internal_risk_grade":
        categories = RISK_GRADE_ORDER
    elif field == "aasb9_stage":
        categories = [1, 2, 3]
    else:
        categories = sorted(set(merged[prior_col].unique()) | set(merged[current_col].unique()))

    ct = ct.reindex(index=categories, columns=categories, fill_value=0.0)
    ct = ct.round(4)
    ct.index.name = f"{field}_from"
    ct.columns.name = f"{field}_to"

    return ct


def identify_downgrades(
    current_df: pd.DataFrame,
    prior_df: pd.DataFrame,
    field: str = "internal_risk_grade",
) -> pd.DataFrame:
    """Identify facilities that worsened between periods."""
    merged = prior_df[["facility_id", field]].merge(
        current_df[["facility_id", field, "product_type", "industry", "ead", "pd_final"]],
        on="facility_id",
        how="inner",
        suffixes=("_prior", "_current"),
    )

    if field == "internal_risk_grade":
        order_map = {g: i for i, g in enumerate(RISK_GRADE_ORDER)}
        merged["prior_rank"] = merged[f"{field}_prior"].map(order_map)
        merged["current_rank"] = merged[f"{field}_current"].map(order_map)
        downgrades = merged[merged["current_rank"] > merged["prior_rank"]].copy()
        downgrades["notches_down"] = downgrades["current_rank"] - downgrades["prior_rank"]
    elif field == "aasb9_stage":
        merged["prior_rank"] = merged[f"{field}_prior"].astype(int)
        merged["current_rank"] = merged[f"{field}_current"].astype(int)
        downgrades = merged[merged["current_rank"] > merged["prior_rank"]].copy()
        downgrades["notches_down"] = downgrades["current_rank"] - downgrades["prior_rank"]
    else:
        return pd.DataFrame()

    return downgrades.sort_values("notches_down", ascending=False).reset_index(drop=True)


def summarise_migration(transition_matrix: pd.DataFrame) -> dict:
    """Key statistics from the transition matrix."""
    diag = sum(transition_matrix.iloc[i, i] for i in range(min(transition_matrix.shape)))
    n = min(transition_matrix.shape)
    stability_ratio = diag / max(n, 1)

    upgrade_count = 0
    downgrade_count = 0
    total_cells = 0
    for i in range(transition_matrix.shape[0]):
        for j in range(transition_matrix.shape[1]):
            val = transition_matrix.iloc[i, j]
            if j < i:
                upgrade_count += val
            elif j > i:
                downgrade_count += val
            total_cells += 1

    return {
        "stability_ratio": round(stability_ratio, 4),
        "avg_upgrade_rate": round(upgrade_count / max(n, 1), 4),
        "avg_downgrade_rate": round(downgrade_count / max(n, 1), 4),
    }
