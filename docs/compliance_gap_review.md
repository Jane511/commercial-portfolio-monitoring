# Regulatory gap review — Commercial Portfolio Monitor (SBA 7(a))

**Subject:** this repository (`commercial-portfolio-monitoring`), an SBA 7(a) FOIA public-data
demonstrator of a Layer-3 credit-portfolio monitoring programme.

**Benchmark:** *How to Build a Credit Portfolio Monitoring Programme* (training guide) and the
paragraphs it cites — APRA **APS 220**, **APG 220**, **APS 113**, **APG 113**, **APS 330**, and the
**Basel Framework** (CRE36, BCP 17).

**Date of review:** 2026-06-25. **Status:** all findings below were actioned in the same change set
(see the *Resolution* line on each). Documentation-only fixes record a scope statement; code fixes
record the module(s) touched.

---

## How to read this

This is a **public-data demonstrator**, not a regulated entity's framework, and the SBA FOIA dataset
is *outcome-level* (one final status per loan; no monthly panel, no running balance, no facility
limits). Findings tagged **`[data-inherent]`** stem from that and are resolved with a precise scope
statement rather than new analytics. The remainder are resolved with code.

Severity: 🔴 material · 🟡 moderate · ⚪ minor.

---

## A. Risk appetite & limit framework (APS 220 paras 20, 35)

### 🔴 G1 — "Single-lender" limit measures the *originating bank*, not the *borrower*; single-name concentration was unaddressed
- **Guidance:** APS 220 para 35(a); APG 220 para 77 (borrowers with *similar risk characteristics*); guide Step 9.
- **Issue:** the dashboard's "single-lender"/"top-20 lender" limits measure the originating bank (a
  distribution channel), not obligor credit concentration. `borrname` was read but "not analysed."
- **Resolution (code):** added a **borrower / franchise-brand** concentration dimension
  (`concentration.py`), with single-name and top-20 borrower limits in `config.yaml`. The top names
  are franchise brands (SUBWAY, DUNKIN DONUTS, DAYS INN…) — correlated-obligor clusters per APG 220
  para 77 — so the view is surfaced as **brand-cluster** concentration with a caveat that SBA 7(a) is
  highly granular (top-20 ≈ 0.4% of book). The bank metrics are **relabelled** "originating-lender /
  channel concentration."

### 🟡 G2 — Geographic concentration computed but not an appetite limit
- **Guidance:** APS 220 para 35(c); APG 220 paras 77–80.
- **Resolution (code):** added a **top-state geographic** limit (`top_state_share`) to the register so
  a geographic build-up trips RAG.

### 🟡 G3 — No higher-risk-product / higher-risk-segment sub-limit
- **Guidance:** APS 220 para 35(a)(b).
- **Resolution (code):** added a **revolving working-capital share** product sub-limit and a
  **small-ticket (≤$50k) share** segment sub-limit (the two highest-EL cuts).

### 🟡 G4 — No growth limit despite computing YoY origination growth
- **Guidance:** guide Step 1 (RWA growth); APG 220 para 67 (rapid loan growth as leading indicator).
- **Resolution (code):** added an **origination exposure-growth** limit driven by the existing
  `leading.origination_trend` YoY figure.

### 🟡 G5 — Appetite statement did not distinguish *appetite* from *tolerance*, nor document calibration/approval/review
- **Guidance:** APS 220 para 20.
- **Resolution (docs):** `config.yaml` header and `governance.md` now state **amber = appetite**
  (early-warning) / **red = tolerance** (hard limit), the calibration basis for each bound, the
  approver (Board Risk Committee), and the review timing/process.

### 🟡 G6 — Only a count-based charge-off limit; no $-loss-rate or NPL-ratio limit
- **Guidance:** guide Step 1 (NPL ratio; loss rate), Part 5.1.
- **Resolution (code):** added a **dollar EL-rate** limit and a **non-performing (NPL-proxy) ratio**
  limit to the register.

---

## B. Default definition & problem exposure (APS 220 para 33; APG 220 paras 63, 67)

### 🔴 G7 — Default = charge-off, not APS 220's 90+DPD / unlikely-to-pay; PD/NPL understated
- **Guidance:** APS 220 reference default; para 33.
- **Resolution (code):** added a **non-performing (`is_nonperforming`) flag** = charge-off ∪
  problem-exposure pipeline — the closest SBA-feasible 90+DPD/UTP proxy. PD is now reported on **both**
  bases (charge-off PD *and* non-performing PD) with the charge-off PD explicitly flagged as a floor.

