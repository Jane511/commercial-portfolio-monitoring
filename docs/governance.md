# Governance, reporting & independent validation

How this monitoring framework would sit inside a bank's risk governance. The
analytics in this repo are the *content* of a monitoring pack; this note covers
the *governance wrapper* around them — who sees what, how often, and how the
framework itself is kept honest. References: APS 220 paras 28 and 75–76,
APG 113 para 140, APS 330 (Pillar 3).

> Scope note. This is a public-data demonstrator built on the SBA 7(a) FOIA
> dataset. It is **not** a regulated entity's governance document; it shows the
> framing a credit-portfolio monitor would carry into a real Layer-3 monitoring
> function.

## 1. Reporting cadence to forums

| Forum | Cadence | What they receive | Decision rights |
|---|---|---|---|
| Credit Risk team | Monthly | Full monitoring pack (`outputs/report.md`): concentration, charge-off, vintage, early-warning, problem-exposure, the RAG dashboard | Investigate amber/red items; prepare actions |
| Credit Committee | Quarterly | RAG dashboard (section: board dashboard) + actions table + stress scenario | Approve breach actions; set/adjust sub-limits |
| Board Risk Committee | Quarterly / on red breach | Dashboard summary, any red-limit breaches and the stress result | Ratify risk appetite; escalate origination/pricing change |

The **review cycle** column on each appetite limit (`config.yaml` →
`risk_appetite`) is the per-limit cadence; the table above is the forum-level
roll-up. A red breach is reported out of cycle.

## 2. Risk appetite ownership

Each limit in the appetite framework (CML-2) names an **owner** and a **breach
action**. The owner is accountable for the metric staying within appetite and
for executing the breach action when it does not. The appetite statement itself
(the amber/red bounds) is owned by the Board Risk Committee and reviewed at
least annually (APS 220 para 28 — the Board sets and oversees risk appetite).

## 3. Independent validation

The monitoring **framework** — its metrics, thresholds, and the code that
produces them — would be subject to **independent annual validation** by a party
not involved in building or running it (APS 220 paras 75–76). A validation pass
would cover, at minimum:

- **Data lineage & quality** — that the base table faithfully represents the
  source extracts (the `00_data_quality_summary` table is the first input).
- **Metric correctness** — recomputation of concentration, charge-off and
  vintage metrics from source; reconciliation to the published tables.
- **Threshold calibration** — whether the appetite amber/red bounds remain
  appropriate for the book and the cycle.
- **Stress assumptions** — that the crisis multiplier and its application remain
  defensible (APG 220 para 76).

The `pytest` suite (`tests/`) is the *continuous* control that the analytics
behave as specified; it is a complement to, not a substitute for, periodic
independent validation.

## 4. Model risk — Layer 4 is N/A here (by design)

APRA's model-risk expectations (APG 113 para 140; the PD/LGD/EAD
model-performance layer) **do not apply to this repo**: there is **no rating or
capital model** in the commercial monitor. Default is an observed status
(`LoanStatus == CHGOFF`), not a model output, and the charge-off/vintage views
are realised outcomes, not estimates. There is therefore nothing here to
back-test for discrimination, calibration or stability.

The model-performance layer lives in the **sister modelling repositories**:

- `scorecard pd ead consummer credit` — PD/EAD scorecard development & validation.
- `freddie mac mortgage` / `mortgage-portfolio-monitoring` — mortgage default
  modelling and IFRS 9-style staging / transition matrices.

Cross-reference those repos for Layer-4 (model performance & validation); this
repo is Layer-3 (portfolio monitoring) only.

## 5. APS 330 / Pillar 3 linkage

The concentration and credit-quality outputs (exposure by industry/geography,
charge-off/impairment by segment) are the same primitives that feed a **Pillar 3
(APS 330) credit-risk disclosure**. The `05_aps330_style_credit_quality` table
is laid out in that **format for familiarity only** — built from public SBA data,
it is **not** a regulated entity's disclosure and is labelled as such everywhere
it appears. In a real bank these monitoring outputs would be a feeder into the
periodic Pillar 3 disclosure, not the disclosure itself.
