"""Monitoring pack assembly: stage proxy, an APS 330-style table, and a report.

NOTE ON LABELLING: the credit-quality table below is laid out in the *format*
of an APS 330 (Pillar 3) disclosure for familiarity only. It is built from
public SBA loan data, is not a regulated entity's disclosure, and is labelled
"APS 330-style disclosure format" wherever it appears — not regulatory output.
"""
from __future__ import annotations

import pandas as pd

from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)


def stage_proxy_summary(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Coarse performing-vs-defaulted split — a PROXY, not IFRS 9 staging.

    SBA is outcome-level, not a monthly grade panel, so only this two-way split
    is possible. Full IFRS 9 staging and transition matrices live in the
    companion Freddie Mac monitor.
    """
    cfg = config or load_config()
    default_statuses = set(cfg["universe"]["default_statuses"])
    df = df.copy()
    df["proxy_stage"] = df["loanstatus"].isin(default_statuses).map(
        {True: "Defaulted (charged off) — proxy Stage 3",
         False: "Performing — proxy Stage 1/2"}
    )

    total_exposure = float(df["grossapproval"].sum())
    out = df.groupby("proxy_stage").agg(
        loan_count=("grossapproval", "size"),
        exposure=("grossapproval", "sum"),
        chargeoff_amount=("grosschargeoffamount", "sum"),
    ).reset_index()
    out["exposure_share"] = (out["exposure"] / total_exposure).round(4)
    return out.sort_values("proxy_stage").reset_index(drop=True)


def aps330_style_credit_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Credit-quality-by-industry table in APS 330-style disclosure FORMAT.

    Not a regulatory disclosure — built from public SBA data for layout
    familiarity only.
    """
    total_exposure = float(df["grossapproval"].sum())
    out = df.groupby("naics_sector").agg(
        gross_exposure=("grossapproval", "sum"),
        loan_count=("grossapproval", "size"),
        charged_off_count=("is_default", "sum"),
        charged_off_amount=("grosschargeoffamount", "sum"),
    ).reset_index().rename(columns={"naics_sector": "industry"})
    out["exposure_share"] = (out["gross_exposure"] / total_exposure).round(4)
    out["impairment_rate_dollar"] = (out["charged_off_amount"] / out["gross_exposure"]).round(4)
    return out.sort_values("gross_exposure", ascending=False).reset_index(drop=True)


def _fmt_pct(x: float) -> str:
    return f"{x:.1%}" if pd.notna(x) else "—"


def _fmt_money(x: float) -> str:
    return f"${x:,.0f}" if pd.notna(x) else "—"


_RAG_BADGE = {"GREEN": "🟢 GREEN", "AMBER": "🟡 AMBER", "RED": "🔴 RED", "N/A": "⚪ N/A"}


def _fmt_limit_value(basis: str, v: float) -> str:
    """Format an appetite metric for display per its natural units."""
    if pd.isna(v):
        return "—"
    if basis == "hhi_industry":
        return f"{v:.4f}"
    if basis == "vintage_early_mob_multiple":
        return f"{v:.2f}x"
    return f"{v:.1%}"  # shares and rates


def _render_dashboard(a, appetite: pd.DataFrame, actions: pd.DataFrame | None) -> None:
    """Render the board RAG dashboard + actions table at the top of the report."""
    n_amber = int((appetite["rag"] == "AMBER").sum())
    n_red = int((appetite["rag"] == "RED").sum())
    n_green = int((appetite["rag"] == "GREEN").sum())

    a("## Board credit-risk dashboard — RAG vs risk-appetite limits")
    a("")
    a(f"_Status: 🟢 {n_green} within appetite · 🟡 {n_amber} amber · 🔴 {n_red} red. "
      "Limits, owners and breach actions are defined in `config.yaml` "
      "(risk_appetite) per APS 220 paras 20/35; see section 7._")
    a("")
    a("| Metric | Value | Amber | Red | RAG status | Owner |")
    a("|---|---|---|---|---|---|")
    for _, r in appetite.iterrows():
        basis = r["basis"]
        a(f"| {r['metric']} | {_fmt_limit_value(basis, r['value'])} | "
          f"{_fmt_limit_value(basis, r['amber'])} | {_fmt_limit_value(basis, r['red'])} | "
          f"{_RAG_BADGE.get(r['rag'], r['rag'])} | {r['owner']} |")
    a("")

    a("**Actions (amber/red items):**")
    a("")
    if actions is None or actions.empty:
        a("_All limits within appetite — no escalation actions outstanding._")
    else:
        a("| Action | Owner | Due | Trigger |")
        a("|---|---|---|---|")
        for _, r in actions.iterrows():
            a(f"| {r['action']} | {r['owner']} | {r['due']} | "
              f"{r['metric']} ({_RAG_BADGE.get(r['rag'], r['rag'])}) |")
    a("")
    a("---")
    a("")


def build_markdown_report(
    dq: pd.DataFrame,
    hhi: pd.DataFrame,
    co_industry: pd.DataFrame,
    co_vintage: pd.DataFrame,
    early_warning: pd.DataFrame,
    stage_proxy: pd.DataFrame,
    problem_exposure: pd.DataFrame | None = None,
    appetite: pd.DataFrame | None = None,
    appetite_actions: pd.DataFrame | None = None,
) -> str:
    """Assemble a short monitoring-pack report (Markdown) from key tables.

    The optional args (CML-1/CML-3) keep existing callers/tests working:
    *problem_exposure* adds the pre-charge-off early-warning layer, and
    *appetite* / *appetite_actions* lead the pack with the board RAG dashboard.
    """
    lines: list[str] = []
    a = lines.append

    a("# Commercial Portfolio Monitoring Pack — SBA 7(a)")
    a("")
    a("_Real public SBA 7(a) loan-level data. Monitoring outputs only — not a "
      "regulated disclosure. Any APS 330-style table below is laid out in that "
      "format for familiarity and is labelled accordingly._")
    a("")

    if appetite is not None and not appetite.empty:
        _render_dashboard(a, appetite, appetite_actions)

    a("## 1. Portfolio at a glance")
    a("")
    a("| Metric | Value |")
    a("|---|---|")
    for _, r in dq.iterrows():
        a(f"| {r['metric']} | {r['value']} |")
    a("")

    a("## 2. Concentration (HHI + top-N exposure share)")
    a("")
    share_col = [c for c in hhi.columns if c.startswith("top")][0]
    a(f"| Dimension | Segments | HHI | Level | {share_col} |")
    a("|---|---|---|---|---|")
    for _, r in hhi.iterrows():
        a(f"| {r['dimension']} | {r['segments']} | {r['hhi']:.4f} | "
          f"{r['concentration_level']} | {_fmt_pct(r[share_col])} |")
    a("")
    a("> HHI = sum of squared segment shares (0 = diversified, 1 = fully concentrated).")
    a("")

    a("## 3. Charge-off rates by industry (worst 8)")
    a("")
    a("| Industry | Loans | Charge-off rate (count) | Charge-off rate ($) |")
    a("|---|---|---|---|")
    for _, r in co_industry.head(8).iterrows():
        a(f"| {r['industry']} | {int(r['loan_count']):,} | "
          f"{_fmt_pct(r['chargeoff_rate_count'])} | {_fmt_pct(r['chargeoff_rate_dollar'])} |")
    a("")

    a("## 4. Charge-off rate by vintage (approval-year cohort)")
    a("")
    a("> **Default-definition note (APS 220 para 79).** Default here is "
      "`LoanStatus == CHGOFF` — a *realised, lagging* write-off point. APS 220's "
      "reference default is earlier (90+ days past due / unlikely-to-pay), so "
      "this rate **understates** how many loans have already breached the "
      "reference-default point. The pre-charge-off problem-exposure layer "
      "(section 5b) is the SBA-feasible *leading* view; `IN LIQUIDATION` in "
      "particular is a near-certain future charge-off.")
    a("")
    a("| Vintage | Loans | Charge-off rate (count) | Fully seasoned |")
    a("|---|---|---|---|")
    for _, r in co_vintage.iterrows():
        a(f"| {int(r['vintage'])} | {int(r['loan_count']):,} | "
          f"{_fmt_pct(r['chargeoff_rate_count'])} | {'yes' if r['fully_seasoned'] else 'no (under-reports)'} |")
    a("")

    a("## 5. Early-warning segments (industry x vintage x size)")
    a("")
    if early_warning.empty:
        a("_No segments exceeded the elevated-risk threshold._")
    else:
        a("| Industry | Vintage | Size band | Loans | Charge-off rate | x Portfolio | Severity |")
        a("|---|---|---|---|---|---|---|")
        for _, r in early_warning.head(15).iterrows():
            a(f"| {r['industry']} | {int(r['vintage'])} | {r['size_band']} | "
              f"{int(r['loan_count']):,} | {_fmt_pct(r['chargeoff_rate'])} | "
              f"{r['rate_multiple']:.1f}x | {r['severity']} |")
    a("")

    if problem_exposure is not None and not problem_exposure.empty:
        a("## 5b. Problem-exposure layer (pre-charge-off early warning)")
        a("")
        a("_APS 220 para 79 / APG 220 para 66 — act early on **problem "
          "exposures** using **forward-looking** signals. These statuses are "
          "**not** counted as default (default = charge-off), but they are the "
          "pipeline that precedes charge-off. `IN LIQUIDATION` is a near-certain "
          "future charge-off — a leading signal._")
        a("")
        a("| Status | Meaning | Loans | Exposure ($) | Share of book ($) | Signal |")
        a("|---|---|---|---|---|---|")
        for _, r in problem_exposure.iterrows():
            bold = r["status"] == "ALL_PROBLEM"
            label = f"**{r['status_label']}**" if bold else r["status_label"]
            a(f"| {r['status']} | {label} | {int(r['loan_count']):,} | "
              f"{_fmt_money(r['exposure'])} | {_fmt_pct(r['exposure_share'])} | "
              f"{r['signal']} |")
        a("")

    a("## 6. Stage proxy (performing vs defaulted)")
    a("")
    a("_Coarse split only — a proxy, not IFRS 9 staging. Full staging and "
      "transition matrices live in the companion Freddie Mac monitor._")
    a("")
    a("| Proxy stage | Loans | Exposure ($) | Exposure share |")
    a("|---|---|---|---|")
    for _, r in stage_proxy.iterrows():
        a(f"| {r['proxy_stage']} | {int(r['loan_count']):,} | "
          f"{r['exposure']:,.0f} | {_fmt_pct(r['exposure_share'])} |")
    a("")

    if appetite is not None and not appetite.empty:
        a("## 7. Risk appetite & limit register (full)")
        a("")
        a("_APS 220 para 20 (appetite statement) + para 35 (concentration "
          "limits — industry, geography, single name / lender). The board "
          "dashboard at the top reports live RAG against these limits._")
        a("")
        a("| Metric | Value | Amber | Red | RAG | Owner | Breach action | Review |")
        a("|---|---|---|---|---|---|---|---|")
        for _, r in appetite.iterrows():
            basis = r["basis"]
            a(f"| {r['metric']} | {_fmt_limit_value(basis, r['value'])} | "
              f"{_fmt_limit_value(basis, r['amber'])} | {_fmt_limit_value(basis, r['red'])} | "
              f"{_RAG_BADGE.get(r['rag'], r['rag'])} | {r['owner']} | "
              f"{r['breach_action']} | {r['review_cycle']} |")
        a("")

    a("---")
    a("")
    a("_Generated by the commercial-portfolio-monitor pipeline. Data source: "
      "U.S. Small Business Administration 7(a) FOIA loan-level dataset "
      "(data.sba.gov), public domain._")
    return "\n".join(lines)
