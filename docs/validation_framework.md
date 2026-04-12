# Validation Framework

- The smoke test in `tests/test_pipeline.py` runs the pipeline with regenerated demo inputs and checks that the required output tables are produced.
- Staging outputs are checked indirectly through the generated stage summary and stage migration tables.
- Probability-weighted ECL is reconciled at facility level before the summary tables are written.
- Concentration, early-warning, and disclosure outputs are written as separate tables so reviewers can inspect each control surface independently.
- Local runs should finish with populated `data/output/` tables and no import errors from the command-line entrypoint.
