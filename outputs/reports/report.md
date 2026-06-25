# Commercial Portfolio Monitoring Pack — SBA 7(a)

_Real public SBA 7(a) loan-level data. Monitoring outputs only — not a regulated disclosure. Any APS 330-style table below is laid out in that format for familiarity and is labelled accordingly._

## Board credit-risk dashboard — RAG vs risk-appetite limits

_Status: 🟢 11 within appetite · 🟡 3 amber · 🔴 0 red. Limits, owners and breach actions are defined in `config.yaml` (risk_appetite) per APS 220 paras 20/35; see section 7._

_Amber = appetite (early warning) · Red = tolerance (hard breach). † = marginal breach within the configured tolerance band._

| Metric | Value | Amber | Red | RAG status | Owner |
|---|---|---|---|---|---|
| Industry concentration (HHI) | 0.1004 | 0.1000 | 0.1800 | 🟡 AMBER † | Head of Credit Risk |
| Top single-industry exposure share | 17.7% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk |
| Largest originating-lender (channel) exposure share | 7.2% | 10.0% | 15.0% | 🟢 GREEN | Head of Counterparty Risk |
| Top-20 originating-lender (channel) exposure share | 42.2% | 45.0% | 60.0% | 🟢 GREEN | Head of Counterparty Risk |
| Largest single-borrower / brand-cluster exposure share | 0.0% | 2.0% | 5.0% | 🟢 GREEN | Head of Credit Risk |
| Top-20 borrower / brand-cluster exposure share | 0.4% | 5.0% | 10.0% | 🟢 GREEN | Head of Credit Risk |
| Top single-state exposure share | 17.0% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk |
| Revolving working-capital line exposure share | 7.9% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk |
| Small-ticket (<=$50k) exposure share | 4.4% | 15.0% | 25.0% | 🟢 GREEN | Head of Credit Risk |
| Latest-cohort origination exposure growth (YoY) | -9.9% | 15.0% | 25.0% | 🟢 GREEN | Head of Credit Risk |
| Through-the-cycle expected-loss rate ($) | 4.9% | 5.0% | 7.0% | 🟢 GREEN | Chief Credit Officer |
| Non-performing ratio (NPL proxy, count) | 13.1% | 13.0% | 17.0% | 🟡 AMBER | Chief Credit Officer |
| Portfolio charge-off rate (seasoned, count) | 13.5% | 12.0% | 16.0% | 🟡 AMBER | Chief Credit Officer |
| Young-cohort early-MOB charge-off vs predecessors | 0.60x | 1.25x | 1.50x | 🟢 GREEN | Head of Credit Risk |

> † This metric crossed its bound by less than the tolerance band (`config.yaml` → `concentration.hhi_tolerance_band`); treat as a watch item, not a step-change breach.

**Actions (amber/red items):**

| Action | Owner | Due | Trigger |
|---|---|---|---|
| Freeze new exposure growth in the top sector; table a diversification plan at the next Credit Committee. | Head of Credit Risk | Quarterly | Industry concentration (HHI) (🟡 AMBER) |
| Investigate the problem-exposure pipeline by segment; confirm provisioning keeps pace with NPL movement. | Chief Credit Officer | Quarterly | Non-performing ratio (NPL proxy, count) (🟡 AMBER) |
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
| Non-performing loans (NPL proxy, count) | 142,467 |
| Non-performing rate (NPL proxy, count) | 13.11% |
| Distinct NAICS sectors | 21 |
| Distinct borrower states | 60 |
|   of which 50 states + DC | 1,075,335 loans |
|   of which territories / military / FAS | 11,684 loans |
|   of which unrecognised state code | 0 loans |
| Distinct borrowers (names) | 910,399 |
| Distinct lenders (named) | 4,221 |
| Missing lender name | 27 |
| Missing borrower name | 23 |
| Missing NAICS sector | 16,922 |
| Missing approval date | 0 |
| Charge-offs missing charge-off date | 13 |

## 2. Concentration (HHI + top-N exposure share)

