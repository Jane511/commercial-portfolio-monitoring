# PROJECT BUILD — Commercial Portfolio Monitor (SBA real data)

**For:** Claude Code
**Repo:** the existing `portfolio-monitor-commercial` (replace synthetic data with real SBA data)
**Dataset:** U.S. Small Business Administration (SBA) 7(a) and 504 loan-level data — real,
public, **commercial** small-business lending.

This converts the existing synthetic repo into a real-data commercial monitoring project.
Its strength is **concentration and charge-off cohort analytics on genuine commercial loans**.
The full monthly transition/staging mechanics live in the companion Freddie Mac monitor — keep
that boundary; don't duplicate it here.

---

## 0. Golden rules
- **Real public data only.** No synthetic data, no proprietary sources.
- **Self-contained.** Real loan data in → monitoring outputs out. No references to non-existent
  upstream repos.
- **Keep it simple and interpretable.** Pandas + clear aggregations; no heavy ML.
- **HR-friendly.** Plain-English summary at the top of each notebook; explain any term in one line.
- **One clean results table per notebook**, saved to `outputs/`.
- If anything is ambiguous, ask me one question.

## 1. Data — SBA loan-level
- Source: SBA open data (data.sba.gov) — the **7(a) FOIA** and **504 FOIA** loan datasets (CSV).
- Download a manageable slice (e.g. approval years ~2000–2015, fully seasoned so outcomes are known).
- Key fields to use: `GrossApproval` (loan amount), `ApprovalDate` / `ApprovalFiscalYear`,
  `NaicsCode` + `NaicsDescription` (industry), `BorrState` / `ProjectState`, `TermInMonths`,
  `LoanStatus` (e.g. PIF = paid in full, CHGOFF = charged off), `ChargeOffDate`,
  `GrossChargeOffAmount`, `JobsSupported`, lender fields.
- **Compliance:** SBA data is public/government — fine to use. Still gitignore the large raw CSVs;
  commit only small output snapshots, charts, and the report.

## 2. Key definitions (state each in plain English in the notebook)
- **Default = charge-off** (`LoanStatus == CHGOFF`). Performing = paid in full or still current.
- **Charge-off rate** = charged-off count (or $) ÷ total in the segment.
- **Vintage** = approval-year cohort.
- **Concentration measures:** top-N share and **HHI** (Herfindahl–Hirschman Index — sum of squared
  segment shares; higher = more concentrated). Define HHI in one line.
- **Staging note:** SBA is outcome-level, not a monthly grade panel, so only a coarse
  performing-vs-defaulted split is possible here. Say so, and point to the Freddie Mac monitor for
  full IFRS 9 staging and transition matrices.

## 3. What it produces (monitoring outputs on real commercial data)
- Concentration: exposure and count by **industry (NAICS)**, by state, by lender; with top-N share
  and HHI.
- Charge-off rates by industry, by loan-size band, by vintage.
- **Vintage cohort curves:** cumulative charge-off rate by months-since-approval per approval-year
  cohort (uses ChargeOffDate − ApprovalDate).
- **Loan-age status transition view:** share performing vs charged-off by loan age (the SBA-feasible
  substitute for a monthly migration matrix).
- **Early-warning segmentation:** flag high-risk segments (industry × vintage × size) by elevated
  charge-off rate vs the portfolio average.
- (Optional) a simple performing/defaulted stage summary, clearly labelled a proxy.

## 4. Build steps (notebooks)
- **00 — Load & clean:** read SBA CSVs, clean `LoanStatus` codes, parse dates, map NAICS to industry
  names, basic data-quality summary (row counts, charge-off rate overall).
- **01 — Monitoring base table:** one row per loan + derived fields (vintage, loan age at charge-off,
  size band, default flag).
- **02 — Concentration:** by industry/state/lender, top-N share, HHI + charts.
- **03 — Charge-off & vintage cohorts:** charge-off rates by segment; cumulative cohort curves + charts.
- **04 — Loan-age transitions & early warning:** status by loan age; high-risk segment flags.
- **05 — Monitoring pack / report:** a short disclosure-style report (md/html) pulling the key tables;
  any APS 330-style table labelled "APS 330-style disclosure format," not regulatory disclosure.

## 5. Repo practices
- gitignore raw SBA data; commit output snapshots + charts + report.
- README: a "See it in 30 seconds" link block; a "What this produces" section with sample tables +
  one chart read from real outputs; a "Data sources & provenance" section (real public SBA data);
  a "Related projects" section cross-linking the mortgage repo and the companion Freddie Mac monitor.
- Remove the `synthetic-data` GitHub topic; add topics like `commercial-lending`, `concentration-risk`,
  `portfolio-monitoring`, `credit-risk`.
- Remove all references to non-existent upstream stack repos.

## 6. One-line message (for the README)
> Commercial portfolio monitoring on real SBA small-business loan data — industry/state concentration
> (HHI, top-N), charge-off rates and vintage cohort curves, and early-warning segmentation.