### 🔴 G8 — `PURCH(NOT C/O)` (guaranty purchased, not charged off) was classified "Performing"
- **Guidance:** APS 220 para 33 (early identification of non-performing exposures).
- **Issue:** a purchased-but-not-charged-off guaranty is the SBA honouring its guarantee — an effective
  default. 5,211 such loans were bucketed as performing, understating problem exposure.
- **Resolution (code):** `PURCH(NOT C/O)` moved into the **problem-exposure / non-performing layer**
  with a distinct "guaranty purchased — effective default" signal (`config.yaml`, `base_table.py`).

### 🟡 G9 — No staged problem-exposure workflow; no restructured/hardship; no provision adequacy
- **Guidance:** APS 220 para 33; APG 220 paras 63, 68; guide Step 8. `[partly data-inherent]`
- **Resolution (docs):** `governance.md` now documents the watch-list → heightened → pre-default →
  workout → charge-off escalation workflow, and records that restructured/hardship metrics and
  provision coverage are unavailable in FOIA data (deferred to the sister repos).

### 🟡 G10 — Stage proxy put near-certain-loss `LIQUID` and arrears into "Performing — Stage 1/2"
- **Guidance:** APG 220 para 67(a); IFRS 9 SICR logic.
- **Resolution (code):** the stage proxy now splits **Stage 1 (performing)** / **Stage 2 (problem
  exposure)** / **Stage 3 (charged off)**, reconciling report §5b and §6.

---

## C. Forward-looking indicators & MI (APG 220 paras 65, 66, 67)

### 🟡 G11 — Heavily lagging; "leading" indicators never shown to be predictive
- **Guidance:** APG 220 para 66.
- **Resolution (code):** new `validation.py` backtests that the leading signals (early-MOB charge-off,
  origination mix) actually precede higher final cohort losses (rank correlation across seasoned
  vintages); surfaced in a report section.

### 🟡 G12 — No override/exception, rating-migration, peer, or macro indicators
- **Guidance:** guide Steps 3–4; APG 220 para 67(c). `[mostly data-inherent]`
- **Resolution (docs):** `assumptions.md` states which MI categories are infeasible on public data
  (override/exception, rating migration, peer) and why; a macro-context note accompanies the vintage
  curves.

### ⚪ G25 — Third-party / originator oversight feasible but not surfaced
- **Guidance:** APS 220 para 39; APG 220 paras 307–308.
- **Resolution (code):** added an **originator-performance** table (charge-off rate by originating
  lender, worst-first, min-volume filtered) as the third-party-oversight view.

---

## D. IRB parameters, rating governance & validation (APS 113 Att. D; APG 113 paras 134–141)

### 🔴 G13 — PD/LGD/EAD published as RWA/ECL "calibration inputs" but with no validation; the layer was called "N/A"
- **Guidance:** APS 113 Attachment D; APG 113 paras 134–141; APS 220 para 76.
- **Resolution (docs):** `governance.md` now distinguishes *model estimation* (genuinely N/A — no
  fitted model) from *parameter validation* (still required), and adds a parameter-validation note
  covering representativeness (SBA SME vs a target book), data quality, and downturn calibration.

### 🟡 G14 — EAD = gross approval; no CCF for undrawn commitments on revolving facilities
- **Guidance:** APS 113 Attachment D EAD para 6. `[partly data-inherent]`
- **Resolution (docs):** `assumptions.md` caveats revolving EAD as an origination proxy that ignores
  CCF/limit-utilisation (unavailable in FOIA data) and is not a downturn-calibrated EAD.

### 🟡 G15 — No rating refresh / independent review; monitoring-independent-of-origination not stated
- **Guidance:** Basel CRE36.41, CRE36.40, CRE36.57; guide Part 4.1. `[partly N/A]`
- **Resolution (docs):** `governance.md` states the monitoring function's independence from
  origination and cross-references the sister modelling repos for rating refresh/validation.

---

## E. Daily monitoring & collateral (APS 113 Att. D; Basel CRE36.92, CRE36.140)