| Dimension | Segments | HHI | Level | top10_exposure_share |
|---|---|---|---|---|
| industry | 21 | 0.1004 | Moderate | 87.5% |
| state | 60 | 0.0577 | Low | 57.1% |
| lender | 4222 | 0.0144 | Low | 30.2% |
| borrower | 910400 | 0.0000 | Low | 0.3% |

> HHI = sum of squared segment shares (0 = diversified, 1 = fully concentrated).
> `lender` is the **originating bank / channel** (APS 220 para 39 — third-party-originator reliance), not the borrower. `borrower` is single-name / brand-cluster obligor concentration (APS 220 para 35(a)).

**2a. Single-name / franchise-brand concentration (APG 220 para 77).** SBA 7(a) is highly granular (>900k borrowers), so single-name share is immaterial — but the largest names are **franchise brands**, i.e. correlated-obligor clusters worth watching. Top 10 by exposure:

| Borrower / brand | Loans | Exposure ($) | Exposure share | Charge-off rate (count) |
|---|---|---|---|---|
| SUBWAY | 886 | $128,916,716 | 0.0% | 4.3% |
| COLD STONE CREAMERY | 398 | $98,476,345 | 0.0% | 19.4% |
| DUNKIN DONUTS | 160 | $97,634,150 | 0.0% | 3.1% |
| DAYS INN | 62 | $72,192,665 | 0.0% | 8.1% |
| SUPER 8 MOTEL | 64 | $71,236,200 | 0.0% | 4.7% |
| QUIZNO'S SUBS | 444 | $66,416,141 | 0.0% | 12.6% |
| THE UPS STORE | 356 | $55,182,200 | 0.0% | 6.5% |
| Interco Trading, Inc. | 12 | $51,000,000 | 0.0% | 0.0% |
| QUIZNO'S | 335 | $49,981,990 | 0.0% | 11.3% |
| ECONO LODGE | 45 | $45,133,950 | 0.0% | 8.9% |

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

> **Default-definition note (APS 220 para 79).** Default here is `LoanStatus == CHGOFF` — a *realised, lagging* write-off point. APS 220's reference default is earlier (90+ days past due / unlikely-to-pay), so this rate **understates** how many loans have already breached the reference-default point. The **non-performing (NPL) proxy** — charge-off plus the problem-exposure pipeline (section 5b) — is the closer reference-default measure (13.1% vs 12.2% on the whole book) and is reported in sections 1 and 10; `IN LIQUIDATION` and guaranty-purchased loans in particular are near-certain future charge-offs.

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

_APS 220 paras 33/79 / APG 220 para 66 — act early on **problem exposures** using **forward-looking** signals. These statuses are **not** a realised charge-off, but together with charge-off they form the **non-performing (NPL) proxy** (gap review G7/G8). `IN LIQUIDATION` and `PURCH(NOT C/O)` (SBA guaranty already purchased) are effective / near-certain defaults, not 'performing'._

| Status | Meaning | Loans | Exposure ($) | Share of book ($) | Signal |
|---|---|---|---|---|---|
| DELINQ | Delinquent | 1,130 | $525,298,418 | 0.2% | Leading — pre-charge-off problem exposure |
| PSTDUE | Past due | 575 | $345,098,500 | 0.1% | Leading — pre-charge-off problem exposure |
| LIQUID | In liquidation | 2,889 | $1,523,132,085 | 0.5% | Leading — near-certain future charge-off (in liquidation) |
| PURCH(NOT C/O) | Guaranty purchased (not charged off) | 5,211 | $4,129,932,295 | 1.4% | Non-performing — SBA guaranty purchased (effective default, not yet written off) |
| ALL_PROBLEM | **Total problem-exposure pipeline** | 9,805 | $6,523,461,298 | 2.3% | Leading — pre-charge-off pipeline (vs lagging charge-off) |

## 5c. Originator (third-party) performance oversight

_APS 220 para 39 / APG 220 paras 307-308 — third-party-originated exposures warrant enhanced monitoring. SBA 7(a) loans are written by originating lenders; this surfaces each material originator's realised charge-off rate (not just its volume), worst-first. A high rate flags a channel whose origination quality needs review._

