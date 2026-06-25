# Governance, reporting & independent validation

How this monitoring framework would sit inside a bank's risk governance. The
analytics in this repo are the *content* of a monitoring pack; this note covers
the *governance wrapper* around them — who sees what, how often, who owns the
appetite, how problem exposures are escalated, and how the framework itself is
kept honest. References: APS 220 paras 20, 28, 33, 73, 75–76; APG 220 paras 63,
66–68; APG 113 paras 134–141; Basel CRE36.41/36.57/36.92/36.140; APS 330.

> Scope note. This is a public-data demonstrator built on the SBA 7(a) FOIA
> dataset. It is **not** a regulated entity's governance document; it shows the
> framing a credit-portfolio monitor would carry into a real Layer-3 monitoring
> function. See `docs/compliance_gap_review.md` for the regulatory gap review
> this governance note responds to.

## 1. Reporting cadence to forums

A real programme reports at several altitudes simultaneously (guide Step 12). The
forums below span front-line operations to the Board; this repo's monthly pack
(`outputs/reports/report.md`) is the *content* that flows up the stack.

| Forum | Cadence | What they receive | Decision rights |
|---|---|---|---|
| Front-line credit operations | **Daily / weekly** | Limit utilisation & excesses, new originations, early-arrears / problem-exposure flow, exceptions | Action individual exposures; clear exceptions |
| Credit Risk team | Monthly | Full monitoring pack: concentration, charge-off, vintage, early-warning, problem-exposure, originator performance, the RAG dashboard | Investigate amber/red items; prepare actions |
| Group Credit Risk Committee | Monthly | Whole-portfolio MI, concentration, model/parameter performance, stress | Set/adjust sub-limits; endorse actions |
| Credit Committee | Quarterly | RAG dashboard + actions table + stress ladder | Approve breach actions; set/adjust sub-limits |
| Board Risk Committee | Quarterly / on red breach | Dashboard summary, red-limit breaches, stress result, appetite review | Ratify risk appetite & tolerance; escalate origination/pricing change |
| Board Audit Committee | Quarterly | **Independent assurance / internal-audit findings** on the monitoring framework, validation outcomes | Commission remediation; assurance sign-off |

The **review cycle** column on each appetite limit (`config.yaml` →
`risk_appetite`) is the per-limit *monitoring* cadence; the table above is the
forum-level roll-up. A red breach is reported out of cycle.

> **Daily facility/limit monitoring (APS 113 Att. D EAD para 6; Basel CRE36.92).**
> A live deployment must monitor facility amounts, outstanding-vs-committed
> balances, undrawn lines and limit excesses **daily**, per borrower and grade /
> pool. This repo is a *periodic batch* on historical, outcome-level data with no
> running balance or facility limit, so it does **not** implement daily limit
> monitoring; that control sits in the live limit-management system, not here.

## 2. Risk appetite ownership, calibration & review

Each limit in the appetite framework (CML-2) names an **owner** and a **breach
action**; the owner is accountable for the metric staying within appetite and
for executing the breach action when it does not.

**Appetite vs tolerance (APS 220 para 20).** Every limit carries two bounds:

- **`amber` = credit-risk appetite** — the level the ADI is *prepared to accept*.
  Crossing it is an early warning that triggers monitoring and the breach action.
- **`red` = credit-risk tolerance** — the *maximum the ADI is willing to operate
  within*. Crossing it is a hard breach escalated to the Board Risk Committee out
  of cycle.

**Calibration basis.** Each bound is anchored to (a) the training guide's
illustrative levels (Step 1 / Part 5.1), (b) the realised SBA book, then widened
where the programme's structure makes the illustrative bank level non-binding —
e.g. the single-name limits sit far above any achievable value because SBA 7(a)
has >900k borrowers, and the charge-off / EL / NPL limits reflect that SME
guarantee lending runs materially higher loss than a secured retail book. The
HSBC-style "knife-edge" issue is handled by a **tolerance band**
(`concentration.hhi_tolerance_band`) so a marginal cross is a watch item, not a
step-change breach.

**Ownership & review process.** The appetite statement (the amber/red bounds) is
**owned and approved by the Board Risk Committee** and reviewed **at least
annually**, or sooner if the portfolio, strategy or cycle shifts materially
(APS 220 paras 20/28). The process: Credit Risk proposes bounds with supporting
analysis → Group Credit Risk Committee endorses → Board Risk Committee approves →
breaches and proposed recalibrations are reported back each cycle.

## 2b. Problem-exposure identification & escalation (APS 220 para 33)

Problem exposures are identified early and escalated through a defined workflow
(APG 220 para 63; guide Step 8). In this repo the SBA statuses map onto the
workflow as follows (the analytics surface the population at each stage; the
*actions* are the governance overlay a live function would apply):

| Stage | Trigger (SBA-feasible proxy) | Action |
|---|---|---|
| Watch list | Adverse forward indicator (early-MOB deterioration; segment in the early-warning table) | Increase monitoring frequency; lender review |
| Heightened risk | `DELINQ` / `PSTDUE` (arrears) | Restructure / strengthen security / lower limit |
| Pre-default | `LIQUID` (in liquidation); `PURCH(NOT C/O)` (SBA guaranty purchased) | Collections; reassess classification & provision |
| Default | `CHGOFF` (charge-off) | Move to NPL; specific provision; workout team |
| Charge-off | No further recovery expected | Write-off; continue post-charge-off recovery |

