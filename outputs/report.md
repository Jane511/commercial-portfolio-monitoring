# Commercial Portfolio Monitoring Pack — SBA 7(a)

_Real public SBA 7(a) loan-level data. Monitoring outputs only — not a regulated disclosure. Any APS 330-style table below is laid out in that format for familiarity and is labelled accordingly._

## Board credit-risk dashboard — RAG vs risk-appetite limits

_Status: 🟢 4 within appetite · 🟡 2 amber · 🔴 0 red. Limits, owners and breach actions are defined in `config.yaml` (risk_appetite) per APS 220 paras 20/35; see section 7._

| Metric | Value | Amber | Red | RAG status | Owner |
|---|---|---|---|---|---|
| Industry concentration (HHI) | 0.1004 | 0.1000 | 0.1800 | 🟡 AMBER | Head of Credit Risk |
| Top single-industry exposure share | 17.7% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk |
| Largest single-lender exposure share | 7.2% | 10.0% | 15.0% | 🟢 GREEN | Head of Counterparty Risk |
| Top-20 lender exposure share | 42.2% | 45.0% | 60.0% | 🟢 GREEN | Head of Counterparty Risk |
| Portfolio charge-off rate (seasoned, count) | 13.5% | 12.0% | 16.0% | 🟡 AMBER | Chief Credit Officer |
| Young-cohort early-MOB charge-off vs predecessors | 0.60x | 1.25x | 1.50x | 🟢 GREEN | Head of Credit Risk |

**Actions (amber/red items):**

| Action | Owner | Due | Trigger |
|---|---|---|---|
| Freeze new exposure growth in the top sector; table a diversification plan at the next Credit Committee. | Head of Credit Risk | Quarterly | Industry concentration (HHI) (🟡 AMBER) |
| Tighten origination credit policy and pricing; escalate to the Board Risk Committee. | Chief Credit Officer | Quarterly | Portfolio charge-off rate (seasoned, count) (🟡 AMBER) |

---

## 1. Portfolio at a glance

| Metric | Value |
|---|---|
| Funded loans | 1,087,019 |
| Approval FY range | 2000-2019 |
| Total gross approval ($) | 287,809,010,585 |
| Charged-off loans (count) | 132,662 |
| Charge-off rate (count) | 12.20% |
| Charge-off rate ($) | 4.92% |
| Distinct NAICS sectors | 21 |
| Distinct borrower states | 60 |
| Distinct lenders | 4,221 |
| Missing NAICS sector | 16,922 |
| Missing approval date | 0 |
| Charge-offs missing charge-off date | 13 |

## 2. Concentration (HHI + top-N exposure share)

| Dimension | Segments | HHI | Level | top10_exposure_share |
|---|---|---|---|---|
| industry | 21 | 0.1004 | Moderate | 87.5% |
| state | 60 | 0.0577 | Low | 57.1% |
| lender | 4222 | 0.0144 | Low | 30.2% |

> HHI = sum of squared segment shares (0 = diversified, 1 = fully concentrated).

## 3. Charge-off rates by industry (worst 8)

| Industry | Loans | Charge-off rate (count) | Charge-off rate ($) |
|---|---|---|---|
| Public Administration | 184 | 17.9% | 5.6% |
| Real Estate & Rental & Leasing | 23,104 | 15.0% | 5.0% |
| Information | 15,692 | 15.0% | 7.6% |
| Wholesale Trade | 60,185 | 14.8% | 6.4% |
| Retail Trade | 174,624 | 14.2% | 8.2% |
| Construction | 104,884 | 13.7% | 9.2% |
| Transportation & Warehousing | 46,449 | 13.5% | 7.3% |
| Finance & Insurance | 17,513 | 13.1% | 4.7% |

## 4. Charge-off rate by vintage (approval-year cohort)

> **Default-definition note (APS 220 para 79).** Default here is `LoanStatus == CHGOFF` — a *realised, lagging* write-off point. APS 220's reference default is earlier (90+ days past due / unlikely-to-pay), so this rate **understates** how many loans have already breached the reference-default point. The pre-charge-off problem-exposure layer (section 5b) is the SBA-feasible *leading* view; `IN LIQUIDATION` in particular is a near-certain future charge-off.

| Vintage | Loans | Charge-off rate (count) | Fully seasoned |
|---|---|---|---|
| 2000 | 37,600 | 4.7% | yes |
| 2001 | 37,323 | 5.8% | yes |
| 2002 | 45,184 | 6.9% | yes |
| 2003 | 59,119 | 9.4% | yes |
| 2004 | 71,283 | 12.2% | yes |
| 2005 | 84,436 | 17.6% | yes |
| 2006 | 86,570 | 24.3% | yes |
| 2007 | 88,270 | 28.8% | yes |
| 2008 | 61,636 | 24.2% | yes |
| 2009 | 36,636 | 11.6% | yes |
| 2010 | 39,913 | 7.2% | yes |
| 2011 | 45,628 | 5.6% | yes |
| 2012 | 38,889 | 5.3% | yes |
| 2013 | 40,416 | 5.2% | yes |
| 2014 | 45,962 | 5.8% | yes |
| 2015 | 55,421 | 6.4% | yes |
| 2016 | 56,789 | 6.9% | no (under-reports) |
| 2017 | 56,079 | 7.4% | no (under-reports) |
| 2018 | 54,195 | 7.6% | no (under-reports) |
| 2019 | 45,670 | 6.2% | no (under-reports) |

