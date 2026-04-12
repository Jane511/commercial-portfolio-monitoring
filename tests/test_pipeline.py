from __future__ import annotations

from pathlib import Path

from src.pipeline import run_pipeline


def test_pipeline_generates_required_outputs() -> None:
    artifacts_root = Path("tests") / "_artifacts"
    result = run_pipeline(
        input_dir=artifacts_root / "input",
        processed_dir=artifacts_root / "processed",
        output_dir=artifacts_root / "output",
        refresh_demo_inputs=True,
        persist=True,
    )

    assert not result["facility_ecl"].empty
    assert not result["ecl_by_stage"].empty
    assert not result["ecl_by_segment"].empty
    assert not result["concentration"].empty
    assert not result["early_warning"].empty
    assert (artifacts_root / "output" / "facility_ecl.csv").exists()
    assert (artifacts_root / "output" / "ecl_summary_by_stage.csv").exists()
    assert (artifacts_root / "output" / "concentration_report.csv").exists()
    assert (artifacts_root / "processed" / "ecl_dataset.csv").exists()
