from __future__ import annotations

from pathlib import Path

import pandas as pd


def ensure_directories(*paths: str | Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def save_dataframe(df: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    ensure_directories(target.parent)
    df.to_csv(target, index=False)


def weighted_average(values: pd.Series, weights: pd.Series) -> float:
    valid = values.notna() & weights.notna()
    if not valid.any():
        return float(values.dropna().mean()) if not values.dropna().empty else 0.0
    total_weight = float(weights.loc[valid].sum())
    if total_weight <= 0:
        return float(values.loc[valid].mean()) if valid.any() else 0.0
    return float((values.loc[valid] * weights.loc[valid]).sum() / total_weight)
