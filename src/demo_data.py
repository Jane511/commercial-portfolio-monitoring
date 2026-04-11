from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    AS_OF_DATE,
    INDUSTRY_SETTINGS,
    N_FACILITIES,
    PRIOR_PERIOD_DATE,
    PRODUCT_SETTINGS,
    RANDOM_SEED,
    REGION_FACTORS,
    RISK_GRADE_ORDER,
    RISK_GRADE_PD_LOOKUP,
)


def _assign_risk_grade(risk_score: float) -> str:
    if risk_score < 0.22:
        return "RG1"
    if risk_score < 0.30:
        return "RG2"
    if risk_score < 0.40:
        return "RG3"
    if risk_score < 0.54:
        return "RG4"
    return "RG5"


def build_demo_el_dataset(
    n_facilities: int = N_FACILITIES,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate a synthetic loan-level EL dataset with fields needed for AASB 9 staging."""
    rng = np.random.default_rng(seed)
    product_names = tuple(PRODUCT_SETTINGS.keys())
    product_weights = np.array([0.40, 0.32, 0.28], dtype=float)
    industry_names = tuple(INDUSTRY_SETTINGS.keys())
    region_names = tuple(REGION_FACTORS.keys())

    records: list[dict] = []
    for i in range(1, n_facilities + 1):
        product_type = rng.choice(product_names, p=product_weights / product_weights.sum())
        ps = PRODUCT_SETTINGS[product_type]
        industry = rng.choice(industry_names)
        region = rng.choice(region_names)

        limit_amount = round(rng.uniform(*ps["limit_range"]), 2)
        drawn_pct = float(rng.uniform(*ps["drawn_range"]))
        drawn_balance = round(limit_amount * drawn_pct, 2)
        loan_term_months = int(rng.choice(ps["term_options"]))
        remaining_term_months = max(6, loan_term_months - int(rng.uniform(0, loan_term_months * 0.6)))
        security_type = rng.choice(
            ps["security_types"],
            p=np.array(ps["security_weights"], dtype=float),
        )

        quality = rng.normal(0.0, 1.0)
        risk_score = float(np.clip(
            0.12 + ps["risk_factor"] * 0.45 + INDUSTRY_SETTINGS[industry]["risk_factor"] * 0.35 + rng.normal(0, 0.03),
            0.05, 0.95,
        ))
        risk_grade = _assign_risk_grade(risk_score)
        pd_final = float(np.clip(
            RISK_GRADE_PD_LOOKUP[risk_grade] * (1.0 + rng.normal(0, 0.05)),
            0.005, 0.35,
        ))

        # Origination PD — typically lower (borrower was healthier at origination)
        origination_pd = float(np.clip(pd_final * rng.uniform(0.5, 1.1), 0.003, 0.30))
        origination_grade_idx = max(0, RISK_GRADE_ORDER.index(risk_grade) - int(rng.choice([0, 0, 0, 1, 1, 2])))
        origination_risk_grade = RISK_GRADE_ORDER[origination_grade_idx]

        lgd_final = float(np.clip(rng.uniform(0.20, 0.65), 0.08, 0.95))
        ead = drawn_balance
        expected_loss = pd_final * lgd_final * ead

        dscr = float(np.clip(1.55 + quality * 0.22 - ps["risk_factor"] * 0.55 + rng.normal(0, 0.08), 0.75, 2.50))
        arrears_days = int(np.clip(
            round(rng.normal(8 + ps["risk_factor"] * 55 + max(-quality, 0) * 20, 14)),
            0, 120,
        ))
        watchlist_flag = int(
            arrears_days >= 60
            or dscr < 1.00
            or rng.random() < (0.03 + ps["risk_factor"] * 0.03)
        )
        default_flag = int(arrears_days >= 90 or (watchlist_flag and rng.random() < 0.15))

        risk_addon = {"RG1": 0.000, "RG2": 0.005, "RG3": 0.011, "RG4": 0.020, "RG5": 0.035}[risk_grade]
        interest_rate = round(ps["interest_base"] + risk_addon + rng.normal(0, 0.004), 4)

        records.append({
            "facility_id": f"FAC-{i:05d}",
            "borrower_id": f"BOR-{((i - 1) % 90) + 1:04d}",
            "product_type": product_type,
            "industry": industry,
            "region": region,
            "security_type": security_type,
            "internal_risk_grade": risk_grade,
            "origination_risk_grade": origination_risk_grade,
            "limit_amount": limit_amount,
            "drawn_balance": drawn_balance,
            "loan_term_months": loan_term_months,
            "remaining_term_months": remaining_term_months,
            "interest_rate": interest_rate,
            "pd_final": round(pd_final, 4),
            "origination_pd": round(origination_pd, 4),
            "lgd_final": round(lgd_final, 4),
            "ead": round(ead, 2),
            "expected_loss": round(expected_loss, 2),
            "el_rate": round(pd_final * lgd_final, 6),
            "dscr": round(dscr, 3),
            "arrears_days": arrears_days,
            "watchlist_flag": watchlist_flag,
            "default_flag": default_flag,
            "as_of_date": AS_OF_DATE,
        })

    return pd.DataFrame.from_records(records)


def build_demo_prior_period(
    current_df: pd.DataFrame,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate a prior-period snapshot for migration tracking.

    Simulates the portfolio 6 months earlier with slightly better credit quality.
    """
    rng = np.random.default_rng(seed + 10)
    prior = current_df[["facility_id", "borrower_id", "product_type", "industry",
                         "region", "internal_risk_grade", "pd_final", "lgd_final",
                         "ead", "arrears_days", "watchlist_flag", "default_flag"]].copy()

    # Prior period had generally better credit quality
    grade_upgrade_map = {"RG1": "RG1", "RG2": "RG1", "RG3": "RG2", "RG4": "RG3", "RG5": "RG4"}
    upgrade_mask = rng.random(len(prior)) < 0.25
    prior.loc[upgrade_mask, "internal_risk_grade"] = prior.loc[upgrade_mask, "internal_risk_grade"].map(grade_upgrade_map)

    prior["pd_final"] = np.clip(prior["pd_final"] * rng.uniform(0.7, 1.0, len(prior)), 0.005, 0.35).round(4)
    prior["arrears_days"] = np.clip(prior["arrears_days"] - rng.integers(0, 20, len(prior)), 0, 120).astype(int)
    prior["watchlist_flag"] = np.where(prior["arrears_days"] >= 60, 1, (rng.random(len(prior)) < 0.05).astype(int))
    prior["default_flag"] = np.where(prior["arrears_days"] >= 90, 1, 0)
    prior["as_of_date"] = PRIOR_PERIOD_DATE

    # Assign prior-period stage
    prior["aasb9_stage"] = 1
    prior.loc[
        (prior["arrears_days"] >= 30) | (prior["watchlist_flag"] == 1) |
        (prior["internal_risk_grade"].isin(["RG4", "RG5"])),
        "aasb9_stage"
    ] = 2
    prior.loc[(prior["arrears_days"] >= 90) | (prior["default_flag"] == 1), "aasb9_stage"] = 3

    return prior


def build_demo_rwa_dataset(el_df: pd.DataFrame) -> pd.DataFrame:
    """Generate a synthetic RWA dataset mimicking Module 4 output."""
    out = el_df[["facility_id", "pd_final", "lgd_final", "ead"]].copy()
    out.rename(columns={"pd_final": "pd_12m", "lgd_final": "lgd_downturn", "ead": "ead_downturn"}, inplace=True)
    out["expected_loss"] = out["pd_12m"] * out["lgd_downturn"] * out["ead_downturn"]
    out["capital_requirement"] = out["expected_loss"] * 12.5
    out["rwa"] = out["capital_requirement"] * 12.5
    return out.round({"expected_loss": 2, "capital_requirement": 2, "rwa": 2})
