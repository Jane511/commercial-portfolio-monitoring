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
    leading_map: pd.DataFrame | None = None,
    origination: pd.DataFrame | None = None,
    vov_early_mob: pd.DataFrame | None = None,
    stress: pd.DataFrame | None = None,
    credit_params: pd.DataFrame | None = None,
    credit_params_size: pd.DataFrame | None = None,
    credit_params_product: pd.DataFrame | None = None,
    credit_params_structure: pd.DataFrame | None = None,
) -> str:
    """Assemble a short monitoring-pack report (Markdown) from key tables.

    The optional args keep existing callers/tests working: *problem_exposure*
    adds the pre-charge-off early-warning layer, *appetite* / *appetite_actions*
    lead the pack with the board RAG dashboard, *leading_map* / *origination* /
    *vov_early_mob* add the leading-vs-lagging framing and the two leading views,
    and *credit_params* / *credit_params_size* add the empirical PD/LGD/EAD/EL
    parameter block used as deal-pricing and ECL/RWA assumption inputs.
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

    if leading_map is not None and not leading_map.empty:
        a("## 8. Leading vs lagging — framing & leading views")
        a("")
        a("_APG 220 para 66 — favour **forward-looking** signals. SBA is "
          "outcome-level, so most metrics here are lagging by nature; the table "
          "is explicit about which is which, and the two leading views below "
          "are the forward signals the data still supports._")
        a("")
        a("| Metric | Type | Rationale |")
        a("|---|---|---|")
        for _, r in leading_map.iterrows():
            a(f"| {r['metric']} | {r['type']} | {r['rationale']} |")
        a("")

        if origination is not None and not origination.empty:
            a("**8a. Origination volume & mix trend by approval year (leading).** "
              "A swing into higher-charge-off sectors or larger tickets leads the "
              "future book charge-off rate. Most recent 8 cohorts:")
            a("")
            a("| Approval FY | Loans | Exposure ($) | YoY growth | Top sector | "
              "Top-sector share | Large-ticket share |")
            a("|---|---|---|---|---|---|---|")
            for _, r in origination.tail(8).iterrows():
                yoy = _fmt_pct(r["exposure_yoy_growth"]) if pd.notna(r["exposure_yoy_growth"]) else "—"
                a(f"| {int(r['vintage'])} | {int(r['loans_originated']):,} | "
                  f"{_fmt_money(r['exposure'])} | {yoy} | {r['top_sector']} | "
                  f"{_fmt_pct(r['top_sector_share'])} | {_fmt_pct(r['large_ticket_share'])} |")
            a("")

        if vov_early_mob is not None and not vov_early_mob.empty:
            ref = int(vov_early_mob["reference_mob"].iloc[0])
            a(f"**8b. Vintage-over-vintage early-MOB charge-off ({ref}m, leading).** "
              "Is a young cohort charging off faster than its predecessor did at "
              "the same age? A ratio > 1 is a forward deterioration signal:")
            a("")
            a(f"| Vintage | Charge-off @ {ref}m | Prior vintage @ {ref}m | VoV ratio |")
            a("|---|---|---|---|")
            for _, r in vov_early_mob.iterrows():
                prior = _fmt_pct(r["prior_vintage_rate"]) if pd.notna(r["prior_vintage_rate"]) else "—"
                ratio = f"{r['vintage_over_vintage_ratio']:.2f}x" if pd.notna(r["vintage_over_vintage_ratio"]) else "—"
                a(f"| {int(r['vintage'])} | {_fmt_pct(r['early_mob_chargeoff'])} | "
                  f"{prior} | {ratio} |")
            a("")

    if stress is not None and not stress.empty:
        breached = bool(stress["breaches_appetite"].any())
        a("## 9. Stress scenario — crisis multiplier vs the charge-off limit")
        a("")
        a("_APS 220 para 73 / APG 220 para 76. The financial-crisis cohorts "
          "(2006-08) charged off well above the book average; that multiplier is "
          "applied to the current portfolio charge-off rate and re-tested against "
          "the appetite limit. The linkage is the point: a stressed breach "
          "triggers the charge-off-rate limit's breach action (tighter "
          "origination / pricing), per the dashboard._")
        a("")
        a("| Scenario | Charge-off rate | RAG vs limit | Implied charge-off ($) | Additional vs baseline ($) |")
        a("|---|---|---|---|---|")
        for _, r in stress.iterrows():
            add = _fmt_money(r["additional_vs_baseline"]) if pd.notna(r["additional_vs_baseline"]) else "—"
            a(f"| {r['scenario']} | {_fmt_pct(r['chargeoff_rate'])} | "
              f"{_RAG_BADGE.get(r['rag_vs_limit'], r['rag_vs_limit'])} | "
              f"{_fmt_money(r['implied_chargeoff_exposure'])} | {add} |")
        a("")
        if breached:
            a("> **Stress breaches appetite** → escalate to the charge-off-rate "
              "limit owner; review origination credit policy and pricing (see "
              "the dashboard actions table).")
        else:
            a("> Stressed rate stays within appetite — no escalation triggered, "
              "but the headroom is monitored.")
        a("")

    if credit_params is not None and not credit_params.empty:
        p = credit_params.iloc[0]
        a("## 10. Credit-risk parameters (PD / LGD / EAD / EL) — pricing & ECL inputs")
        a("")
        a("_Realised, **through-the-cycle** parameters read off the FY2000-2019 "
          "outcome data — the loss-experience anchors a deal-pricing or ECL/RWA "
          "model is calibrated against. These are **observed**, not model "
          "outputs: no obligor-level rating model lives here (default is an "
          "actual status). Identity check: EL rate = PD($) x LGD._")
        a("")
        a("| Parameter | Definition | Portfolio average |")
        a("|---|---|---|")
        a(f"| **PD** — probability of default (obligor-weighted) | charged-off "
          f"loans / funded loans | {_fmt_pct(p['pd_count'])} |")
        a(f"| **PD** — exposure-weighted ($) | defaulted EAD / total EAD | "
          f"{_fmt_pct(p['pd_dollar'])} |")
        a(f"| **LGD** — loss given default (gross, whole-loan) | charge-off $ / "
          f"defaulted EAD | {_fmt_pct(p['lgd'])} |")
        a(f"| **LGD** — net of SBA guarantee (indicative, lender-retained) | "
          f"LGD x (1 - guaranteed share) | {_fmt_pct(p['lgd_net_of_guarantee'])} |")
        a(f"| **EAD** — exposure at default (avg per loan) | gross approval | "
          f"{_fmt_money(p['ead_avg'])} |")
        a(f"| **EAD** — avg per *defaulted* loan | gross approval of defaults | "
          f"{_fmt_money(p['ead_avg_defaulted'])} |")
        a(f"| **EL rate** — expected loss / exposure | PD($) x LGD = charge-off "
          f"$ / total EAD | {_fmt_pct(p['el_rate'])} |")
        a(f"| **EL** — expected loss per loan (avg) | charge-off $ / funded "
          f"loans | {_fmt_money(p['el_per_loan'])} |")
        a(f"| _SBA guaranteed share_ | guaranteed $ / gross approval | "
          f"{_fmt_pct(p['guarantee_ratio'])} |")
        a("")
        a("> **Reading note.** The obligor-weighted PD (12%+) pairs with the "
          "*defaulted-loan* EAD, not the book-average EAD — defaulters skew "
          "smaller, so the exposure-weighted PD($) is lower. For an "
          "exposure-based EL, use `EL rate = PD($) x LGD`; for a per-account "
          "EL, use the EL-per-loan figure.")
        a("")

        if credit_params_size is not None and not credit_params_size.empty:
            a("**10a. Risk-based parameters by loan-size band (for tiered "
              "pricing).** Small tickets default ~5x more often and lose more "
              "per dollar — the curve a risk-based price has to ride:")
            a("")
            a("| Size band | Loans | PD (count) | LGD | Avg EAD | EL rate |")
            a("|---|---|---|---|---|---|")
            for _, r in credit_params_size.iterrows():
                a(f"| {r['segment']} | {int(r['loan_count']):,} | "
                  f"{_fmt_pct(r['pd_count'])} | {_fmt_pct(r['lgd'])} | "
                  f"{_fmt_money(r['ead_avg'])} | {_fmt_pct(r['el_rate'])} |")
            a("")

        if credit_params_product is not None and not credit_params_product.empty:
            a("**10b. Parameters by product (facility type).** This is "
              "small-business lending throughout — the dataset has **no "
              "residential** mortgage product, and **no labelled commercial-"
              "property** field. Facility type is a *use-of-proceeds* read from "
              "the data: trade/export subprogram → trade finance; revolving flag "
              "→ working-capital line; loan term > 15y → real-estate purpose "
              "(only real estate carries SBA maturities that long — a labelled "
              "**proxy**); everything else → general SME term loan:")
            a("")
            a("| Product (facility type) | Loans | PD (count) | LGD | Avg EAD | EL rate |")
            a("|---|---|---|---|---|---|")
            for _, r in credit_params_product.iterrows():
                a(f"| {r['segment']} | {int(r['loan_count']):,} | "
                  f"{_fmt_pct(r['pd_count'])} | {_fmt_pct(r['lgd'])} | "
                  f"{_fmt_money(r['ead_avg'])} | {_fmt_pct(r['el_rate'])} |")
            a("")

        if credit_params_structure is not None and not credit_params_structure.empty:
            a("**10c. Parameters by loan structure & collateral.** Two more "
              "pricing-relevant cuts — term loan vs revolving line, and "
              "secured (collateralised — the PPSR-registered equivalent) vs "
              "unsecured:")
            a("")
            a("| Cut | Segment | Loans | PD (count) | LGD | Avg EAD | EL rate |")
            a("|---|---|---|---|---|---|---|")
            for _, r in credit_params_structure.iterrows():
                a(f"| {r['cut']} | {r['segment']} | {int(r['loan_count']):,} | "
                  f"{_fmt_pct(r['pd_count'])} | {_fmt_pct(r['lgd'])} | "
                  f"{_fmt_money(r['ead_avg'])} | {_fmt_pct(r['el_rate'])} |")
            a("")

    a("## Notes — APS 330 / Pillar 3 & governance")
    a("")
    a("- **APS 330 / Pillar 3 (CML-7).** The concentration (section 2) and "
      "credit-quality-by-industry outputs are the same primitives that feed a "
      "**Pillar 3 (APS 330) credit-risk disclosure**. The "
      "`05_aps330_style_credit_quality` table is laid out in that **format for "
      "familiarity only** — built from public SBA data, it is **not** a "
      "regulated entity's disclosure. In a bank these would be a *feeder* into "
      "the periodic Pillar 3 disclosure, not the disclosure itself.")
    a("- **Governance & validation.** Reporting cadence to forums, appetite "
      "ownership, and independent annual validation are documented in "
      "`docs/governance.md`. Section 10 extracts **realised** PD/LGD/EAD/EL as "
      "calibration inputs, but there is **no fitted rating model** in this repo "
      "(default is an observed status, not a model output), so the "
      "model-performance / backtesting layer is **N/A** — that lives in the "
      "sister modelling repos.")
    a("")
    a("---")
    a("")
    a("_Generated by the commercial-portfolio-monitor pipeline. Data source: "
      "U.S. Small Business Administration 7(a) FOIA loan-level dataset "
      "(data.sba.gov), public domain._")
    return "\n".join(lines)
