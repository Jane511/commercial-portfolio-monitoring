# Data Folder Guide

The public repo keeps the `data/` folder lightweight. The monitoring pipeline creates the working subfolders below during local runs:

- `input/`: staged upstream expected-loss, pricing, and capital inputs
- `manual/`: optional analyst overrides and reviewer-supplied adjustments
- `processed/`: intermediate working tables generated during the run
- `output/`: final ECL, staging, migration, concentration, and disclosure tables

These runtime folders are gitignored so the repository stays clean between runs.
