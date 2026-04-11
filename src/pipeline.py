from __future__ import annotations

import argparse
from pathlib import Path

from .concentration import generate_concentration_report
from .config import DEFAULT_OUTPUT_FILES, INPUT_DIR, OUTPUT_DIR, PROCESSED_DIR
from .data_loader import load_input_tables
from .disclosure import generate_credit_quality_table, generate_stage_movement_table
from .early_warning import flag_early_warnings, summarise_early_warnings
from .ecl_engine import calculate_ecl, summarise_ecl_by_segment, summarise_ecl_by_stage
from .lifetime_pd import assign_lifetime_pd
from .macro_overlay import apply_macro_overlay, probability_weight_ecl
from .migration import build_transition_matrix, identify_downgrades
from .staging import classify_stage, summarise_staging
from .utils import ensure_directories, save_dataframe


def run_pipeline(
    input_dir: str | Path | None = None,
    processed_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    refresh_demo_inputs: bool = False,
    persist: bool = True,
) -> dict:
    input_path = Path(input_dir) if input_dir is not None else INPUT_DIR
    processed_path = Path(processed_dir) if processed_dir is not None else PROCESSED_DIR
    output_path = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    ensure_directories(input_path, processed_path, output_path)

    # 1. Load inputs
    inputs = load_input_tables(input_dir=input_path, refresh_demo=refresh_demo_inputs)
    el_df = inputs["loan_level_el"]
    prior_df = inputs["prior_period"]

    # 2. Classify AASB 9 stages
    el_df = classify_stage(el_df)

    # 3. Build lifetime PD curves for Stage 2
    el_df = assign_lifetime_pd(el_df)

    # 4. Apply macro overlays and calculate scenario ECL
    scenario_df = apply_macro_overlay(el_df)
    scenario_df = calculate_ecl(scenario_df)

    # 5. Probability-weight ECL across scenarios
    pw_ecl = probability_weight_ecl(scenario_df)
    el_df = el_df.merge(pw_ecl, on="facility_id", how="left")

    # Also compute base-case ECL for reference
    base_ecl = scenario_df[scenario_df["scenario"] == "base"][["facility_id", "ecl_scenario"]].copy()
    base_ecl.rename(columns={"ecl_scenario": "ecl_base"}, inplace=True)
    el_df = el_df.merge(base_ecl, on="facility_id", how="left")

    # 6. Summaries
    ecl_by_stage = summarise_ecl_by_stage(el_df)
    ecl_by_segment = summarise_ecl_by_segment(el_df, group_fields=["product_type"])

    # 7. Concentration risk
    concentration = generate_concentration_report(el_df)

    # 8. Migration tracking
    # Ensure prior_df has staging
    if "aasb9_stage" not in prior_df.columns:
        prior_df = classify_stage(prior_df)
    transition_grade = build_transition_matrix(el_df, prior_df, field="internal_risk_grade")
    transition_stage = build_transition_matrix(el_df, prior_df, field="aasb9_stage")

    # 9. Early warning signals
    el_df = flag_early_warnings(el_df)
    ew_summary = summarise_early_warnings(el_df)

    # 10. APS 330 disclosure tables
    aps330_movement = generate_stage_movement_table(el_df, prior_df)
    aps330_quality = generate_credit_quality_table(el_df)

    if persist:
        save_dataframe(el_df, output_path / DEFAULT_OUTPUT_FILES["facility_ecl"].name)
        save_dataframe(ecl_by_stage, output_path / DEFAULT_OUTPUT_FILES["ecl_by_stage"].name)
        save_dataframe(ecl_by_segment, output_path / DEFAULT_OUTPUT_FILES["ecl_by_segment"].name)
        save_dataframe(concentration, output_path / DEFAULT_OUTPUT_FILES["concentration"].name)
        save_dataframe(transition_grade.reset_index(), output_path / DEFAULT_OUTPUT_FILES["transition_grade"].name)
        save_dataframe(transition_stage.reset_index(), output_path / DEFAULT_OUTPUT_FILES["transition_stage"].name)
        save_dataframe(ew_summary, output_path / DEFAULT_OUTPUT_FILES["early_warning"].name)
        save_dataframe(aps330_movement, output_path / DEFAULT_OUTPUT_FILES["aps330_stage_movement"].name)
        save_dataframe(aps330_quality, output_path / DEFAULT_OUTPUT_FILES["aps330_credit_quality"].name)
        save_dataframe(el_df, processed_path / "ecl_dataset.csv")

    return {
        "inputs": inputs,
        "facility_ecl": el_df,
        "ecl_by_stage": ecl_by_stage,
        "ecl_by_segment": ecl_by_segment,
        "concentration": concentration,
        "transition_grade": transition_grade,
        "transition_stage": transition_stage,
        "early_warning": ew_summary,
        "aps330_stage_movement": aps330_movement,
        "aps330_credit_quality": aps330_quality,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AASB 9 ECL and Portfolio Monitor pipeline.")
    parser.add_argument(
        "--refresh-demo-inputs",
        action="store_true",
        help="Regenerate the synthetic input files before running the pipeline.",
    )
    args = parser.parse_args()

    result = run_pipeline(refresh_demo_inputs=args.refresh_demo_inputs, persist=True)
    n = len(result["facility_ecl"])
    total_ecl = float(result["facility_ecl"]["ecl_probability_weighted"].sum())
    print(f"Facilities processed: {n}")
    print(f"Probability-weighted ECL: ${total_ecl:,.2f}")
    print(f"\nStaging summary:")
    print(result["ecl_by_stage"].to_string(index=False))
    print(f"\nConcentration report:")
    print(result["concentration"].to_string(index=False))
    print(f"\nOutput files written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
