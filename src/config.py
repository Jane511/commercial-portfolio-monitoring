from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
MANUAL_DIR = DATA_DIR / "manual"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"
DOCS_DIR = ROOT / "docs"
NOTEBOOKS_DIR = ROOT / "notebooks"

DEFAULT_INPUT_FILES = {
    "loan_level_el": INPUT_DIR / "loan_level_el.csv",
    "exposure_level_rwa": INPUT_DIR / "exposure_level_rwa.csv",
    "facility_raroc": INPUT_DIR / "facility_raroc.csv",
    "prior_period": INPUT_DIR / "prior_period_snapshot.csv",
}

DEFAULT_OUTPUT_FILES = {
    "facility_ecl": OUTPUT_DIR / "facility_ecl.csv",
    "ecl_by_stage": OUTPUT_DIR / "ecl_summary_by_stage.csv",
    "ecl_by_segment": OUTPUT_DIR / "ecl_summary_by_segment.csv",
    "concentration": OUTPUT_DIR / "concentration_report.csv",
    "transition_grade": OUTPUT_DIR / "transition_matrix_grade.csv",
    "transition_stage": OUTPUT_DIR / "transition_matrix_stage.csv",
    "early_warning": OUTPUT_DIR / "early_warning_summary.csv",
    "aps330_stage_movement": OUTPUT_DIR / "aps330_stage_movement.csv",
    "aps330_credit_quality": OUTPUT_DIR / "aps330_credit_quality.csv",
}

SIBLING_INPUT_CANDIDATES = {
    "loan_level_el": (
        ROOT.parent / "5. Expected Loss Engine and Portfolio Stress Testing" / "data" / "output" / "loan_level_el.csv",
    ),
    "exposure_level_rwa": (
        ROOT.parent / "4. RWA & Capital Module" / "output" / "exposure_level_rwa.csv",
    ),
    "facility_raroc": (
        ROOT.parent / "6. RAROC Pricing and Return Hurdle" / "data" / "output" / "facility_raroc.csv",
    ),
}

AS_OF_DATE = "2026-04-10"
PRIOR_PERIOD_DATE = "2025-10-10"
RANDOM_SEED = 42
N_FACILITIES = 180

# --------------------------------------------------------------------------- #
# AASB 9 Staging — Significant Increase in Credit Risk (SICR) thresholds      #
# --------------------------------------------------------------------------- #
SICR_THRESHOLDS = {
    "dpd_stage2": 30,               # days past due for Stage 2
    "dpd_stage3": 90,               # days past due for Stage 3
    "pd_increase_relative": 2.0,    # 2x origination PD → SICR
    "pd_increase_absolute": 0.005,  # absolute PD increase floor (50bps)
    "grade_downgrade_notches": 2,   # 2+ notch downgrade → SICR
}

# --------------------------------------------------------------------------- #
# Macro Scenarios — RBA-aligned forward-looking overlays                       #
# --------------------------------------------------------------------------- #
MACRO_SCENARIOS = {
    "base": {
        "gdp_growth": 0.025,
        "unemployment": 0.042,
        "house_price_change": 0.03,
        "pd_scalar": 1.00,
        "lgd_scalar": 1.00,
        "description": "Consensus baseline — steady growth, stable employment",
    },
    "downside": {
        "gdp_growth": 0.005,
        "unemployment": 0.058,
        "house_price_change": -0.08,
        "pd_scalar": 1.35,
        "lgd_scalar": 1.12,
        "description": "Mild recession — GDP stalls, unemployment rises, property softens",
    },
    "severe_downside": {
        "gdp_growth": -0.020,
        "unemployment": 0.080,
        "house_price_change": -0.20,
        "pd_scalar": 2.00,
        "lgd_scalar": 1.30,
        "description": "Deep recession — GDP contraction, property crash, credit stress",
    },
}

SCENARIO_WEIGHTS = {
    "base": 0.50,
    "downside": 0.35,
    "severe_downside": 0.15,
}

