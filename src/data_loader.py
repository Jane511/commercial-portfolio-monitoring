from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_INPUT_FILES, INPUT_DIR, MANUAL_DIR, SIBLING_INPUT_CANDIDATES
from .demo_data import build_demo_el_dataset, build_demo_prior_period, build_demo_rwa_dataset
from .utils import ensure_directories, save_dataframe


def _try_sibling(key: str) -> Path | None:
    candidates = SIBLING_INPUT_CANDIDATES.get(key, ())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def stage_demo_inputs(
    input_dir: str | Path | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    inp = Path(input_dir) if input_dir is not None else INPUT_DIR
    ensure_directories(inp)

    file_map = {
        "loan_level_el": inp / DEFAULT_INPUT_FILES["loan_level_el"].name,
        "exposure_level_rwa": inp / DEFAULT_INPUT_FILES["exposure_level_rwa"].name,
        "prior_period": inp / DEFAULT_INPUT_FILES["prior_period"].name,
    }

    # Try sibling module paths first
    for key in ("loan_level_el", "exposure_level_rwa"):
        if not file_map[key].exists():
            sibling = _try_sibling(key)
            if sibling is not None:
                file_map[key] = sibling

    need_demo = overwrite or not file_map["loan_level_el"].exists()
    if need_demo:
        el_df = build_demo_el_dataset()
        rwa_df = build_demo_rwa_dataset(el_df)
        prior_df = build_demo_prior_period(el_df)
        save_dataframe(el_df, file_map["loan_level_el"])
        save_dataframe(rwa_df, file_map["exposure_level_rwa"])
        save_dataframe(prior_df, file_map["prior_period"])
    elif not file_map["prior_period"].exists():
        el_df = pd.read_csv(file_map["loan_level_el"])
        prior_df = build_demo_prior_period(el_df)
        save_dataframe(prior_df, file_map["prior_period"])

    return file_map


def load_input_tables(
    input_dir: str | Path | None = None,
    refresh_demo: bool = False,
) -> dict[str, pd.DataFrame]:
    file_map = stage_demo_inputs(input_dir=input_dir, overwrite=refresh_demo)
    return {
        "loan_level_el": pd.read_csv(file_map["loan_level_el"]),
        "exposure_level_rwa": pd.read_csv(file_map["exposure_level_rwa"]),
        "prior_period": pd.read_csv(file_map["prior_period"]),
    }