| Originating lender | Loans | Exposure share | Charge-off rate (count) | Charge-off rate ($) | NPL rate |
|---|---|---|---|---|---|
| Independence Bank | 1,804 | 0.1% | 46.3% | 32.5% | 46.8% |
| Popular Bank | 7,640 | 0.6% | 34.4% | 29.7% | 35.5% |
| Capital One, National Association | 20,566 | 0.5% | 30.6% | 23.3% | 30.7% |
| Business Loan Center, LLC | 6,180 | 0.9% | 29.3% | 17.9% | 29.3% |
| Bank of Hope | 33,321 | 2.3% | 29.1% | 8.4% | 29.3% |
| HSBC Bank USA National Association | 4,250 | 0.1% | 29.1% | 24.9% | 29.1% |
| VelocitySBA, LLC | 11,950 | 0.1% | 24.7% | 19.9% | 24.8% |
| Bank of America, National Association | 72,260 | 1.4% | 22.7% | 19.9% | 22.7% |
| BayFirst National Bank | 3,894 | 0.4% | 20.3% | 14.5% | 29.6% |
| Business Lenders, LLC | 904 | 0.1% | 19.7% | 21.1% | 19.7% |

## 6. Stage proxy (IFRS 9-style: Stage 1 / 2 / 3)

_A PROXY, not true IFRS 9 staging — but the problem-exposure pipeline lets us separate **Stage 2** (problem exposure / SICR proxy: DELINQ / PSTDUE / LIQUID / guaranty-purchased) from **Stage 1** (performing) rather than lumping near-certain-loss loans into 'performing', and **Stage 3** (charged off). Full staging / transition matrices live in the companion Freddie Mac monitor._

| Proxy stage | Loans | Exposure ($) | Exposure share |
|---|---|---|---|
| Stage 1 — performing | 944,552 | 259,153,795,298 | 90.0% |
| Stage 2 — problem exposure (SICR proxy) | 9,805 | 6,523,461,298 | 2.3% |
| Stage 3 — charged off (default) | 132,662 | 22,131,753,989 | 7.7% |

## 7. Risk appetite & limit register (full)

_APS 220 para 20 (appetite statement) + para 35 (limits on industry, geography, single-name / borrower, originating channel and higher-risk products), plus dollar-EL, NPL and growth limits. **Amber = appetite** (early warning); **red = tolerance** (hard breach). Calibration, ownership and review are documented in `docs/governance.md` §2. The board dashboard at the top reports live RAG against these limits._

| Metric | Value | Amber | Red | RAG | Owner | Breach action | Review |
|---|---|---|---|---|---|---|---|
| Industry concentration (HHI) | 0.1004 | 0.1000 | 0.1800 | 🟡 AMBER | Head of Credit Risk | Freeze new exposure growth in the top sector; table a diversification plan at the next Credit Committee. | Quarterly |
| Top single-industry exposure share | 17.7% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk | Review sector sub-limits; require Committee sign-off on further originations in the top sector. | Quarterly |
| Largest originating-lender (channel) exposure share | 7.2% | 10.0% | 15.0% | 🟢 GREEN | Head of Counterparty Risk | Re-underwrite the lender relationship; cap incremental volume and reassess guaranty reliance. | Quarterly |
| Top-20 originating-lender (channel) exposure share | 42.2% | 45.0% | 60.0% | 🟢 GREEN | Head of Counterparty Risk | Broaden the originating-lender panel; set per-lender concentration sub-limits. | Quarterly |
| Largest single-borrower / brand-cluster exposure share | 0.0% | 2.0% | 5.0% | 🟢 GREEN | Head of Credit Risk | Review the single-name exposure against the large-exposure (APS 221) framework; assess correlated brand-cluster risk. | Quarterly |
| Top-20 borrower / brand-cluster exposure share | 0.4% | 5.0% | 10.0% | 🟢 GREEN | Head of Credit Risk | Assess correlated risk across the top brand clusters; consider per-brand sub-limits. | Quarterly |
| Top single-state exposure share | 17.0% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk | Review state sub-limits; assess regional macro exposure and require Committee sign-off on further originations in the top state. | Quarterly |
| Revolving working-capital line exposure share | 7.9% | 20.0% | 30.0% | 🟢 GREEN | Head of Credit Risk | Tighten revolving-line origination and pricing; review undrawn-limit (CCF) exposure. | Quarterly |
| Small-ticket (<=$50k) exposure share | 4.4% | 15.0% | 25.0% | 🟢 GREEN | Head of Credit Risk | Review small-ticket origination standards and risk-based pricing (highest-EL band). | Quarterly |
| Latest-cohort origination exposure growth (YoY) | -9.9% | 15.0% | 25.0% | 🟢 GREEN | Head of Credit Risk | Confirm growth is not loosening standards; review the latest cohort's origination mix and early-MOB performance. | Quarterly |
| Through-the-cycle expected-loss rate ($) | 4.9% | 5.0% | 7.0% | 🟢 GREEN | Chief Credit Officer | Reprice for risk and reassess provision adequacy; escalate to the Board Risk Committee. | Quarterly |
| Non-performing ratio (NPL proxy, count) | 13.1% | 13.0% | 17.0% | 🟡 AMBER | Chief Credit Officer | Investigate the problem-exposure pipeline by segment; confirm provisioning keeps pace with NPL movement. | Quarterly |
| Portfolio charge-off rate (seasoned, count) | 13.5% | 12.0% | 16.0% | 🟡 AMBER | Chief Credit Officer | Tighten origination credit policy and pricing; escalate to the Board Risk Committee. | Quarterly |
| Young-cohort early-MOB charge-off vs predecessors | 0.60x | 1.25x | 1.50x | 🟢 GREEN | Head of Credit Risk | Investigate the deteriorating cohort's origination standards; pause comparable new lending pending review. | Quarterly |

