# Project Overview

`portfolio-monitor-commercial` is the post-origination monitoring and impairment-reporting layer in the public commercial credit-risk stack.

## Portfolio role

It turns expected-loss outputs, prior-period snapshots, and optional pricing or capital context into monitoring-ready ECL, staging, migration, early-warning, and concentration views.

## Upstream inputs

- `expected-loss-engine-commercial`
- optional facility-level capital context from `RWA-capital-commercial`
- optional pricing context from `RAROC-pricing-and-return-hurdle`
- prior-period snapshots and reviewer-supplied overrides staged under `data/`

## Downstream consumers

No required downstream modelling repo. Outputs are intended for monitoring packs, impairment review, and management reporting, with optional reuse in capital or pricing discussion packs.
