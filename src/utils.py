from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

# Use the standard library logger directly to avoid a circular import
# (logger.py imports pathlib; utils.py is imported by logger.py indirectly).
_log = logging.getLogger("portfolio_monitor.src.utils")


def ensure_directories(*paths: str | Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def save_dataframe(df: pd.DataFrame, path: str | Path) -> None:
    """Write *df* to CSV (no index), creating parent directories as needed."""
    target = Path(path)
    ensure_directories(target.parent)
    df.to_csv(target, index=False)
    _log.info("Saved %d rows -> %s", len(df), target)


def top_n_share(values: pd.Series, n: int) -> float:
    """Fraction of the total held by the largest *n* segments.

    ``values`` is a per-segment total (e.g. exposure by industry). Returns a
    value in [0, 1]: e.g. 0.42 means the top *n* segments hold 42% of the book.
    """
    total = float(values.sum())
    if total <= 0:
        return 0.0
    return round(float(values.sort_values(ascending=False).head(n).sum() / total), 4)


def herfindahl_index(values: pd.Series) -> float:
    """Herfindahl-Hirschman Index (HHI) = sum of squared segment shares.

    0 (perfectly diversified) -> 1.0 (everything in one segment). ``values`` is
    a per-segment total; shares are computed as value / grand total.
    """
    total = float(values.sum())
    if total <= 0:
        return 0.0
    shares = values / total
    return round(float((shares ** 2).sum()), 6)