## 8. Leading vs lagging — framing & leading views

_APG 220 para 66 — favour **forward-looking** signals. SBA is outcome-level, so most metrics here are lagging by nature; the table is explicit about which is which. The leading views below (origination mix, vintage-over-vintage early-MOB) are the forward signals the data supports, and section 8c **validates** that they actually predict loss._

| Metric | Type | Rationale |
|---|---|---|
| Concentration (HHI, top-N share) | Lagging/static | Snapshot of the current book |
| Charge-off rate by industry/size/vintage | Lagging | Realised write-offs |
| Vintage cohort charge-off curves | Lagging | Cumulative realised losses by age |
| Loan-age transition (when charge-offs occur) | Lagging | Realised default timing |
| Stage proxy (Stage 1 / 2 / 3) | Mixed | Stage 2 (problem) is leading; Stage 3 is realised |
| Originator (third-party) performance | Leading/oversight | A weak channel's charge-off rate flags future losses from its pipeline |
| Problem-exposure layer (DELINQ/PSTDUE/LIQUID/PURCH) | Leading | Non-performing pipeline; IN LIQUIDATION / guaranty-purchased ~ certain future charge-off |
| Origination volume/mix trend by approval year | Leading | Mix shift in what is being written leads the future charge-off rate |
| Vintage-over-vintage early-MOB charge-off | Leading | Young cohort deteriorating faster than predecessors at the same age |
| Predictiveness validation (early signal vs final loss) | Leading/validation | Confirms the leading signals actually rank cohorts by eventual loss |

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

## 8c. Predictiveness validation of the leading indicators

_APG 113 para 140 element 3 (performance) / APG 220 para 66. A signal is only 'leading' if it actually predicts later loss. Across seasoned cohorts, each early indicator is rank-correlated (Spearman) with the cohort's *final* charge-off rate — a positive correlation confirms the indicator ranks cohorts the way their eventual losses do._

| Leading indicator | Cohorts | Spearman vs final charge-off | Verdict |
|---|---|---|---|
| Early-MOB charge-off rate | 16 | +0.87 | Predictive (confirmed leading) |
| Large-ticket origination share | 16 | -0.26 | Weak / not predictive |
| Top-sector origination share | 16 | +0.16 | Weak / not predictive |

## 9. Stress ladder — vs the charge-off AND dollar-EL limits

_APS 220 para 73 / APG 220 paras 14, 76. Four scenarios — baseline, **adverse** (historical 2006-08 crisis replay), **severe** (worst observed vintage) and a **hypothetical** forward management overlay — each re-tested against TWO appetite limits: the charge-off-rate limit AND the dollar-EL-rate limit (so stressed LGD/EAD severity is bounded by appetite, not just the count rate). A breach of either triggers the limit's breach action (tighter origination / pricing / provisioning)._