# --------------------------------------------------------------------------- #
# Lifetime PD — term structure parameters                                      #
# --------------------------------------------------------------------------- #
LIFETIME_PD_MAX_YEARS = 5

# Shape factors control how the marginal PD curve behaves over time.
# Higher-quality grades have flatter curves; lower grades are front-loaded.
GRADE_SHAPE_FACTORS = {
    "RG1": 0.85,
    "RG2": 0.90,
    "RG3": 1.00,
    "RG4": 1.10,
    "RG5": 1.25,
}

# --------------------------------------------------------------------------- #
# Concentration Limits — ICAAP / CPS 220 alignment                            #
# --------------------------------------------------------------------------- #
CONCENTRATION_LIMITS = {
    "single_name_pct": 0.10,         # max 10% of portfolio EAD per borrower
    "sector_pct": 0.25,               # max 25% per industry sector
    "region_pct": 0.35,               # max 35% per geographic region
    "hhi_moderate_threshold": 0.10,    # HHI > 0.10 = moderate concentration
    "hhi_high_threshold": 0.18,        # HHI > 0.18 = high concentration
}

# --------------------------------------------------------------------------- #
# Early Warning Signal thresholds                                              #
# --------------------------------------------------------------------------- #
EARLY_WARNING_THRESHOLDS = {
    "dscr_weak": 1.25,
    "dscr_critical": 1.00,
    "arrears_trending_days": 15,
    "pd_increase_pct": 0.50,          # 50% increase in PD from origination
}

# --------------------------------------------------------------------------- #
# Shared settings (reused from Module 5 for demo data generation)              #
# --------------------------------------------------------------------------- #
PRODUCT_SETTINGS = {
    "SME Cash Flow Term Loan": {
        "loan_type": "term",
        "limit_range": (250_000, 2_500_000),
        "drawn_range": (0.72, 1.00),
        "term_options": (24, 36, 48),
        "interest_base": 0.082,
        "risk_factor": 0.18,
        "security_types": ("General Security Agreement", "Receivables Security", "Unsecured"),
        "security_weights": (0.55, 0.20, 0.25),
    },
    "Property Backed Loan": {
        "loan_type": "term",
        "limit_range": (500_000, 6_000_000),
        "drawn_range": (0.80, 1.00),
        "term_options": (36, 48, 60),
        "interest_base": 0.071,
        "risk_factor": 0.12,
        "security_types": ("Commercial Property", "Residential Investment Property"),
        "security_weights": (0.65, 0.35),
    },
    "Overdraft / Revolving Working Capital": {
        "loan_type": "revolving",
        "limit_range": (100_000, 1_500_000),
        "drawn_range": (0.35, 0.80),
        "term_options": (12, 12, 24),
        "interest_base": 0.094,
        "risk_factor": 0.24,
        "security_types": ("General Security Agreement", "Unsecured"),
        "security_weights": (0.75, 0.25),
    },
}

INDUSTRY_SETTINGS = {
    "Agriculture, Forestry and Fishing": {"risk_factor": 0.20},
    "Manufacturing": {"risk_factor": 0.22},
    "Retail Trade": {"risk_factor": 0.18},
    "Wholesale Trade": {"risk_factor": 0.15},
    "Accommodation and Food Services": {"risk_factor": 0.24},
    "Construction": {"risk_factor": 0.21},
    "Health Care and Social Assistance": {"risk_factor": 0.10},
    "Professional, Scientific and Technical Services": {"risk_factor": 0.11},
    "Transport, Postal and Warehousing": {"risk_factor": 0.17},
}

REGION_FACTORS = {
    "NSW": 0.00, "VIC": 0.02, "QLD": 0.03, "WA": -0.01, "SA": 0.01,
}

RISK_GRADE_PD_LOOKUP = {
    "RG1": 0.012, "RG2": 0.022, "RG3": 0.041, "RG4": 0.079, "RG5": 0.150,
}

RISK_GRADE_ORDER = ["RG1", "RG2", "RG3", "RG4", "RG5"]
