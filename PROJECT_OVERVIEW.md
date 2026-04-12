# Project Overview - portfolio-monitor-commercial

`portfolio-monitor-commercial` is the post-origination monitoring and impairment-reporting layer in the commercial credit-risk stack.

## Portfolio role

This repo takes expected-loss outputs and turns them into monitoring-ready ECL, staging, migration, early-warning, and concentration views for a commercial lending portfolio.

## Upstream inputs

- `expected-loss-engine-commercial`
- optional facility-level capital context from `RWA-capital-commercial`
- optional pricing context from `RAROC-pricing-and-return-hurdle`
- prior-period snapshots and reviewer-supplied overrides staged under `data/`

## Main outputs

- `data/output/facility_ecl.csv`
- `data/output/ecl_summary_by_stage.csv`
- `data/output/ecl_summary_by_segment.csv`
- `data/output/concentration_report.csv`
- `data/output/transition_matrix_grade.csv`
- `data/output/transition_matrix_stage.csv`
- `data/output/early_warning_summary.csv`
- `data/output/aps330_stage_movement.csv`
- `data/output/aps330_credit_quality.csv`

## Public repo structure

- `data/README.md` explains the runtime-created input, manual, processed, and output folders.
- `docs/` contains methodology, assumptions, data definitions, and validation notes.
- `notebooks/` contains reviewer-facing notebook guidance.
- `src/` contains the reusable monitoring and ECL pipeline modules.
- `scripts/` contains the command-line entrypoint.
- `tests/` contains smoke and regression checks for the public workflow.

## Run commands

- `python -m src.pipeline --refresh-demo-inputs`
- `python scripts/run_pipeline.py --refresh-demo-inputs`
- `pytest`