| Scenario | Charge-off rate | RAG (CO limit) | EL rate ($) | RAG (EL limit) | Implied charge-off ($) | Additional vs baseline ($) |
|---|---|---|---|---|---|---|
| Baseline (current book) | 13.5% | 🟡 AMBER | 4.9% | 🟢 GREEN | $38,739,092,825 | $0 |
| Adverse — historical crisis (1.93x, [2006, 2007, 2008]) | 26.0% | 🔴 RED | 15.3% | 🔴 RED | $74,772,780,950 | $36,033,688,125 |
| Severe — worst vintage (2007) | 28.8% | 🔴 RED | 17.6% | 🔴 RED | $82,946,556,850 | $44,207,464,026 |
| Hypothetical overlay (1.25x severe) | 36.0% | 🔴 RED | 21.9% | 🔴 RED | $103,697,586,514 | $64,958,493,689 |

> **Stress breaches appetite** → escalate to the relevant limit owner(s); review origination credit policy, pricing and provision adequacy (see the dashboard actions table).

## 10. Credit-risk parameters (PD / LGD / EAD / EL) — pricing & ECL inputs

_Realised, **through-the-cycle** parameters read off the FY2000-2019 outcome data — the loss-experience anchors a deal-pricing or ECL/RWA model is calibrated against. These are **observed**, not model outputs: no obligor-level rating model lives here (default is an actual status). Identity check: EL rate = PD($) x LGD._

| Parameter | Definition | Portfolio average |
|---|---|---|
| **PD** — charge-off default (obligor-weighted) | charged-off loans / funded loans | 12.2% |
| **PD** — charge-off default, exposure-weighted ($) | defaulted EAD / total EAD | 7.7% |
| **PD** — non-performing (90+DPD/UTP proxy, count) | non-performing loans / funded loans | 13.1% |
| **PD** — non-performing, exposure-weighted ($) | non-performing EAD / total EAD | 10.0% |
| **LGD** — loss given default (gross, whole-loan) | charge-off $ / defaulted EAD | 64.0% |
| **LGD** — net of SBA guarantee (indicative, lender-retained) | LGD x (1 - guaranteed share) | 17.2% |
| **EAD** — exposure at default (avg per loan) | gross approval | $264,769 |
| **EAD** — avg per *defaulted* loan | gross approval of defaults | $166,828 |
| **EL rate** — expected loss / exposure | PD($) x LGD = charge-off $ / total EAD | 4.9% |
| **EL** — expected loss per loan (avg) | charge-off $ / funded loans | $13,032 |
| _SBA guaranteed share_ | guaranteed $ / gross approval | 73.2% |

> **Reading note.** The charge-off PD is a *realised, lagging* default; the **non-performing PD** adds the problem-exposure pipeline (DELINQ / PSTDUE / LIQUID / guaranty-purchased) and is the closer proxy to the APS 220 reference default (90+DPD / UTP) — the charge-off PD therefore **understates** how many loans ever breached. The obligor-weighted PD pairs with the *defaulted-loan* EAD, not the book-average EAD — defaulters skew smaller, so the exposure-weighted PD($) is lower. For an exposure-based EL, use `EL rate = PD($) x LGD`; for a per-account EL, use the EL-per-loan figure.

**10a. Risk-based parameters by loan-size band (for tiered pricing).** Small tickets default ~5x more often and lose more per dollar — the curve a risk-based price has to ride:

| Size band | Loans | PD (count) | LGD | Avg EAD | EL rate |
|---|---|---|---|---|---|
| <=50k | 458,365 | 16.1% | 83.3% | $27,372 | 13.5% |
| 50k-150k | 260,397 | 11.0% | 72.9% | $103,701 | 8.0% |
| 150k-350k | 163,918 | 9.1% | 66.9% | $251,442 | 6.1% |
| 350k-1m | 137,852 | 8.2% | 60.3% | $602,830 | 4.9% |
| 1m-2m | 49,362 | 7.3% | 57.4% | $1,429,610 | 4.2% |
| >2m | 17,125 | 2.9% | 52.5% | $3,116,693 | 1.5% |

