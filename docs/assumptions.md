# Assumptions

- All portfolio inputs are synthetic or simulated for demonstration purposes.
- AASB 9 staging uses transparent SICR thresholds defined in `src/config.py`, including arrears, PD increase, and downgrade triggers.
- Macro overlays use three scenarios: `base`, `downside`, and `severe_downside`, with fixed scenario weights for probability-weighted ECL.
- Optional pricing and capital inputs enrich monitoring context but are not required for the core ECL and staging workflow.
- The repo is intended for portfolio presentation and workflow review, not production accounting, regulatory reporting, or policy sign-off.
