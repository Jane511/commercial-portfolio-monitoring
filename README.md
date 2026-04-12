# Commercial Portfolio Monitoring & ECL Project

This repository is the post-origination monitoring and impairment reporting layer in the commercial credit-risk stack. It uses loan-level expected loss data, prior-period snapshots, and optional pricing or capital inputs to produce facility-level ECL outputs, stage summaries, transition matrices, early-warning views, and concentration reports. The project is positioned as a portfolio monitoring layer rather than a front-line model build.

## What this repo is

This project demonstrates how a commercial portfolio can be monitored after origination using staging, lifetime PD, scenario-weighted ECL, migration, and concentration analytics. It is designed as a portfolio project, so the workflow is transparent, the assumptions are clearly disclosed, and the outputs are shaped for recruiter-friendly review.

## Where it sits in the stack

Upstream inputs:
- `expected-loss-engine-commercial`
- optional facility-level capital context from `RWA-capital-commercial`
- optional pricing context from `RAROC-pricing-and-return-hurdle`
- prior-period snapshots and reviewer inputs staged under `data/`

Downstream use:
- portfolio monitoring packs and early-warning review
- impairment and stage-movement summaries
- employer-ready disclosure and management-reporting examples

## Key outputs

- `data/output/facility_ecl.csv`
- `data/output/ecl_summary_by_stage.csv`
- `data/output/ecl_summary_by_segment.csv`
- `data/output/concentration_report.csv`
- `data/output/transition_matrix_grade.csv`
- `data/output/transition_matrix_stage.csv`
- `data/output/early_warning_summary.csv`
- `data/output/aps330_stage_movement.csv`
- `data/output/aps330_credit_quality.csv`

## Repo structure

- `data/`: tracked folder guide plus runtime-created `input/`, `manual/`, `processed/`, and `output/` subfolders used during local runs
- `src/`: reusable staging, lifetime PD, ECL, migration, and monitoring modules
- `scripts/`: wrapper scripts for pipeline execution
- `docs/`: methodology and disclosure notes
- `notebooks/`: reviewer-facing notebook index and walkthrough placeholders
- `tests/`: validation and regression checks

## How to run

```powershell
python -m src.pipeline --refresh-demo-inputs
```

Or:

```powershell
python scripts/run_pipeline.py --refresh-demo-inputs
```

Run validation tests:

```powershell
pytest
```

## Limitations / Demo-Only Note

- All monitoring inputs are synthetic or simulated for demonstration purposes.
- The repo shows a practical monitoring and impairment workflow, not a production accounting, disclosure, or regulatory reporting platform.
- Scenario weights, staging thresholds, and early-warning rules are simplified so the logic remains easy to inspect.
