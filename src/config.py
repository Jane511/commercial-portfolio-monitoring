"""Project configuration: paths, runtime config loading, and SBA constants.

Analytical modules import paths and constants from here and call
``load_config()`` for tunable business parameters (read from ``config.yaml``).
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

# --------------------------------------------------------------------------- #
# Paths                                                                        #
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INPUT_DIR = DATA_DIR / "input"          # raw SBA CSVs (gitignored)
OUTPUT_DIR = ROOT / "outputs"           # committed result tables + charts
TABLES_DIR = OUTPUT_DIR / "tables"
CHARTS_DIR = OUTPUT_DIR / "charts"
DOCS_DIR = ROOT / "docs"
NOTEBOOKS_DIR = ROOT / "notebooks"

DEFAULT_CONFIG_PATH = ROOT / "config.yaml"

# The two real SBA 7(a) FOIA loan-level extracts shipped with this project.
# Any CSV matching ``foia-7a-*.csv`` in INPUT_DIR is picked up automatically by
# the loader, so adding the 504 file later requires no code change here.
DEFAULT_INPUT_GLOB = "foia-7a-*.csv"

# Result tables written by the pipeline (under outputs/tables/).
OUTPUT_TABLES = {
    "data_quality": TABLES_DIR / "00_data_quality_summary.csv",
    "base_table_sample": TABLES_DIR / "01_base_table_sample.csv",
    "concentration_industry": TABLES_DIR / "02_concentration_industry.csv",
    "concentration_state": TABLES_DIR / "02_concentration_state.csv",
    "concentration_lender": TABLES_DIR / "02_concentration_lender.csv",
    "concentration_hhi": TABLES_DIR / "02_concentration_hhi_summary.csv",
    "chargeoff_by_industry": TABLES_DIR / "03_chargeoff_by_industry.csv",
    "chargeoff_by_size": TABLES_DIR / "03_chargeoff_by_size_band.csv",
    "chargeoff_by_vintage": TABLES_DIR / "03_chargeoff_by_vintage.csv",
    "vintage_curves": TABLES_DIR / "03_vintage_cohort_curves.csv",
    "loan_age_transitions": TABLES_DIR / "04_loan_age_transitions.csv",
    "early_warning": TABLES_DIR / "04_early_warning_segments.csv",
    "problem_exposure_overview": TABLES_DIR / "04_problem_exposure_overview.csv",
    "problem_exposure_by_industry": TABLES_DIR / "04_problem_exposure_by_industry.csv",
    "stage_proxy": TABLES_DIR / "05_stage_proxy_summary.csv",
    "aps330_credit_quality": TABLES_DIR / "05_aps330_style_credit_quality.csv",
    "risk_appetite_dashboard": TABLES_DIR / "06_risk_appetite_dashboard.csv",
    "risk_appetite_actions": TABLES_DIR / "06_risk_appetite_actions.csv",
    "leading_lagging_map": TABLES_DIR / "07_leading_lagging_map.csv",
    "origination_trend": TABLES_DIR / "07_origination_trend.csv",
    "vintage_over_vintage_early_mob": TABLES_DIR / "07_vintage_over_vintage_early_mob.csv",
}

# --------------------------------------------------------------------------- #
# SBA data constants                                                          #
# --------------------------------------------------------------------------- #
# Raw LoanStatus codes as they appear in the FOIA CSVs (note "P I F" has
# embedded spaces). Mapped to a small set of plain-English outcome classes.
LOAN_STATUS_LABELS = {
    "P I F": "Paid in full",
    "CHGOFF": "Charged off",
    "CURR": "Current",
    "PIF": "Paid in full",            # defensive: some extracts drop the spaces
    "CANCLD": "Cancelled (never funded)",
    "COMMIT": "Committed (never funded)",
    "EXEMPT": "Exempt",
    "PURCH(NOT C/O)": "Guaranty purchased (not charged off)",
    "LIQUID": "In liquidation",
    "CLSLN": "Closed loan",
    "DELINQ": "Delinquent",
    "PSTDUE": "Past due",
    "DEFERD": "Deferred",
}

# NAICS 2-digit sector prefix -> sector name (2017 NAICS structure). Several
# sectors span a range of 2-digit codes, hence the repeated names.
NAICS_SECTOR_NAMES = {
    "11": "Agriculture, Forestry, Fishing & Hunting",
    "21": "Mining, Quarrying, Oil & Gas Extraction",
    "22": "Utilities",
    "23": "Construction",
    "31": "Manufacturing",
    "32": "Manufacturing",
    "33": "Manufacturing",
    "42": "Wholesale Trade",
    "44": "Retail Trade",
    "45": "Retail Trade",
    "48": "Transportation & Warehousing",
    "49": "Transportation & Warehousing",
    "51": "Information",
    "52": "Finance & Insurance",
    "53": "Real Estate & Rental & Leasing",
    "54": "Professional, Scientific & Technical Services",
    "55": "Management of Companies & Enterprises",
    "56": "Administrative & Waste Management Services",
    "61": "Educational Services",
    "62": "Health Care & Social Assistance",
    "71": "Arts, Entertainment & Recreation",
    "72": "Accommodation & Food Services",
    "81": "Other Services (except Public Admin)",
    "92": "Public Administration",
}

# Columns read from the raw CSVs. Keeping this explicit keeps memory down on
# the ~1.2M-row load and documents exactly what the project depends on.
RAW_COLUMNS = [
    "program", "borrname", "borrstate", "bankname",
    "grossapproval", "sbaguaranteedapproval",
    "approvaldate", "approvalfy", "terminmonths",
    "naicscode", "naicsdescription", "projectstate",
    "businesstype", "jobssupported",
    "loanstatus", "paidinfulldate", "chargeoffdate", "grosschargeoffamount",
]


@functools.lru_cache(maxsize=4)
def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load and return project configuration from ``config.yaml``.

    Results are cached per path; call ``load_config.cache_clear()`` to reload
    after editing the file.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
