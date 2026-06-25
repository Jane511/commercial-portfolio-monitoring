# Methodology

A plain-English walk through how each output is computed. Everything is a
pandas aggregation on the base table (`src/base_table.py`); no ML, no opaque
steps.

## 1. Universe

Start from the two SBA 7(a) FOIA extracts (FY2000–2019). Drop `CANCLD` and
`COMMIT` loans — they never funded, so they carry no exposure and would
understate charge-off rates. What remains (~1.09M loans) is the monitored book.

## 2. Concentration

For each dimension (industry = NAICS sector, state, **originating lender**,
**borrower**):

- **Exposure share** of a segment = segment gross approval ÷ total gross approval.
- **Top-N share** = combined exposure share of the largest N segments.
- **HHI** = Σ(segment share²) across all segments. Classified via `config.yaml`
  thresholds: `< 0.10` Low, `0.10–0.18` Moderate, `≥ 0.18` High, with a
  `hhi_tolerance_band` so a marginal cross is a watch item, not a step-change.

`lender` is the **originating bank / channel** (third-party-originator reliance,
APS 220 para 39), distinct from `borrower`, which is single-name / franchise-brand
obligor concentration (APS 220 para 35(a); the top names are franchise brands —
correlated-obligor clusters per APG 220 para 77). **Originator performance**
(`originator_performance`) ranks material originating lenders by realised
charge-off rate, the third-party-oversight view.

## 3. Charge-off rates

For any segment:

- **Count rate** = charged-off loans ÷ loans in segment.
- **Dollar rate** = Σ`grosschargeoffamount` ÷ Σ`grossapproval` in segment.

Computed by industry, by loan-size band, and by vintage. The dollar rate runs
lower than the count rate because larger loans charge off less often.

## 4. Vintage cohort curves

For each approval-year cohort and each months-on-book (MOB) checkpoint *m*:

```
cumulative charge-off rate(m) = (loans charged off within m months) / (cohort size)
```

where months-on-book = `chargeoffdate − approvaldate`. A cohort is only shown
out to its **observable horizon** — the months elapsed between its most recent
approval and the data as-of date. Checkpoints beyond that are left blank (NaN)
so an immature cohort is never plotted as if its low rate were final.

## 5. Loan-age transition view

SBA is outcome-level, not a monthly grade panel, so a true monthly migration /
transition matrix is **not** possible here (it lives in the companion Freddie
Mac monitor). The feasible substitute: among fully-seasoned vintages, bucket
charge-offs by the loan age at which they occurred, and show the share and
cumulative share per age band. This reveals *when* commercial defaults happen.

## 6. Early-warning segmentation

Within fully-seasoned vintages, group by **industry × vintage × size band**.
Keep segments with at least `early_warning.min_segment_loans` loans (so a tiny
segment with one default can't trip a flag). Flag a segment when its charge-off
rate ≥ `elevated_multiple` × the portfolio average; mark "High" at
`high_multiple` ×. Output is sorted worst-first by the multiple.

## 7. Stage proxy & report

A **three-way** IFRS 9-style proxy split, labelled explicitly as a **proxy**, not
true IFRS 9 staging: **Stage 1** (performing), **Stage 2** (problem exposure /
SICR proxy — DELINQ / PSTDUE / LIQUID / PURCH(NOT C/O)), **Stage 3** (charged
off). Using the problem-exposure pipeline avoids lumping near-certain-loss loans
into "performing". An APS 330-style credit-quality-by-industry table is produced
in that **format only** (clearly labelled, not a regulatory disclosure).
`src/report.py` assembles the key tables into `outputs/reports/report.md`.

## 8. Non-performing (NPL) proxy

`is_nonperforming` = charge-off ∪ problem-exposure pipeline (DELINQ / PSTDUE /
LIQUID / PURCH(NOT C/O)). It is the closest SBA-feasible stand-in for the APS 220
reference default (90+DPD / unlikely-to-pay) and is reported beside the (narrower,
lagging) charge-off default — as a portfolio rate, an NPL appetite limit, and a
second PD basis in the parameter block.

## 9. Predictiveness validation

`src/validation.py` tests the claim that the "leading" indicators are actually
predictive (APG 113 para 140 element 3). Across fully-seasoned cohorts it
rank-correlates (Spearman) each early indicator — early-MOB charge-off rate,
large-ticket and top-sector origination share — with the cohort's **final**
charge-off rate. A positive correlation confirms the indicator ranks cohorts the
way their eventual losses do. (On the real data the early-MOB rate is strongly
predictive; the mix signals are weak — reported honestly either way.)

## 10. Stress ladder

`src/stress.py` runs four scenarios — baseline, adverse (historical 2006–08
crisis replay), severe (worst observed vintage) and a hypothetical forward
management overlay — each re-tested against **two** appetite limits: the
charge-off-rate limit and the dollar-EL-rate limit, so stressed LGD/EAD severity
is bounded by appetite, not just the count rate (APS 220 para 73; APG 220
paras 14/76).

## Seasoning

Vintages after `universe.fully_seasoned_max_fy` (default 2015) are still shown
but flagged `fully_seasoned = False`: their loans haven't all had time to fail,
so their charge-off rates understate the eventual total. Rate-by-segment and
early-warning analyses restrict to seasoned vintages to keep comparisons fair.