### 🟡 G16 — No daily monitoring of facility amounts / limit excesses / undrawn lines
- **Guidance:** APS 113 Attachment D EAD para 6; Basel CRE36.92. `[data-inherent]`
- **Resolution (docs):** `governance.md` records that a live deployment requires a daily
  facility/limit-utilisation monitor and that this batch historical demonstrator does not cover it.

### ⚪ G17 — No collateral monitoring beyond a secured/unsecured flag
- **Guidance:** Basel CRE36.140. `[data-inherent]`
- **Resolution (docs):** `assumptions.md` notes collateral valuation/ageing/revaluation monitoring is
  out of scope on FOIA data (would apply if 504 real-estate collateral data is added).

---

## F. Stress testing linkage (APS 220 para 73; APG 220 paras 14, 76)

### 🟡 G18 — Stress fed only the charge-off limit; single historical-replay scenario
- **Guidance:** APS 220 para 73; APG 220 paras 14, 76.
- **Resolution (code):** the scenario set now includes baseline, **adverse (historical crisis)**,
  **severe (worst vintage)**, and a **hypothetical management-overlay** scenario beyond the historical
  replay.

### 🟡 G19 — Stressed LGD/EAD (rising in §10d) was never limit-tested
- **Guidance:** as G18.
- **Resolution (code):** the stress now also computes a **stressed dollar EL rate** and tests it
  against the new EL-rate appetite limit (G6), so stressed severity is bounded by appetite.

---

## G. Validation, governance & data quality (APG 113 para 140; APS 220 paras 28, 76; APG 220 para 64)

### 🟡 G20 — Validation note covered ~4 of the 8 APG 113 elements; no performance/predictiveness element
- **Guidance:** APG 113 para 140; APS 220 para 76.
- **Resolution (docs + code):** `governance.md` now maps validation to **all 8** APG 113 elements, and
  element 3 (performance) is evidenced by the new `validation.py` predictiveness backtest.

### 🟡 G21 — Reporting cadence lighter than the guide's forums; no independent-assurance line
- **Guidance:** guide Step 12; APS 220 para 28.
- **Resolution (docs):** `governance.md` forum table expanded to add front-line (daily/weekly), a group
  credit risk committee, and an **audit committee / independent assurance** line.

### ⚪ G22 — No domain validation of dimension fields; minor count discrepancies
- **Guidance:** APG 220 para 64; APG 113 element 2.
- **Resolution (code):** the data-quality summary now classifies geography into **50 states + DC vs
  territories / military / freely-associated states**, reports **missing lender (27)** and missing
  borrower name, and reconciles the distinct-lender count (the NaN bucket explained the 4,221 vs 4,222).

### ⚪ G23 — HHI thresholds asserted, not validated; industry HHI on a knife-edge (0.1004 vs 0.1000)
- **Guidance:** APG 113 element 4; APG 220 para 64.
- **Resolution (code + docs):** added a configurable **HHI tolerance band** so a marginal 0.0004 breach
  is flagged "AMBER (within tolerance band)" rather than a hard amber, and documented the calibration
  basis in `config.yaml` / `assumptions.md`.

### ⚪ G24 — Country/transfer risk not stated as out-of-scope
- **Guidance:** APS 220 para 36.
- **Resolution (docs):** `assumptions.md` adds a scope line (domestic US SBA; no country/transfer risk).

---

## Items deliberately left as N/A (with rationale)

| Topic | Guidance | Why N/A here |
|---|---|---|
| Fitted rating-model performance / backtesting | APG 113 Ch. 7 | No obligor-level model in this repo; default is an observed status. Lives in the sister modelling repos. Note G13: *parameter* validation is still added. |
| IFRS 9 staging / monthly transition matrices | — | SBA is outcome-level; a coarse 3-stage proxy is the feasible substitute. Full staging lives in the Freddie Mac monitor. |
| Purchased-receivables monitoring | Basel CRE36.117 | No purchased-receivables product in 7(a). |

---

## Scope note

This review covers the **commercial-portfolio-monitoring** repo only. It defers IFRS 9 staging and
PD/LGD model validation to the sister repos (`freddie mac mortgage`, `mortgage-portfolio-monitoring`,
`scorecard pd ead consummer credit`); G13/G15 assume those linkages hold but they cannot be verified
from inside this repo.