`DELINQ` / `PSTDUE` / `LIQUID` / `PURCH(NOT C/O)` together with `CHGOFF` form the
**non-performing (NPL) proxy** reported throughout the pack (gap review G7/G8).

> **Restructured / hardship & provisions (APG 220 para 68; APS 220 para 33).**
> The SBA FOIA outcome file carries **no** restructured/hardship flag and **no**
> provision/ECL balances, so cure rates, concession volumes and provision
> coverage cannot be computed here. In a live programme these dashboards
> (new-request volume by product, approval & cure rates, provisions and realised
> loss on the concession book) are required; here they are an acknowledged data
> gap, deferred to the sister repos that carry a performance panel.

## 3. Independent validation — the 8-element framework

The monitoring **framework** — its metrics, thresholds, and the code that
produces them — is subject to **independent annual validation** by a party not
involved in building or running it (APS 220 paras 75–76; APG 113 para 140). The
validation maps to the **eight APG 113 elements**:

| # | Element | How it applies to this monitor |
|---|---|---|
| 1 | Design & construction | Logic of the MI, choice of indicators, alignment to risk appetite |
| 2 | Data quality | Source reconciliation; the `00_data_quality_summary` domain checks (geography classification, missing lender/borrower, NPL count) |
| 3 | **Performance / predictiveness** | The `validation.py` backtest that leading indicators (early-MOB, mix) actually rank cohorts by *final* loss — report §8c |
| 4 | Conservative adjustments | Watch-list multiples; the HHI tolerance band; appetite bounds widened/narrowed with rationale |
| 5 | Implementation | The pipeline runs reproducibly; the `pytest` suite is the continuous control |
| 6 | Use | The dashboard & actions table are framed for the governance forums in §1 (the "use test") |
| 7 | Documentation | These docs (`methodology`, `assumptions`, `data_dictionary`, this note) are kept current |
| 8 | Management reporting | The board RAG dashboard leads the pack and reaches the right forum on the right cadence |

The `pytest` suite (`tests/`) is the *continuous* control that the analytics
behave as specified; it complements, but does not replace, periodic independent
validation. The stress multiplier and its application are validated under element
4 (APG 220 para 76).

## 3b. Parameter validation — distinct from model validation

Section 10 of the pack extracts **realised** PD / LGD / EAD / EL as calibration
anchors. There is **no fitted obligor-level model** here, so *model-estimation*
backtesting (discrimination, calibration, stability of a scorecard) is genuinely
N/A — but that does **not** make the parameters validation-free (gap review G13).
A parameter used for pricing / ECL / RWA must still be validated for:

- **Representativeness** — SBA 7(a) is small, often unsecured, government-guaranteed
  SME lending; its realised PD/LGD are **not** transferable to a different target
  book without adjustment. These figures are an *anchor to reason from*, not a
  drop-in calibration.
- **Data quality** — outcome-level, exposure measured at approval (no running
  balance), default = charge-off (lagging vs 90+DPD/UTP). See `assumptions.md`.
- **Downturn calibration** — the parameter stress (report §10d / §9) gives the
  downturn-PD/LGD/EL read off the 2006–08 cohorts; a downturn-EAD (CCF) cannot be
  derived without limit/utilisation data and is an acknowledged gap.

## 4. Model risk — Layer 4 lives in the sister repos

APRA's full model-risk expectations (APG 113 Ch. 7 — rating-system design, annual
rating refresh per Basel CRE36.41, independent rating review per CRE36.40/36.57)
apply to a **fitted rating/capital model**, of which there is none in this repo.
The model-performance / backtesting layer lives in the sister modelling repos:

- `scorecard pd ead consummer credit` — PD/EAD scorecard development & validation.
- `freddie mac mortgage` / `mortgage-portfolio-monitoring` — mortgage default
  modelling and IFRS 9-style staging / transition matrices.

Cross-reference those repos for Layer-4 (model performance & validation); this
repo is Layer-3 (portfolio monitoring) only. **Independence (Basel CRE36.57;
guide Part 4.1):** the monitoring function is, by design, independent of loan
origination — it reports through the risk line (Head of Credit Risk → CCO →
Board Risk Committee), not through the originating business. **Collateral
monitoring (Basel CRE36.140)** and **country/transfer risk (APS 220 para 36)**
are out of scope on this domestic, collateral-unvalued dataset — see
`assumptions.md`.

## 5. APS 330 / Pillar 3 linkage

The concentration and credit-quality outputs (exposure by industry/geography,
charge-off/impairment by segment) are the same primitives that feed a **Pillar 3
(APS 330) credit-risk disclosure**. The `05_aps330_style_credit_quality` table is
laid out in that **format for familiarity only** — built from public SBA data, it
is **not** a regulated entity's disclosure and is labelled as such everywhere it
appears. In a real bank these monitoring outputs would be a feeder into the
periodic Pillar 3 disclosure, not the disclosure itself.
