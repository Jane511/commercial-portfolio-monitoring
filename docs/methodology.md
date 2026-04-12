# Methodology

## Workflow

1. Stage or regenerate the demo monitoring inputs under `data/input/`.
2. Classify current facilities into AASB 9 stages using arrears, watchlist, and downgrade signals.
3. Build lifetime PD curves for Stage 2 exposures.
4. Apply macro overlays and calculate scenario ECL.
5. Probability-weight scenario ECL back to a facility-level monitoring dataset.
6. Aggregate outputs into stage, segment, concentration, migration, and disclosure summaries.
7. Export processed and reviewer-facing output tables under `data/processed/` and `data/output/`.

## Design choices

- The pipeline is intentionally flat and explainable so reviewers can trace facility-level logic into portfolio-level summaries.
- Monitoring context is modular: expected-loss inputs are required, while pricing and capital context remain optional enrichments.
- All outputs are CSV-first so they can be reused in downstream reporting packs or presentation material without extra tooling.
