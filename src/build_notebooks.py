"""Generate and execute the SBA monitoring notebooks 00-05.

Run from the repo root:  python -m src.build_notebooks
Each notebook is self-contained, opens with a plain-English summary, and saves
one clean results table to outputs/. This script (re)builds them from source so
they always match the current src/ code, then executes them with real data.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"

# Shared first code cell: make `src` importable regardless of CWD.
BOOTSTRAP = (
    "%matplotlib inline\n"
    "import sys, warnings\n"
    "from pathlib import Path\n"
    "warnings.filterwarnings('ignore')\n"
    "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
    "sys.path.insert(0, str(ROOT))\n"
    "import pandas as pd\n"
    "pd.set_option('display.max_columns', 40, 'display.width', 200)\n"
    "from src.config import load_config, TABLES_DIR\n"
    "CFG = load_config()"
)

LOAD_BASE = (
    "from src.data_loader import load_clean\n"
    "from src.base_table import build_base_table\n"
    "loans = load_clean(config=CFG)\n"
    "base = build_base_table(loans, config=CFG)\n"
    "print(f'{len(base):,} funded loans, vintages "
    "{int(base.vintage.min())}-{int(base.vintage.max())}')"
)


def md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(text)


def code(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(text)


def notebook(cells: list) -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    return nb


# --------------------------------------------------------------------------- #
# 00 — Load & clean                                                           #
# --------------------------------------------------------------------------- #
nb00 = notebook([
    md("# 00 — Load & clean the SBA 7(a) data\n\n"
       "**Plain English:** We read the real U.S. Small Business Administration "
       "7(a) loan files, tidy them up, and check the data looks sensible before "
       "any analysis.\n\n"
       "Each row is one approved small-business loan. We:\n"
       "- parse the dates (approval, paid-in-full, charge-off),\n"
       "- standardise the `LoanStatus` codes (e.g. `P I F` = *paid in full*, "
       "`CHGOFF` = *charged off / defaulted*),\n"
       "- map each loan's 6-digit NAICS code to a plain industry name, and\n"
       "- drop loans that were cancelled or only committed (they never funded, "
       "so they carry no real exposure).\n\n"
       "**Key term — charge-off:** when a lender writes a loan off as a loss. "
       "We treat charge-off as *default* throughout this project."),
    code(BOOTSTRAP),
    code("from src.data_loader import load_clean, data_quality_summary\n"
         "loans = load_clean(config=CFG)\n"
         "loans.shape"),
    md("### Result: data-quality / coverage summary\n"
       "One row per check. This is the table we save for this notebook."),
    code("dq = data_quality_summary(loans, config=CFG)\n"
         "dq.to_csv(TABLES_DIR / '00_data_quality_summary.csv', index=False)\n"
         "dq"),
    md("**Read-out:** ~1.09M funded 7(a) loans, fiscal years 2000–2019. The "
       "overall charge-off rate is ~12% by loan count but only ~5% by dollars — "
       "larger loans default less often, a pattern we quantify in notebook 03."),
])

# --------------------------------------------------------------------------- #
# 01 — Monitoring base table                                                  #
# --------------------------------------------------------------------------- #
nb01 = notebook([
    md("# 01 — Monitoring base table\n\n"
       "**Plain English:** We turn the cleaned loans into one tidy table with a "
       "few extra columns that every later notebook reuses:\n\n"
       "- **vintage** — the approval-year cohort (which year the loan was made),\n"
       "- **is_default** — `True` if the loan was charged off,\n"
       "- **size_band** — the loan grouped into a dollar-size bucket,\n"
       "- **months_to_chargeoff** — for defaulted loans, how many months after "
       "approval the charge-off happened (charge-off date − approval date),\n"
       "- **fully_seasoned** — `True` for older vintages whose outcomes are "
       "essentially final; recent vintages still have loans that may yet fail."),
    code(BOOTSTRAP),
    code(LOAD_BASE),
    md("### Result: base-table schema + a sample\n"
       "The derived fields are on the right. We save the first 500 rows as a "
       "lightweight, committable sample (the full table is ~1M rows)."),
    code("cols = ['vintage','grossapproval','size_band','naics_sector','borrstate',\n"
         "        'loanstatus','is_default','months_to_chargeoff','fully_seasoned']\n"
         "sample = base[cols].head(500)\n"
         "sample.to_csv(TABLES_DIR / '01_base_table_sample.csv', index=False)\n"
         "base[cols].head(10)"),
    md("**Read-out:** every downstream view — concentration, charge-off rates, "
       "vintage curves, early warning — is a `groupby` on this one table."),
])

# --------------------------------------------------------------------------- #
# 02 — Concentration                                                          #
# --------------------------------------------------------------------------- #
nb02 = notebook([
    md("# 02 — Concentration risk\n\n"
       "**Plain English:** *Concentration* asks \"are we putting too many eggs "
       "in one basket?\" We measure how exposure (total gross approval $) spreads "
       "across **industries**, **states**, **originating lenders** (the channel) "
       "and **borrowers** (single-name / franchise brands).\n\n"
       "Two standard measures:\n"
       "- **Top-N share** — the % of the book held by the largest N segments.\n"
       "- **HHI (Herfindahl–Hirschman Index)** — the sum of squared segment "
       "shares. 0 = perfectly diversified, 1.0 = everything in one segment; "
       "higher = more concentrated."),
    code(BOOTSTRAP),
    code(LOAD_BASE),
    code("from src import concentration as conc\n"
         "from src.charts import plot_concentration_bar\n"
         "hhi = conc.hhi_summary(base)\n"
         "hhi.to_csv(TABLES_DIR / '02_concentration_hhi_summary.csv', index=False)\n"
         "ind = conc.concentration_by(base, 'industry')\n"
         "st = conc.concentration_by(base, 'state')\n"
         "ld = conc.concentration_by(base, 'lender')\n"
         "bo = conc.concentration_by(base, 'borrower')\n"
         "ind.to_csv(TABLES_DIR / '02_concentration_industry.csv', index=False)\n"
         "st.to_csv(TABLES_DIR / '02_concentration_state.csv', index=False)\n"
         "ld.to_csv(TABLES_DIR / '02_concentration_lender.csv', index=False)\n"
         "bo.to_csv(TABLES_DIR / '02_concentration_borrower.csv', index=False)"),
    md("### Result: HHI + top-N exposure share by dimension"),
    code("hhi"),
    md("#### Top industries by exposure (with each segment's charge-off rate)"),
    code("ind"),
    code("plot_concentration_bar(ind, 'industry', 'Exposure concentration by industry (NAICS sector)')"),
    md("**Read-out:** the book is **moderately** concentrated by industry "
       "(HHI ≈ 0.10) but **well diversified** across states, the 4,000+ "
       "originating lenders and >900k borrowers (single-name share is immaterial — "
       "the largest names are franchise brands, a correlated-cluster to watch). "
       "Industry is the dimension worth watching."),
])

# --------------------------------------------------------------------------- #
# 03 — Charge-off & vintage cohorts                                           #
# --------------------------------------------------------------------------- #
nb03 = notebook([
    md("# 03 — Charge-off rates & vintage cohort curves\n\n"
       "**Plain English:** Now we look at *who defaults*. The **charge-off rate** "
       "is charged-off loans ÷ total loans in a segment. We break it down by "
       "industry, loan-size band, and **vintage** (approval-year cohort).\n\n"
       "Then we build **vintage cohort curves**: for each approval-year, the "
       "cumulative charge-off rate as the loans age (months since approval). This "
       "is the classic credit-risk view of how cohorts season.\n\n"
       "**Seasoning caveat:** recent vintages haven't had time to fully default, "
       "so their rates understate the eventual total — we flag those."),
    code(BOOTSTRAP),
    code(LOAD_BASE),
    code("from src import chargeoff as co, vintage\n"
         "from src.charts import plot_chargeoff_by_vintage, plot_vintage_curves, plot_chargeoff_bar\n"
         "co_ind = co.chargeoff_by_industry(base)\n"
         "co_size = co.chargeoff_by_size_band(base)\n"
         "co_vin = co.chargeoff_by_vintage(base)\n"
         "curves = vintage.compute_vintage_curves(base, config=CFG)\n"
         "co_ind.to_csv(TABLES_DIR / '03_chargeoff_by_industry.csv', index=False)\n"
         "co_size.to_csv(TABLES_DIR / '03_chargeoff_by_size_band.csv', index=False)\n"
         "co_vin.to_csv(TABLES_DIR / '03_chargeoff_by_vintage.csv', index=False)\n"
         "curves.reset_index().to_csv(TABLES_DIR / '03_vintage_cohort_curves.csv', index=False)"),
    md("### Result: charge-off rate by vintage\n"
       "Watch the 2005–2008 cohorts — loans made into the financial crisis."),
    code("co_vin"),
    code("plot_chargeoff_by_vintage(co_vin)"),
    md("#### Charge-off rate by loan-size band\n"
       "Smaller loans default markedly more often."),
    code("co_size"),
    md("#### Vintage cohort curves — cumulative charge-off rate vs loan age"),
    code("plot_vintage_curves(curves)"),
    md("**Read-out:** the 2006–2008 vintages charged off at ~24–29% — roughly "
       "**5× the calm-year cohorts** — and their curves sit far above the rest. "
       "Smaller loans (≤\\$50k) default ~16% vs ~3% for loans over \\$2m."),
])

# --------------------------------------------------------------------------- #
# 04 — Loan-age transitions & early warning                                   #
# --------------------------------------------------------------------------- #
nb04 = notebook([
    md("# 04 — Loan-age transitions & early-warning segments\n\n"
       "**Plain English:** Two monitoring views.\n\n"
       "**Loan-age transition view** — *when* do charge-offs happen? SBA data is "
       "outcome-level (one final status per loan), not a monthly grade panel, so "
       "a true monthly migration matrix isn't possible here (that lives in the "
       "companion Freddie Mac monitor). The feasible substitute: bucket charge-offs "
       "by the loan age at which they occurred.\n\n"
       "**Early-warning segmentation** — which **industry × vintage × size** "
       "segments are charging off well above the portfolio average? We only flag "
       "segments large enough to be meaningful, so one unlucky loan can't trip it."),
    code(BOOTSTRAP),
    code(LOAD_BASE),
    code("from src import transitions\n"
         "from src.early_warning import flag_high_risk_segments\n"
         "from src.charts import plot_loan_age_transition\n"
         "age = transitions.loan_age_transition(base)\n"
         "ew = flag_high_risk_segments(base, config=CFG)\n"
         "age.to_csv(TABLES_DIR / '04_loan_age_transitions.csv', index=False)\n"
         "ew.to_csv(TABLES_DIR / '04_early_warning_segments.csv', index=False)"),
    md("### Result: when charge-offs occur, by loan age (seasoned vintages)"),
    code("age"),
    code("plot_loan_age_transition(age)"),
    md("#### Early-warning segments — worst 15 by multiple of portfolio rate"),
    code("ew.head(15)"),
    md("**Read-out:** most charge-offs land in the **2–5 year** window after "
       "approval (early-life defaults are rare, then risk peaks). The flagged "
       "segments are dominated by **2007–2008 crisis vintages in small loans** "
       "across wholesale, real estate and finance — exactly where you'd tighten."),
])

# --------------------------------------------------------------------------- #
# 05 — Monitoring pack / report                                               #
# --------------------------------------------------------------------------- #
nb05 = notebook([
    md("# 05 — Monitoring pack / report\n\n"
       "**Plain English:** We pull the key tables together into a short, "
       "disclosure-style monitoring pack and write it to `outputs/reports/report.md`.\n\n"
       "Includes a 3-stage **IFRS 9-style proxy** (Stage 1 performing / Stage 2 "
       "problem-exposure / Stage 3 charged-off) and a credit-quality table laid "
       "out in **APS 330-style disclosure format**.\n\n"
       "> ⚠️ **Labelling:** these are *monitoring outputs on public SBA data*, "
       "not a regulated entity's disclosure. The APS 330 layout is used for "
       "familiarity only. Full IFRS 9 staging and transition matrices live in "
       "the companion Freddie Mac monitor."),
    code(BOOTSTRAP),
    code(LOAD_BASE),
    code("from src import report as rpt, concentration as conc, chargeoff as co\n"
         "from src.data_loader import load_clean, data_quality_summary\n"
         "from src.early_warning import flag_high_risk_segments\n"
         "dq = data_quality_summary(base, config=CFG)\n"
         "stage = rpt.stage_proxy_summary(base, config=CFG)\n"
         "aps = rpt.aps330_style_credit_quality(base)\n"
         "stage.to_csv(TABLES_DIR / '05_stage_proxy_summary.csv', index=False)\n"
         "aps.to_csv(TABLES_DIR / '05_aps330_style_credit_quality.csv', index=False)"),
    md("### Result: 3-stage IFRS 9-style proxy (Stage 1 / 2 / 3)"),
    code("stage"),
    md("#### APS 330-style credit-quality by industry *(format only — not a regulatory disclosure)*"),
    code("aps.head(12)"),
    md("#### Assemble and write the full Markdown report"),
    code("md_report = rpt.build_markdown_report(\n"
         "    dq=dq, hhi=conc.hhi_summary(base),\n"
         "    co_industry=co.chargeoff_by_industry(base),\n"
         "    co_vintage=co.chargeoff_by_vintage(base),\n"
         "    early_warning=flag_high_risk_segments(base, config=CFG),\n"
         "    stage_proxy=stage,\n"
         ")\n"
         "(ROOT / 'outputs' / 'reports').mkdir(parents=True, exist_ok=True)\n"
         "(ROOT / 'outputs' / 'reports' / 'report.md').write_text(md_report, encoding='utf-8')\n"
         "print(md_report[:1200])"),
    md("**Read-out:** `outputs/reports/report.md` is the one-page pack a credit committee "
       "would skim — portfolio size, concentration, worst industries/vintages, "
       "flagged segments, and the Stage 1/2/3 split."),
])

NOTEBOOKS = {
    "00_load_and_clean.ipynb": nb00,
    "01_monitoring_base_table.ipynb": nb01,
    "02_concentration.ipynb": nb02,
    "03_chargeoff_and_vintage.ipynb": nb03,
    "04_transitions_and_early_warning.ipynb": nb04,
    "05_monitoring_report.ipynb": nb05,
}


def main() -> None:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    for name, nb in NOTEBOOKS.items():
        path = NB_DIR / name
        nbf.write(nb, path)
        print(f"Writing + executing {name} ...")
        ep.preprocess(nb, {"metadata": {"path": str(NB_DIR)}})
        nbf.write(nb, path)
        print(f"  done -> {path}")
    print("All notebooks built and executed.")


if __name__ == "__main__":
    main()
