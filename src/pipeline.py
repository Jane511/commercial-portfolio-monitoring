"""End-to-end SBA commercial-portfolio monitoring pipeline.

Real SBA 7(a) loan data in -> monitoring tables, charts, and a report out.
Run with::

    python -m src.run_pipeline                # uses data/input + config.yaml
    python -m src.run_pipeline --config my_config.yaml
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from . import chargeoff as co
from . import concentration as conc
from . import problem_exposure as pe
from . import report as rpt
from . import transitions, vintage
from .base_table import build_base_table
from .charts import (
    plot_chargeoff_bar,
    plot_chargeoff_by_vintage,
    plot_concentration_bar,
    plot_loan_age_transition,
    plot_vintage_curves,
    plot_vintage_heatmap,
    save_chart,
)
from .config import CHARTS_DIR, INPUT_DIR, OUTPUT_DIR, OUTPUT_TABLES, TABLES_DIR, load_config
from .data_loader import data_quality_summary, load_clean
from .early_warning import flag_high_risk_segments
from .logger import get_logger
from .utils import ensure_directories, save_dataframe

_log = get_logger(__name__)


def run_pipeline(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    config_path: str | None = None,
    persist: bool = True,
    make_charts: bool = True,
) -> dict:
    """Run the full pipeline; return a dict of every result table.

    When *persist* is True, tables are written under ``outputs/tables/``,
    charts under ``outputs/charts/``, and the report to ``outputs/report.md``.
    """
    t0 = time.perf_counter()
    cfg = load_config(config_path)
    input_path = Path(input_dir) if input_dir is not None else INPUT_DIR
    out_path = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    tables_dir = (out_path / "tables") if output_dir else TABLES_DIR
    charts_dir = (out_path / "charts") if output_dir else CHARTS_DIR
    if persist:
        ensure_directories(tables_dir, charts_dir)

    # --- 00 Load & clean -------------------------------------------------- #
    _log.info("Step 1/6 — Load & clean SBA data")
    loans = load_clean(input_path, config=cfg)
    dq = data_quality_summary(loans, config=cfg)

    # --- 01 Monitoring base table ---------------------------------------- #
    _log.info("Step 2/6 — Build monitoring base table")
    base = build_base_table(loans, config=cfg)

    # --- 02 Concentration ------------------------------------------------- #
    _log.info("Step 3/6 — Concentration analytics")
    conc_industry = conc.concentration_by(base, "industry")
    conc_state = conc.concentration_by(base, "state")
    conc_lender = conc.concentration_by(base, "lender")
    conc_hhi = conc.hhi_summary(base)

    # --- 03 Charge-off & vintage cohorts ---------------------------------- #
    _log.info("Step 4/6 — Charge-off rates & vintage cohort curves")
    co_industry = co.chargeoff_by_industry(base)
    co_size = co.chargeoff_by_size_band(base)
    co_vintage = co.chargeoff_by_vintage(base)
    vintage_curves = vintage.compute_vintage_curves(base, config=cfg)

    # --- 04 Loan-age transitions & early warning -------------------------- #
    _log.info("Step 5/6 — Loan-age transitions & early-warning segments")
    age_transition = transitions.loan_age_transition(base)
    early = flag_high_risk_segments(base, config=cfg)
    pe_overview = pe.problem_exposure_overview(base, config=cfg)
    pe_by_industry = pe.problem_exposure_by(base, "industry")

    # --- 05 Monitoring pack / report -------------------------------------- #
    _log.info("Step 6/6 — Stage proxy, APS 330-style table & report")
    stage_proxy = rpt.stage_proxy_summary(base, config=cfg)
    aps330 = rpt.aps330_style_credit_quality(base)
    report_md = rpt.build_markdown_report(
        dq=dq, hhi=conc_hhi, co_industry=co_industry, co_vintage=co_vintage,
        early_warning=early, stage_proxy=stage_proxy,
        problem_exposure=pe_overview,
    )

    results = {
        "data_quality": dq,
        "base_table_sample": base.head(500),
        "concentration_industry": conc_industry,
        "concentration_state": conc_state,
        "concentration_lender": conc_lender,
        "concentration_hhi": conc_hhi,
        "chargeoff_by_industry": co_industry,
        "chargeoff_by_size": co_size,
        "chargeoff_by_vintage": co_vintage,
        "vintage_curves": vintage_curves.reset_index(),
        "loan_age_transitions": age_transition,
        "early_warning": early,
        "problem_exposure_overview": pe_overview,
        "problem_exposure_by_industry": pe_by_industry,
        "stage_proxy": stage_proxy,
        "aps330_credit_quality": aps330,
    }

    if persist:
        for key, path in OUTPUT_TABLES.items():
            target = tables_dir / path.name if output_dir else path
            save_dataframe(results[key], target)
        (out_path / "report.md").write_text(report_md, encoding="utf-8")
        _log.info("Report written -> %s", out_path / "report.md")

        if make_charts:
            _save_charts(
                charts_dir, conc_industry, conc_state, co_industry,
                co_vintage, vintage_curves, age_transition,
            )

    _log.info("Pipeline complete in %.1fs — %d loans, %d tables",
              time.perf_counter() - t0, len(base), len(results))
    results["report_md"] = report_md
    results["base_table"] = base
    return results


def _save_charts(charts_dir, conc_industry, conc_state, co_industry,
                 co_vintage, vintage_curves, age_transition) -> None:
    save_chart(plot_concentration_bar(conc_industry, "industry",
               "Exposure concentration by industry (NAICS sector)"),
               charts_dir / "concentration_industry.png")
    save_chart(plot_concentration_bar(conc_state, "state",
               "Exposure concentration by borrower state (top-N)"),
               charts_dir / "concentration_state.png")
    save_chart(plot_chargeoff_bar(co_industry, "industry",
               "Charge-off rate by industry"),
               charts_dir / "chargeoff_by_industry.png")
    save_chart(plot_chargeoff_by_vintage(co_vintage),
               charts_dir / "chargeoff_by_vintage.png")
    save_chart(plot_vintage_curves(vintage_curves),
               charts_dir / "vintage_cohort_curves.png")
    save_chart(plot_vintage_heatmap(vintage_curves),
               charts_dir / "vintage_cohort_heatmap.png")
    save_chart(plot_loan_age_transition(age_transition),
               charts_dir / "loan_age_transition.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="SBA commercial-portfolio monitoring pipeline")
    parser.add_argument("--input-dir", default=None, help="Directory of SBA FOIA CSVs")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: outputs/)")
    parser.add_argument("--config", default=None, help="Path to a config.yaml")
    parser.add_argument("--no-charts", action="store_true", help="Skip chart generation")
    parser.add_argument("--no-persist", action="store_true", help="Compute only; write nothing")
    args = parser.parse_args()

    run_pipeline(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        config_path=args.config,
        persist=not args.no_persist,
        make_charts=not args.no_charts,
    )


if __name__ == "__main__":
    main()
