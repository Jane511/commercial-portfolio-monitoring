from __future__ import annotations

import numpy as np
import pandas as pd

from .config import GRADE_SHAPE_FACTORS, LIFETIME_PD_MAX_YEARS


def build_marginal_pd_curve(
    pd_12m: float,
    risk_grade: str,
    max_years: int = LIFETIME_PD_MAX_YEARS,
) -> list[float]:
    """Convert a 12-month PD into a marginal PD curve for each future year.

    Uses a conditional survival approach with a grade-dependent shape factor:
    - Higher-quality grades (RG1/RG2) have flatter curves
    - Lower-quality grades (RG4/RG5) are front-loaded (higher early default)

    marginal_pd(t) is derived from:
        survival(t) = (1 - pd_12m)^(t * shape_factor)
        cumulative_pd(t) = 1 - survival(t)
        marginal_pd(t) = cumulative_pd(t) - cumulative_pd(t-1)
    """
    shape = GRADE_SHAPE_FACTORS.get(risk_grade, 1.0)
    marginals: list[float] = []
    prev_cumulative = 0.0
    for year in range(1, max_years + 1):
        survival = (1.0 - pd_12m) ** (year * shape)
        cumulative = 1.0 - survival
        marginal = max(cumulative - prev_cumulative, 0.0)
        marginals.append(round(marginal, 6))
        prev_cumulative = cumulative
    return marginals


def calculate_cumulative_pd(marginal_pds: list[float]) -> list[float]:
    """Running cumulative PD from marginal PD vector."""
    cumulative: list[float] = []
    cum = 0.0
    for mp in marginal_pds:
        cum = 1.0 - (1.0 - cum) * (1.0 - mp)
        cumulative.append(round(cum, 6))
    return cumulative


def assign_lifetime_pd(
    df: pd.DataFrame,
    max_years: int = LIFETIME_PD_MAX_YEARS,
) -> pd.DataFrame:
    """Add lifetime_pd column based on remaining term and stage.

    - Stage 1: lifetime_pd = pd_12m (12-month ECL only)
    - Stage 2: lifetime_pd = cumulative PD over remaining term
    - Stage 3: lifetime_pd = 1.0 (credit-impaired)
    """
    out = df.copy()
    lifetime_pds: list[float] = []

    for _, row in out.iterrows():
        stage = int(row.get("aasb9_stage", 1))
        pd_12m = float(row["pd_final"])
        grade = str(row.get("internal_risk_grade", "RG3"))

        if stage == 3:
            lifetime_pds.append(1.0)
        elif stage == 2:
            remaining_months = int(row.get("remaining_term_months", 36))
            remaining_years = max(1, int(np.ceil(remaining_months / 12)))
            years_to_use = min(remaining_years, max_years)
            marginals = build_marginal_pd_curve(pd_12m, grade, max_years=years_to_use)
            cumulatives = calculate_cumulative_pd(marginals)
            lifetime_pds.append(min(cumulatives[-1], 1.0))
        else:
            lifetime_pds.append(pd_12m)

    out["lifetime_pd"] = [round(p, 6) for p in lifetime_pds]
    return out
