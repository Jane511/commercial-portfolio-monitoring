from __future__ import annotations

import numpy as np
import pandas as pd

from .config import MACRO_SCENARIOS, SCENARIO_WEIGHTS


def build_scenario_adjustments(
    scenarios: dict | None = None,
) -> pd.DataFrame:
    """Map each macro scenario to PD and LGD scalars.

    Returns a table with one row per scenario containing the scalar
    adjustments and macro parameters.
    """
    sc = scenarios or MACRO_SCENARIOS
    records = []
    for name, params in sc.items():
        records.append({
            "scenario": name,
            "gdp_growth": params["gdp_growth"],
            "unemployment": params["unemployment"],
            "house_price_change": params["house_price_change"],
            "pd_scalar": params["pd_scalar"],
            "lgd_scalar": params["lgd_scalar"],
            "description": params["description"],
        })
    return pd.DataFrame.from_records(records)


def apply_macro_overlay(
    df: pd.DataFrame,
    scenario_adjustments: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create one copy of the portfolio per scenario with adjusted PD/LGD.

    Returns a stacked DataFrame with a 'scenario' column.
    Property-backed facilities get additional LGD impact from house price declines.
    """
    if scenario_adjustments is None:
        scenario_adjustments = build_scenario_adjustments()

    frames: list[pd.DataFrame] = []
    for _, sc in scenario_adjustments.iterrows():
        scenario_df = df.copy()
        scenario_df["scenario"] = sc["scenario"]

        # Apply PD scalar
        scenario_df["pd_scenario"] = np.clip(
            scenario_df["lifetime_pd"] * sc["pd_scalar"], 0.0, 1.0
        ).round(6)

        # Apply LGD scalar — property gets extra hit from house price decline
        lgd_scalar = sc["lgd_scalar"]
        hpi_change = sc.get("house_price_change", 0.0)
        property_mask = scenario_df["product_type"] == "Property Backed Loan"
        lgd_adjustment = np.where(
            property_mask & (hpi_change < 0),
            lgd_scalar * (1.0 + abs(hpi_change) * 0.3),
            lgd_scalar,
        )
        scenario_df["lgd_scenario"] = np.clip(
            scenario_df["lgd_final"] * lgd_adjustment, 0.0, 1.0
        ).round(4)

        frames.append(scenario_df)

    return pd.concat(frames, ignore_index=True)


def probability_weight_ecl(
    scenario_ecls: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Collapse scenario-level ECL into probability-weighted ECL per facility.

    AASB 9 requires multiple scenario weighting — this is the final step
    that produces the reported ECL.
    """
    w = weights or SCENARIO_WEIGHTS
    out = scenario_ecls.copy()
    out["scenario_weight"] = out["scenario"].map(w)
    out["weighted_ecl"] = out["ecl_scenario"] * out["scenario_weight"]

    facility_ecl = out.groupby("facility_id", sort=False).agg(
        ecl_probability_weighted=("weighted_ecl", "sum"),
    ).reset_index()

    return facility_ecl
