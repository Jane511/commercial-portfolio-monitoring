# Assumptions & limitations

Stated plainly so a reviewer knows exactly what this project does and does not claim.

## Definitions

- **Default = charge-off only** (`LoanStatus == CHGOFF`). Loans `IN LIQUIDATION`,
  `DELINQ`, or `PSTDUE` are *not* counted as default — they have no booked
  charge-off. This is a deliberately conservative, outcome-based definition.
- **Performing** = everything funded that is not charged off (paid in full,
  current, purchased-not-charged-off, etc.).
- **Exposure** is `grossapproval` (amount approved), not a point-in-time
  outstanding balance — SBA FOIA data does not provide an amortising balance, so
  concentration and dollar rates are measured at approval.

## Data scope

- **7(a) program only.** The 504 dataset is not loaded in this build (the loader
  will pick it up automatically if added to `data/input/`).
- **FY2000–2019.** All vintages are shown; those after 2015 are flagged as not
  fully seasoned and excluded from rate-based comparisons.
- A small number of charged-off loans (~13) have no charge-off date; they count
  toward charge-off totals but are excluded from age-based curves where the date
  is required.
- ~1.5% of loans have a missing/unclassifiable NAICS code → grouped as
  "Unknown / Unclassified" rather than dropped.

## What this is NOT

- **Not IFRS 9 / AASB 9 staging.** SBA is outcome-level, not a monthly grade
  panel, so only a coarse performing-vs-defaulted proxy is possible. Full
  staging, monthly transition matrices, roll rates and ECL live in the companion
  **Freddie Mac mortgage monitor**. The stage proxy here is labelled as such.
- **Not a regulatory disclosure.** The APS 330-style table is laid out in that
  format for familiarity only; it is built from public SBA data and is labelled
  "APS 330-style disclosure format," not regulated output.
- **Not credit advice or a forward-looking forecast.** These are descriptive
  monitoring views of historical, realised outcomes.

## Seasoning / survivorship

Cumulative charge-off curves are capped at each cohort's observable horizon so
immature cohorts are never shown with a deceptively low "final" rate. Even so,
the most recent vintages should be read as lower bounds on ultimate losses.