**10b. Parameters by product (facility type).** This is small-business lending throughout — the dataset has **no residential** mortgage product, and **no labelled commercial-property** field. Facility type is a *use-of-proceeds* read from the data: trade/export subprogram → trade finance; revolving flag → working-capital line; loan term > 15y → real-estate purpose (only real estate carries SBA maturities that long — a labelled **proxy**); everything else → general SME term loan:

| Product (facility type) | Loans | PD (count) | LGD | Avg EAD | EL rate |
|---|---|---|---|---|---|
| General SME term loan | 615,115 | 13.1% | 64.2% | $217,619 | 7.1% |
| Commercial property / real-estate term loan (proxy) | 144,669 | 3.7% | 52.9% | $875,305 | 1.9% |
| Working-capital line (revolving) | 319,735 | 14.4% | 87.0% | $63,483 | 9.4% |
| Trade & export finance | 7,500 | 11.2% | 60.4% | $936,121 | 4.6% |

**10c. Parameters by loan structure & collateral.** Two more pricing-relevant cuts — term loan vs revolving line, and secured (collateralised — the PPSR-registered equivalent) vs unsecured:

| Cut | Segment | Loans | PD (count) | LGD | Avg EAD | EL rate |
|---|---|---|---|---|---|---|
| Loan structure | Term loan | 765,589 | 11.3% | 61.4% | $346,313 | 4.6% |
| Loan structure | Revolving line of credit | 321,430 | 14.4% | 86.9% | $70,545 | 8.6% |
| Collateral | Secured | 436,969 | 8.8% | 62.9% | $410,653 | 3.4% |
| Collateral | Unsecured | 650,050 | 14.5% | 64.8% | $166,705 | 7.5% |

**10d. Parameter stress test — the two downturn severities in the data.** The SBA data holds one macro downturn (the 2008 crisis) but supports a two-level stress ladder read off realised cohorts: **adverse** = the crisis cohort pooled (2006, 2007, 2008); **severe** = the single worst vintage (2007, the peak). PD and LGD both rise, so EL rises multiplicatively — downturn-PD / downturn-LGD inputs for stressed pricing and capital:

| Parameter | Through-the-cycle | Adverse (2006, 2007, 2008) | × | Severe (2007) | × |
|---|---|---|---|---|---|
| PD — default rate (obligor-weighted) | 12.2% | 25.9% | 2.13x | 28.8% | 2.36x |
| PD — default rate (exposure-weighted) | 7.7% | 21.9% | 2.85x | 24.4% | 3.18x |
| LGD — loss given default | 64.0% | 70.0% | 1.09x | 71.9% | 1.12x |
| EAD — avg exposure per loan ($) | $264,769 | $154,065 | 0.58x | $142,500 | 0.54x |
| EL rate — expected loss / exposure | 4.9% | 15.3% | 3.11x | 17.6% | 3.57x |

## Notes — APS 330 / Pillar 3 & governance

- **APS 330 / Pillar 3 (CML-7).** The concentration (section 2) and credit-quality-by-industry outputs are the same primitives that feed a **Pillar 3 (APS 330) credit-risk disclosure**. The `05_aps330_style_credit_quality` table is laid out in that **format for familiarity only** — built from public SBA data, it is **not** a regulated entity's disclosure. In a bank these would be a *feeder* into the periodic Pillar 3 disclosure, not the disclosure itself.
- **Governance & validation.** Reporting cadence to forums, appetite ownership, and independent annual validation (mapped to the 8-element APG 113 framework) are documented in `docs/governance.md`. Section 10 extracts **realised** PD/LGD/EAD/EL as calibration inputs. There is **no fitted rating model** here, so *model-estimation* performance/backtesting is N/A (that lives in the sister modelling repos) — but the *parameters* still carry a validation note (representativeness, downturn calibration) in `docs/governance.md`, and the leading indicators are predictiveness-tested in section 8c.

---

_Generated by the commercial-portfolio-monitor pipeline. Data source: U.S. Small Business Administration 7(a) FOIA loan-level dataset (data.sba.gov), public domain._