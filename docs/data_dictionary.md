# Data Dictionary

## Core staged inputs

- `data/input/loan_level_el.csv`: facility-level expected-loss style dataset used as the core monitoring input.
- `data/input/exposure_level_rwa.csv`: optional capital-style enrichment used for monitoring context.
- `data/input/facility_raroc.csv`: optional pricing-style enrichment used for reviewer-facing comparisons when available.
- `data/input/prior_period_snapshot.csv`: prior-period facility snapshot used for staging and migration analysis.

## Main outputs

- `data/output/facility_ecl.csv`: facility-level ECL dataset with staging, scenario, and alert fields.
- `data/output/ecl_summary_by_stage.csv`: ECL summary table by AASB 9 stage.
- `data/output/ecl_summary_by_segment.csv`: ECL summary table by product segment.
- `data/output/concentration_report.csv`: concentration metrics and limit-style flags across the monitored portfolio.
- `data/output/transition_matrix_grade.csv`: prior-to-current migration matrix by internal risk grade.
- `data/output/transition_matrix_stage.csv`: prior-to-current migration matrix by AASB 9 stage.
- `data/output/early_warning_summary.csv`: aggregated early-warning indicator summary.
- `data/output/aps330_stage_movement.csv`: disclosure-style stage movement summary.
- `data/output/aps330_credit_quality.csv`: disclosure-style credit-quality summary.