## 5. Early-warning segments (industry x vintage x size)

| Industry | Vintage | Size band | Loans | Charge-off rate | x Portfolio | Severity |
|---|---|---|---|---|---|---|
| Real Estate & Rental & Leasing | 2007 | <=50k | 1,978 | 42.4% | 3.1x | High |
| Wholesale Trade | 2007 | <=50k | 2,763 | 38.6% | 2.9x | High |
| Wholesale Trade | 2008 | <=50k | 1,590 | 37.2% | 2.8x | High |
| Finance & Insurance | 2007 | <=50k | 1,308 | 37.0% | 2.8x | High |
| Wholesale Trade | 2007 | 50k-150k | 1,198 | 36.1% | 2.7x | High |
| Real Estate & Rental & Leasing | 2007 | 50k-150k | 379 | 35.1% | 2.6x | High |
| Wholesale Trade | 2006 | 50k-150k | 1,245 | 34.6% | 2.6x | High |
| Finance & Insurance | 2007 | 50k-150k | 258 | 34.5% | 2.6x | High |
| Real Estate & Rental & Leasing | 2006 | 50k-150k | 352 | 34.1% | 2.5x | High |
| Real Estate & Rental & Leasing | 2008 | <=50k | 959 | 34.1% | 2.5x | High |
| Retail Trade | 2007 | <=50k | 9,020 | 33.6% | 2.5x | High |
| Real Estate & Rental & Leasing | 2006 | <=50k | 1,437 | 33.5% | 2.5x | High |
| Construction | 2007 | <=50k | 6,924 | 32.5% | 2.4x | High |
| Finance & Insurance | 2008 | <=50k | 716 | 32.4% | 2.4x | High |
| Information | 2008 | <=50k | 676 | 32.4% | 2.4x | High |

## 5b. Problem-exposure layer (pre-charge-off early warning)

_APS 220 para 79 / APG 220 para 66 — act early on **problem exposures** using **forward-looking** signals. These statuses are **not** counted as default (default = charge-off), but they are the pipeline that precedes charge-off. `IN LIQUIDATION` is a near-certain future charge-off — a leading signal._

| Status | Meaning | Loans | Exposure ($) | Share of book ($) | Signal |
|---|---|---|---|---|---|
| DELINQ | Delinquent | 1,130 | $525,298,418 | 0.2% | Leading — pre-charge-off problem exposure |
| PSTDUE | Past due | 575 | $345,098,500 | 0.1% | Leading — pre-charge-off problem exposure |
| LIQUID | In liquidation | 2,889 | $1,523,132,085 | 0.5% | Leading — near-certain future charge-off |
| ALL_PROBLEM | **Total problem-exposure pipeline** | 4,594 | $2,393,529,003 | 0.8% | Leading — pre-charge-off pipeline (vs lagging charge-off) |

## 6. Stage proxy (performing vs defaulted)

_Coarse split only — a proxy, not IFRS 9 staging. Full staging and transition matrices live in the companion Freddie Mac monitor._

| Proxy stage | Loans | Exposure ($) | Exposure share |
|---|---|---|---|
| Defaulted (charged off) — proxy Stage 3 | 132,662 | 22,131,753,989 | 7.7% |
| Performing — proxy Stage 1/2 | 954,357 | 265,677,256,596 | 92.3% |

## 7. Risk appetite & limit register (full)

_APS 220 para 20 (appetite statement) + para 35 (concentration limits — industry, geography, single name / lender). The board dashboard at the top reports live RAG against these limits._

| Metric | Value | Amber | Red | RAG | Owner | Breach action | Review |
|---|---|---|---|---|---|---|---|
| Industry concentration (HHI) | 0.1004 | 0.1000 | 0.1800 | 🟡 AMBER | Head of Credit Risk | Freeze new exposure growth in the top sector; table a diversification plan at the next Credit Committee. | Quarterly |
| Top single-industry exposure share | 17.7% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk | Review sector sub-limits; require Committee sign-off on further originations in the top sector. | Quarterly |
| Largest single-lender exposure share | 7.2% | 10.0% | 15.0% | 🟢 GREEN | Head of Counterparty Risk | Re-underwrite the lender relationship; cap incremental volume and reassess guaranty reliance. | Quarterly |
| Top-20 lender exposure share | 42.2% | 45.0% | 60.0% | 🟢 GREEN | Head of Counterparty Risk | Broaden the originating-lender panel; set per-lender concentration sub-limits. | Quarterly |
| Portfolio charge-off rate (seasoned, count) | 13.5% | 12.0% | 16.0% | 🟡 AMBER | Chief Credit Officer | Tighten origination credit policy and pricing; escalate to the Board Risk Committee. | Quarterly |
| Young-cohort early-MOB charge-off vs predecessors | 0.60x | 1.25x | 1.50x | 🟢 GREEN | Head of Credit Risk | Investigate the deteriorating cohort's origination standards; pause comparable new lending pending review. | Quarterly |

