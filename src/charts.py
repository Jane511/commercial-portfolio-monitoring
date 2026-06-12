"""Chart generation for SBA portfolio monitoring outputs.

All functions return a ``matplotlib.figure.Figure`` so callers control whether
to display (``plt.show()``) or save to disk (``save_chart(...)``).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

# Use a headless backend for pipeline/script runs, but never clobber an
# interactive backend a notebook has already chosen (e.g. the inline backend),
# otherwise figures stop rendering inline.
_backend = matplotlib.get_backend().lower()
if "inline" not in _backend and "nbagg" not in _backend and "ipympl" not in _backend:
    try:
        matplotlib.use("Agg")
    except Exception:  # pragma: no cover - backend already fixed
        pass
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)

_PCT = mticker.PercentFormatter(xmax=1, decimals=1)


def save_chart(fig: plt.Figure, path: str | Path, dpi: int = 150) -> None:
    """Save a figure to *path*, creating parent directories as needed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    _log.info("Chart saved to %s", target)


def plot_concentration_bar(
    table: pd.DataFrame,
    label_col: str,
    title: str,
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """Horizontal bar of exposure share for a top-N concentration table."""
    data = table.iloc[::-1]  # largest at top
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(data[label_col].astype(str), data["exposure_share"], color="#2b6cb0")
    ax.xaxis.set_major_formatter(_PCT)
    ax.set_xlabel("Share of total gross approval (exposure)")
    ax.set_title(title, fontweight="bold")
    for y, v in enumerate(data["exposure_share"]):
        ax.text(v, y, f" {v:.1%}", va="center", fontsize=8)
    plt.tight_layout()
    return fig


def plot_chargeoff_bar(
    table: pd.DataFrame,
    label_col: str,
    title: str,
    rate_col: str = "chargeoff_rate_count",
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """Horizontal bar of charge-off rate by segment (worst at top)."""
    data = table.sort_values(rate_col).tail(15)
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(data[label_col].astype(str), data[rate_col], color="#c53030")
    ax.xaxis.set_major_formatter(_PCT)
    ax.set_xlabel("Charge-off rate")
    ax.set_title(title, fontweight="bold")
    for y, v in enumerate(data[rate_col]):
        ax.text(v, y, f" {v:.1%}", va="center", fontsize=8)
    plt.tight_layout()
    return fig


def plot_chargeoff_by_vintage(
    table: pd.DataFrame,
    title: str = "Charge-off rate by approval-year vintage",
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """Bar of charge-off rate per vintage; unseasoned cohorts shown lighter."""
    fig, ax = plt.subplots(figsize=figsize)
    colors = ["#2b6cb0" if s else "#a0aec0" for s in table["fully_seasoned"]]
    ax.bar(table["vintage"].astype(int).astype(str), table["chargeoff_rate_count"], color=colors)
    ax.yaxis.set_major_formatter(_PCT)
    ax.set_xlabel("Approval fiscal year (vintage)")
    ax.set_ylabel("Charge-off rate (count)")
    ax.set_title(title, fontweight="bold")
    ax.tick_params(axis="x", rotation=45)
    # Legend for the seasoning shading.
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#2b6cb0"),
        plt.Rectangle((0, 0), 1, 1, color="#a0aec0"),
    ]
    ax.legend(handles, ["Fully seasoned", "Not fully seasoned (under-reports)"], fontsize=9)
    plt.tight_layout()
    return fig


def plot_vintage_curves(
    curves: pd.DataFrame,
    title: str = "Cumulative charge-off rate by vintage cohort",
    figsize: tuple[float, float] = (11, 7),
    max_cohorts: int | None = None,
) -> plt.Figure:
    """Line chart: one cumulative charge-off curve per vintage vs months-on-book.

    *curves* is the output of ``vintage.compute_vintage_curves`` (rows =
    vintage, columns = ``MOB_xxx``).
    """
    if curves.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return fig

    mob_values = [int(c.replace("MOB_", "")) for c in curves.columns]
    rows = curves.tail(max_cohorts) if max_cohorts else curves
    cmap = plt.get_cmap("viridis")

    fig, ax = plt.subplots(figsize=figsize)
    for i, (vintage, row) in enumerate(rows.iterrows()):
        color = cmap(i / max(len(rows) - 1, 1))
        ax.plot(mob_values, row.values, marker="o", markersize=3,
                label=str(int(vintage)), color=color, linewidth=1.5)
    ax.yaxis.set_major_formatter(_PCT)
    ax.set_xlabel("Months since approval (months-on-book)")
    ax.set_ylabel("Cumulative charge-off rate")
    ax.set_title(title, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Vintage", fontsize=8, ncol=2, loc="upper left")
    plt.tight_layout()
    return fig


def plot_vintage_heatmap(
    curves: pd.DataFrame,
    title: str = "Cumulative charge-off rate — vintage x months-on-book",
    figsize: tuple[float, float] = (12, 7),
    cmap: str = "RdYlGn_r",
) -> plt.Figure:
    """Heatmap of the cumulative charge-off curves (rows = vintage, cols = MOB)."""
    if curves.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return fig

    values = curves.values.astype(float)
    flat = values[~np.isnan(values)]
    vmax = max(float(np.nanpercentile(values, 95)) * 1.2, 0.05) if flat.size else 0.1

    cmap_obj = plt.get_cmap(cmap).copy()
    cmap_obj.set_bad(color="#e0e0e0")

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(values, aspect="auto", cmap=cmap_obj, vmin=0.0, vmax=vmax)

    col_labels = [c.replace("MOB_", "") + "m" for c in curves.columns]
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=9)
    ax.set_yticks(range(len(curves.index)))
    ax.set_yticklabels([str(int(v)) for v in curves.index], fontsize=9)
    ax.set_xlabel("Months on book")
    ax.set_ylabel("Approval vintage")

    for r in range(values.shape[0]):
        for c in range(values.shape[1]):
            val = values[r, c]
            if np.isnan(val):
                continue
            rel = val / vmax if vmax > 0 else 0
            ax.text(c, r, f"{val * 100:.1f}", ha="center", va="center",
                    fontsize=7, color="white" if rel > 0.6 else "black")

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Cumulative charge-off rate")
    cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.set_title(title, fontweight="bold", pad=12)
    plt.tight_layout()
    return fig


def plot_loan_age_transition(
    table: pd.DataFrame,
    title: str = "When charge-offs occur, by loan age",
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """Bar of charge-off share by loan-age band with a cumulative line."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(table["loan_age_band"], table["pct_of_chargeoffs"], color="#dd6b20",
           label="Share of charge-offs in band")
    ax.set_ylabel("Share of all charge-offs")
    ax.yaxis.set_major_formatter(_PCT)
    ax.set_xlabel("Loan age at charge-off")
    ax.tick_params(axis="x", rotation=30)

    ax2 = ax.twinx()
    ax2.plot(table["loan_age_band"], table["cumulative_pct_of_chargeoffs"],
             color="#1a202c", marker="o", label="Cumulative")
    ax2.set_ylabel("Cumulative share")
    ax2.yaxis.set_major_formatter(_PCT)
    ax2.set_ylim(0, 1.05)

    ax.set_title(title, fontweight="bold")
    fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.92), fontsize=9)
    plt.tight_layout()
    return fig
