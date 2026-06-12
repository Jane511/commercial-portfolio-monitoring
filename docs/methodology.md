# Methodology

A plain-English walk through how each output is computed. Everything is a
pandas aggregation on the base table (`src/base_table.py`); no ML, no opaque
steps.

## 1. Universe

Start from the two SBA 7(a) FOIA extracts (FY2000–2019). Drop `CANCLD` and
`COMMIT` loans — they never funded, so they carry no exposure and would
understate charge-off rates. What remains (~1.09M loans) is the monitored book.

## 2. Concentration

For each dimension (industry = NAICS sector, state, lender):

- **Exposure share** of a segment = segment gross approval ÷ total gross approval.
- **Top-N share** = combined exposure share of the largest N segments.
- **HHI** = Σ(segment share²) across all segments. Classified via `config.yaml`
  thresholds: `< 0.10` Low, `0.10–0.18` Moderate, `≥ 0.18` High.

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

A coarse two-way split — performing vs charged-off — labelled explicitly as a
**proxy**, not IFRS 9 staging. An APS 330-style credit-quality-by-industry table
is produced in that **format only** (clearly labelled, not a regulatory
disclosure). `src/report.py` assembles the key tables into `outputs/report.md`.

## Seasoning

Vintages after `universe.fully_seasoned_max_fy` (default 2015) are still shown
but flagged `fully_seasoned = False`: their loans haven't all had time to fail,
so their charge-off rates understate the eventual total. Rate-by-segment and
early-warning analyses restrict to seasoned vintages to keep comparisons fair.
