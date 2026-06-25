# Assumptions & limitations

Stated plainly so a reviewer knows exactly what this project does and does not claim.

## Definitions

- **Default (realised) = charge-off only** (`LoanStatus == CHGOFF`). A
  deliberately conservative, outcome-based write-off point. It is **lagging**
  relative to the APS 220 reference default (90+DPD / unlikely-to-pay), so it
  understates how many loans ever breached.
- **Non-performing (NPL proxy)** = charge-off **plus** the problem-exposure
  pipeline `DELINQ` / `PSTDUE` / `LIQUID` / `PURCH(NOT C/O)` (`is_nonperforming`).
  This is the closest SBA-feasible stand-in for the 90+DPD/UTP reference default
  and is reported **alongside** the charge-off PD so the gap is explicit
  (~13.1% NPL vs ~12.2% charge-off on the whole book).
- **`PURCH(NOT C/O)` is treated as non-performing, not performing.** When the SBA
  *purchases* its guaranty it has honoured the guarantee on a loan the lender
  could not collect — an **effective default** awaiting formal charge-off.
  Counting it as "performing" (the prior treatment) understated problem exposure,
  so it now sits in the problem-exposure / Stage 2 layer.
- **Performing** = funded, not charged off, and not in the problem-exposure
  pipeline (paid in full, current, closed, etc.) — the Stage 1 proxy.
- **Exposure / EAD** is `grossapproval` (amount approved), not a point-in-time
  outstanding balance — SBA FOIA data does not provide an amortising balance, so
  concentration and dollar rates are measured at approval. For **revolving**
  working-capital lines this is an origination proxy that **ignores the
  credit-conversion factor (CCF)** on undrawn limits; a true (and downturn-)
  calibrated EAD per APS 113 Att. D would need drawn/limit-utilisation data the
  FOIA file does not carry.

## Credit-risk parameters (PD / LGD / EAD / EL)

These are **realised, through-the-cycle** parameters extracted from observed
outcomes (FY2000–2019, which spans the 2008 crisis) — calibration anchors for
deal pricing and ECL/RWA, **not** outputs of a fitted rating model.

- **PD** = default frequency, reported obligor-weighted (count) *and*
  exposure-weighted ($), on **two bases**: a *charge-off* PD (lagging) and a
  *non-performing* PD (the 90+DPD/UTP proxy — charge-off plus the problem-exposure
  pipeline). The charge-off PD is the lower bound; the non-performing PD is the
  closer reference-default measure.
- **LGD** = `grosschargeoffamount` ÷ exposure of defaulted loans (gross,
  whole-loan). The **net-of-guarantee** LGD multiplies by `(1 − guaranteed
  share)` and is **indicative only** — the SBA guarantee covers the guaranteed
  portion of each loss; it does not eliminate loss, it transfers it.
- **EAD** = `grossapproval`. With no amortising balance available, origination
  exposure is the EAD proxy and slightly **overstates** balance at default.
- **EL** = PD × LGD × EAD = realised charge-off $. The clean, internally
  consistent identity is `EL rate = PD($) × LGD`; pairing the obligor-weighted
  PD with the book-average EAD would overstate EL because defaulters skew
  smaller (see report §10 reading note).

### Product segmentation

This is **small-business (SME) lending throughout** — the dataset has **no
residential mortgage product** and **no labelled commercial-property field**.
Residential / commercial-property *mortgage* books sit in the sister mortgage
repos and SBA's separate **504** real-estate program, not in this 7(a) build.

`product_type` is a **use-of-proceeds facility type** derived (precedence order)
in `src/base_table.py`:

1. **Trade & export finance** — `subprogram` in `config.py:EXPORT_SUBPROGRAMS`.
2. **Working-capital line (revolving)** — `revolverstatus` is TRUE.
3. **Commercial property / real-estate term loan (proxy)** — loan term >
   `RE_TERM_MONTHS_MIN` (15y). SBA 7(a) maturities only exceed ~15y for real
   estate (25y max), so a long term is a **labelled proxy** for an
   owner-occupied commercial-property purpose — it is *not* a labelled field and
   will misclassify the rare long-dated non-RE loan.
4. **General SME term loan** — everything else.

Parameters are also cut by `loan_structure` (term vs revolving) and
`collateral_status` (secured vs unsecured — the **PPSR-registered-security
equivalent**) — report §10b/§10c.

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
- **Not a fitted rating model.** The PD/LGD/EAD/EL in report §10 are *extracted*
  from realised outcomes, not predicted by a scorecard. There is no obligor-level
  PD model and therefore no model-performance / backtesting layer here — that
  lives in the sister modelling repos.
- **Not credit advice or a forward-looking forecast.** These are descriptive
  monitoring views of historical, realised outcomes.

## Scope statements (what is deliberately out of scope, and why)

- **Country / transfer risk (APS 220 para 36): N/A.** The book is domestic US
  (borrower states are 50 states + DC + US territories / military / freely-
  associated states; the data-quality summary classifies these). There is no
  cross-border exposure, so no country-PD overlay or transfer-risk reserve.
- **Collateral monitoring (Basel CRE36.140): out of scope.** The FOIA file
  carries only a secured/unsecured indicator — no collateral type, value, or
  valuation date — so collateral valuation / ageing / revaluation monitoring is
  not possible. It would apply if the SBA **504** real-estate-collateral dataset
  were added.
- **Override / exception, rating-migration and peer MI (guide Steps 3–4): N/A on
  public data.** There is no application-decision, rating-grade or peer dataset in
  the FOIA extract, so origination/rating override rates, rating-migration
  matrices and peer comparisons cannot be produced here. The vintage-over-vintage
  and predictiveness views are the SBA-feasible forward signals; rating migration
  lives in the sister modelling repos.
- **HHI threshold calibration & tolerance band (gap review G23).** The 0.10
  "Moderate" / 0.18 "High" HHI bounds are tuned for a many-segment lending book
  (US DOJ merger guidance calls a *market* >0.25 highly concentrated; loan books
  are far more diversified). A `concentration.hhi_tolerance_band` (default 0.0010,
  ~0.5% of the 0.10 bound) prevents a marginal cross (e.g. industry HHI 0.1004 vs
  a 0.1000 amber) from reading as a hard step-change breach.

## Seasoning / survivorship

Cumulative charge-off curves are capped at each cohort's observable horizon so
immature cohorts are never shown with a deceptively low "final" rate. Even so,
the most recent vintages should be read as lower bounds on ultimate losses.