## 8. Leading vs lagging — framing & leading views

_APG 220 para 66 — favour **forward-looking** signals. SBA is outcome-level, so most metrics here are lagging by nature; the table is explicit about which is which, and the two leading views below are the forward signals the data still supports._

| Metric | Type | Rationale |
|---|---|---|
| Concentration (HHI, top-N share) | Lagging/static | Snapshot of the current book |
| Charge-off rate by industry/size/vintage | Lagging | Realised write-offs |
| Vintage cohort charge-off curves | Lagging | Cumulative realised losses by age |
| Loan-age transition (when charge-offs occur) | Lagging | Realised default timing |
| Stage proxy (performing vs defaulted) | Lagging | Terminal status only |
| Problem-exposure layer (DELINQ/PSTDUE/LIQUID) | Leading | Pre-charge-off pipeline; IN LIQUIDATION ~ certain future charge-off |
| Origination volume/mix trend by approval year | Leading | Mix shift in what is being written leads the future charge-off rate |
| Vintage-over-vintage early-MOB charge-off | Leading | Young cohort deteriorating faster than predecessors at the same age |

**8a. Origination volume & mix trend by approval year (leading).** A swing into higher-charge-off sectors or larger tickets leads the future book charge-off rate. Most recent 8 cohorts:

| Approval FY | Loans | Exposure ($) | YoY growth | Top sector | Top-sector share | Large-ticket share |
|---|---|---|---|---|---|---|
| 2012 | 38,889 | $13,256,492,000 | -18.4% | Accommodation & Food Services | 16.5% | 49.6% |
| 2013 | 40,416 | $15,492,120,600 | 16.9% | Accommodation & Food Services | 18.9% | 52.4% |
| 2014 | 45,962 | $16,871,102,500 | 8.9% | Accommodation & Food Services | 18.6% | 54.2% |
| 2015 | 55,421 | $20,370,589,100 | 20.7% | Accommodation & Food Services | 18.1% | 55.1% |
| 2016 | 56,789 | $21,621,109,443 | 6.1% | Accommodation & Food Services | 18.7% | 56.5% |
| 2017 | 56,079 | $23,048,544,700 | 6.6% | Accommodation & Food Services | 19.9% | 57.9% |
| 2018 | 54,195 | $22,807,991,900 | -1.0% | Accommodation & Food Services | 20.5% | 58.6% |
| 2019 | 45,670 | $20,551,788,500 | -9.9% | Accommodation & Food Services | 19.9% | 58.6% |

**8b. Vintage-over-vintage early-MOB charge-off (24m, leading).** Is a young cohort charging off faster than its predecessor did at the same age? A ratio > 1 is a forward deterioration signal:

| Vintage | Charge-off @ 24m | Prior vintage @ 24m | VoV ratio |
|---|---|---|---|
| 2000 | 0.0% | — | — |
| 2001 | 0.0% | 0.0% | 1.00x |
| 2002 | 0.2% | 0.0% | 6.00x |
| 2003 | 0.6% | 0.2% | 3.28x |
| 2004 | 0.9% | 0.6% | 1.53x |
| 2005 | 1.1% | 0.9% | 1.28x |
| 2006 | 2.4% | 1.1% | 2.04x |
| 2007 | 4.2% | 2.4% | 1.81x |
| 2008 | 3.8% | 4.2% | 0.90x |
| 2009 | 1.6% | 3.8% | 0.41x |
| 2010 | 1.0% | 1.6% | 0.64x |
| 2011 | 0.5% | 1.0% | 0.53x |
| 2012 | 0.4% | 0.5% | 0.75x |
| 2013 | 0.4% | 0.4% | 1.00x |
| 2014 | 0.5% | 0.4% | 1.25x |
| 2015 | 0.4% | 0.5% | 0.90x |
| 2016 | 0.7% | 0.4% | 1.56x |
| 2017 | 0.8% | 0.7% | 1.09x |
| 2018 | 0.8% | 0.8% | 1.11x |
| 2019 | 0.4% | 0.8% | 0.50x |

---

_Generated by the commercial-portfolio-monitor pipeline. Data source: U.S. Small Business Administration 7(a) FOIA loan-level dataset (data.sba.gov), public domain._