"""Tests for the SBA commercial-portfolio monitoring modules.

These use a small synthetic frame that mimics the *cleaned* SBA schema, so the
suite runs fast and does not depend on the large (gitignored) raw CSVs. The
synthetic frame is for exercising the analytics only — the project itself runs
on real SBA 7(a) data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import chargeoff as co
from src import concentration as conc
from src import leading
from src import problem_exposure as pe
from src import report as rpt
from src import risk_appetite as ra
from src import transitions, vintage
from src.base_table import build_base_table
from src.config import load_config
from src.data_loader import clean, data_quality_summary
from src.early_warning import flag_high_risk_segments
from src.utils import herfindahl_index, top_n_share


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def raw_frame():
    """A small raw-like SBA frame (as read from CSV, pre-clean)."""
    rng = np.random.default_rng(42)
    n = 4000
    sectors = ["722110", "236220", "541110", "445110", "484121"]  # 5 NAICS codes
    states = ["CA", "TX", "NY", "FL", "IL"]
    banks = [f"Bank {i}" for i in range(20)]
    fy = rng.integers(2000, 2020, n)

    # Charge-off ~15%, more likely in early (crisis) vintages.
    base_rate = np.where(np.isin(fy, [2006, 2007, 2008]), 0.30, 0.10)
    is_co = rng.random(n) < base_rate

    approval_month = rng.integers(1, 13, n)
    approval = [f"{m:02d}/15/{y}" for m, y in zip(approval_month, fy)]
    # Charge-off date ~2 years after approval for defaulters.
    chargeoff = [
        f"{m:02d}/15/{y + 2}" if co_ else ""
        for m, y, co_ in zip(approval_month, fy, is_co)
    ]
    pif = ["" if co_ else f"{m:02d}/15/{y + 5}" for m, y, co_ in zip(approval_month, fy, is_co)]

    amounts = rng.choice([30_000, 100_000, 250_000, 700_000, 1_500_000, 3_000_000], n)
    co_amount = np.where(is_co, amounts * 0.6, 0.0)
    status = np.where(is_co, "CHGOFF", "P I F")

    return pd.DataFrame({
        "program": " 7A",
        "borrname": [f"Borrower {i}" for i in range(n)],
        "borrstate": rng.choice(states, n),
        "bankname": rng.choice(banks, n),
        "grossapproval": amounts,
        "sbaguaranteedapproval": amounts * 0.75,
        "approvaldate": approval,
        "approvalfy": fy,
        "terminmonths": rng.choice([84, 120, 240], n),
        "naicscode": rng.choice(sectors, n),
        "naicsdescription": "desc",
        "projectstate": rng.choice(states, n),
        "businesstype": "CORPORATION",
        "jobssupported": rng.integers(0, 50, n),
        "loanstatus": status,
        "paidinfulldate": pif,
        "chargeoffdate": chargeoff,
        "grosschargeoffamount": co_amount,
    })


@pytest.fixture(scope="module")
def base(raw_frame, cfg):
    cleaned = clean(raw_frame, config=cfg)
    return build_base_table(cleaned, config=cfg)


# --------------------------------------------------------------------------- #
# Utility maths                                                               #
# --------------------------------------------------------------------------- #
def test_hhi_bounds():
    # Single segment -> HHI 1.0; evenly split four ways -> 0.25.
    assert herfindahl_index(pd.Series([100])) == pytest.approx(1.0)
    assert herfindahl_index(pd.Series([25, 25, 25, 25])) == pytest.approx(0.25)
    assert herfindahl_index(pd.Series([0, 0])) == 0.0


def test_top_n_share():
    s = pd.Series([50, 30, 15, 5])
    assert top_n_share(s, 1) == pytest.approx(0.5)
    assert top_n_share(s, 2) == pytest.approx(0.8)
    assert top_n_share(s, 10) == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Cleaning                                                                    #
# --------------------------------------------------------------------------- #
def test_clean_parses_and_maps(raw_frame, cfg):
    cleaned = clean(raw_frame, config=cfg)
    assert pd.api.types.is_datetime64_any_dtype(cleaned["approvaldate"])
    # NAICS 72xxxx -> Accommodation & Food Services.
    assert (cleaned.loc[cleaned["naics_sector_code"] == "72", "naics_sector"]
            == "Accommodation & Food Services").all()
    # Status label populated.
    assert set(cleaned["status_label"].unique()) <= {"Paid in full", "Charged off"}


def test_clean_drops_never_funded(cfg):
    raw = pd.DataFrame({c: [] for c in [
        "program", "borrname", "borrstate", "bankname", "grossapproval",
        "sbaguaranteedapproval", "approvaldate", "approvalfy", "terminmonths",
        "naicscode", "naicsdescription", "projectstate", "businesstype",
        "jobssupported", "loanstatus", "paidinfulldate", "chargeoffdate",
        "grosschargeoffamount"]})
    raw = pd.concat([raw, pd.DataFrame([
        {"loanstatus": "CANCLD", "grossapproval": 1000, "naicscode": "722110",
         "approvaldate": "01/01/2010", "approvalfy": 2010, "grosschargeoffamount": 0,
         "chargeoffdate": "", "paidinfulldate": "", "borrstate": "CA", "bankname": "B",
         "sbaguaranteedapproval": 750, "terminmonths": 84, "naicsdescription": "d",
         "projectstate": "CA", "businesstype": "CORP", "jobssupported": 1,
         "program": " 7A", "borrname": "x"},
        {"loanstatus": "CHGOFF", "grossapproval": 1000, "naicscode": "722110",
         "approvaldate": "01/01/2010", "approvalfy": 2010, "grosschargeoffamount": 600,
         "chargeoffdate": "01/01/2012", "paidinfulldate": "", "borrstate": "CA", "bankname": "B",
         "sbaguaranteedapproval": 750, "terminmonths": 84, "naicsdescription": "d",
         "projectstate": "CA", "businesstype": "CORP", "jobssupported": 1,
         "program": " 7A", "borrname": "y"},
    ])], ignore_index=True)
    cleaned = clean(raw, config=cfg)
    assert (cleaned["loanstatus"] == "CHGOFF").all()  # CANCLD dropped
    assert len(cleaned) == 1


# --------------------------------------------------------------------------- #
# Base table                                                                  #
# --------------------------------------------------------------------------- #
def test_base_table_derived_fields(base):
    assert {"vintage", "is_default", "size_band", "months_to_chargeoff",
            "fully_seasoned"} <= set(base.columns)
    # months_to_chargeoff only set for defaults.
    assert base.loc[~base["is_default"], "months_to_chargeoff"].isna().all()
    assert (base.loc[base["is_default"], "months_to_chargeoff"] > 0).all()
    # Defaulters are ~24 months to charge-off in the fixture.
    assert base.loc[base["is_default"], "months_to_chargeoff"].median() == pytest.approx(24, abs=1)


def test_seasoning_flag(base, cfg):
    cutoff = cfg["universe"]["fully_seasoned_max_fy"]
    assert (base.loc[base["vintage"] <= cutoff, "fully_seasoned"]).all()
    assert (~base.loc[base["vintage"] > cutoff, "fully_seasoned"]).all()


# --------------------------------------------------------------------------- #
# Concentration                                                               #
# --------------------------------------------------------------------------- #
def test_concentration_by_industry(base):
    out = conc.concentration_by(base, "industry")
    assert "exposure_share" in out.columns
    assert out["exposure_share"].sum() <= 1.01  # rounded shares, full universe in top-N
    # Sorted descending by exposure.
    assert out["exposure"].is_monotonic_decreasing


def test_hhi_summary_dimensions(base):
    out = conc.hhi_summary(base)
    assert set(out["dimension"]) == {"industry", "state", "lender"}
    assert (out["hhi"] >= 0).all() and (out["hhi"] <= 1).all()


# --------------------------------------------------------------------------- #
# Charge-off & vintage                                                        #
# --------------------------------------------------------------------------- #
def test_chargeoff_rates_in_range(base):
    for table in (co.chargeoff_by_industry(base), co.chargeoff_by_size_band(base),
                  co.chargeoff_by_vintage(base)):
        assert (table["chargeoff_rate_count"].between(0, 1)).all()


def test_crisis_vintages_worse(base):
    cov = co.chargeoff_by_vintage(base).set_index("vintage")["chargeoff_rate_count"]
    assert cov.loc[2007] > cov.loc[2003]  # fixture builds in a crisis spike


def test_vintage_curves_monotonic_and_bounded(base, cfg):
    curves = vintage.compute_vintage_curves(base, config=cfg)
    assert not curves.empty
    # Each cohort's cumulative curve is non-decreasing across MOB (ignoring NaN).
    for _, row in curves.iterrows():
        vals = row.dropna().values
        assert np.all(np.diff(vals) >= -1e-9)
        assert vals.max() <= 1.0 if vals.size else True


# --------------------------------------------------------------------------- #
# Transitions & early warning                                                 #
# --------------------------------------------------------------------------- #
def test_loan_age_transition_sums(base):
    out = transitions.loan_age_transition(base)
    assert out["pct_of_chargeoffs"].sum() == pytest.approx(1.0, abs=1e-3)
    assert out["cumulative_pct_of_chargeoffs"].iloc[-1] == pytest.approx(1.0, abs=1e-3)


def test_early_warning_flags_are_elevated(base, cfg):
    flagged = flag_high_risk_segments(base, config=cfg)
    if not flagged.empty:
        thresh = cfg["early_warning"]["elevated_multiple"]
        assert (flagged["rate_multiple"] >= thresh).all()
        assert set(flagged["severity"]) <= {"Elevated", "High"}


# --------------------------------------------------------------------------- #
# Problem-exposure layer (CML-1)                                              #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def problem_base(cfg):
    """A tiny cleaned frame carrying the pre-charge-off problem statuses."""
    statuses = (["CHGOFF"] * 10 + ["P I F"] * 70 + ["DELINQ"] * 8
                + ["PSTDUE"] * 5 + ["LIQUID"] * 7)
    n = len(statuses)
    raw = pd.DataFrame({
        "program": " 7A", "borrname": [f"B{i}" for i in range(n)],
        "borrstate": "CA", "bankname": "Bank A",
        "grossapproval": 100_000, "sbaguaranteedapproval": 75_000,
        "approvaldate": "01/15/2010", "approvalfy": 2010, "terminmonths": 84,
        "naicscode": "722110", "naicsdescription": "d", "projectstate": "CA",
        "businesstype": "CORP", "jobssupported": 3, "loanstatus": statuses,
        "paidinfulldate": "", "chargeoffdate": "",
        "grosschargeoffamount": [60_000 if s == "CHGOFF" else 0 for s in statuses],
    })
    return build_base_table(clean(raw, config=cfg), config=cfg)


def test_problem_exposure_flag_excludes_default(problem_base):
    # Problem-exposure and default are disjoint flags.
    assert not (problem_base["is_problem_exposure"] & problem_base["is_default"]).any()
    # DELINQ + PSTDUE + LIQUID = 20 problem exposures in the fixture.
    assert int(problem_base["is_problem_exposure"].sum()) == 20


def test_problem_exposure_overview(problem_base, cfg):
    ov = pe.problem_exposure_overview(problem_base, config=cfg)
    # One row per problem status plus a total row.
    assert set(["DELINQ", "PSTDUE", "LIQUID", "ALL_PROBLEM"]) <= set(ov["status"])
    total = ov.loc[ov["status"] == "ALL_PROBLEM", "loan_count"].iloc[0]
    assert total == 20
    # LIQUID flagged as a near-certain future charge-off (leading) signal.
    liquid_signal = ov.loc[ov["status"] == "LIQUID", "signal"].iloc[0]
    assert "near-certain" in liquid_signal.lower()


def test_problem_exposure_by_segment(problem_base):
    seg = pe.problem_exposure_by(problem_base, "industry")
    assert {"problem_rate", "chargeoff_rate"} <= set(seg.columns)
    assert (seg["problem_rate"].between(0, 1)).all()


# --------------------------------------------------------------------------- #
# Risk appetite & limits (CML-2)                                              #
# --------------------------------------------------------------------------- #
def test_appetite_dashboard_shape(base, cfg):
    dash = ra.appetite_dashboard(base, config=cfg)
    # One row per configured limit, incl. the single-lender + top-20 limits.
    assert len(dash) == len(cfg["risk_appetite"]["limits"])
    assert {"single_lender_share", "top20_lender_share"} <= set(dash["id"])
    assert set(dash["rag"]) <= {"GREEN", "AMBER", "RED", "N/A"}
    assert {"owner", "breach_action", "review_cycle"} <= set(dash.columns)


def test_appetite_rag_classification():
    # Upper-direction: value below amber is GREEN, in [amber,red) AMBER, >=red RED.
    assert ra._rag(0.05, 0.10, 0.18, "upper") == "GREEN"
    assert ra._rag(0.12, 0.10, 0.18, "upper") == "AMBER"
    assert ra._rag(0.20, 0.10, 0.18, "upper") == "RED"
    assert ra._rag(float("nan"), 0.10, 0.18, "upper") == "N/A"


def test_appetite_actions_only_amber_red(base, cfg):
    dash = ra.appetite_dashboard(base, config=cfg)
    actions = ra.appetite_actions(dash)
    flagged = dash[dash["rag"].isin(["AMBER", "RED"])]
    assert len(actions) == len(flagged)
    if not actions.empty:
        assert {"action", "owner", "due"} <= set(actions.columns)


# --------------------------------------------------------------------------- #
# Leading vs lagging (CML-4)                                                  #
# --------------------------------------------------------------------------- #
def test_metric_classification_has_leading_and_lagging():
    m = leading.metric_classification()
    assert {"Leading", "Lagging"} <= set(m["type"].str.replace("/static", "", regex=False))
    # The problem-exposure layer is one of the leading signals.
    assert m[m["metric"].str.contains("Problem-exposure")]["type"].iloc[0] == "Leading"


def test_origination_trend(base, cfg):
    tr = leading.origination_trend(base, config=cfg)
    assert {"exposure_yoy_growth", "top_sector_share", "large_ticket_share"} <= set(tr.columns)
    assert tr["vintage"].is_monotonic_increasing
    assert (tr["top_sector_share"].between(0, 1)).all()


def test_vintage_over_vintage_early_mob(base, cfg):
    vov = leading.vintage_over_vintage_early_mob(base, config=cfg)
    if not vov.empty:
        assert (vov["early_mob_chargeoff"].between(0, 1)).all()
        # Ratio is rate / prior rate; first row has no prior.
        assert pd.isna(vov["vintage_over_vintage_ratio"].iloc[0])


# --------------------------------------------------------------------------- #
# Report assembly                                                             #
# --------------------------------------------------------------------------- #
def test_report_builds(base, cfg):
    dq = data_quality_summary(base, config=cfg)
    hhi = conc.hhi_summary(base)
    co_ind = co.chargeoff_by_industry(base)
    co_vin = co.chargeoff_by_vintage(base)
    early = flag_high_risk_segments(base, config=cfg)
    stage = rpt.stage_proxy_summary(base, config=cfg)
    md = rpt.build_markdown_report(dq, hhi, co_ind, co_vin, early, stage)
    assert "Commercial Portfolio Monitoring Pack" in md
    assert "APS 330-style" in md
    # Stage proxy is a 2-row performing/defaulted split.
    assert len(stage) == 2


def test_report_leads_with_rag_dashboard(base, cfg):
    dq = data_quality_summary(base, config=cfg)
    hhi = conc.hhi_summary(base)
    co_ind = co.chargeoff_by_industry(base)
    co_vin = co.chargeoff_by_vintage(base)
    early = flag_high_risk_segments(base, config=cfg)
    stage = rpt.stage_proxy_summary(base, config=cfg)
    dash = ra.appetite_dashboard(base, config=cfg)
    actions = ra.appetite_actions(dash)
    md = rpt.build_markdown_report(
        dq, hhi, co_ind, co_vin, early, stage,
        appetite=dash, appetite_actions=actions,
    )
    # Dashboard leads the pack (before "Portfolio at a glance").
    assert "Board credit-risk dashboard" in md
    assert md.index("Board credit-risk dashboard") < md.index("Portfolio at a glance")
    assert "RAG status" in md
    assert "Risk appetite & limit register" in md
