"""Leading-vs-lagging framing and the leading views the data supports (CML-4).

APG 220 para 66: a monitor should lean on **forward-looking** signals, not only
lagging realised metrics. SBA outcome-level data is lagging by nature (one final
status per loan), so most metrics here are lagging — this module is explicit
about that, and adds the two genuinely *leading* views the data still supports:

  1. Origination volume/mix trend by approval year — growth and the industry /
     size mix shift in what is being *written*. A deteriorating mix (e.g. a swing
     into a high-charge-off sector or larger tickets) leads the eventual book
     charge-off rate.
  2. Vintage-over-vintage early-MOB charge-off — is a young cohort charging off
     faster at, say, 24 months than its predecessors did at the same age? That
     lands well before the cohort's *final* charge-off rate is known.
"""
from __future__ import annotations

import pandas as pd

from . import vintage as vint
from .config import load_config
from .logger import get_logger

_log = get_logger(__name__)

_EXPOSURE = "grossapproval"

# Static leading/lagging classification of the monitor's metrics. Honest by
# design: the SBA book is mostly lagging; the leading column is short.
_METRIC_CLASSIFICATION = [
    ("Concentration (HHI, top-N share)", "Lagging/static", "Snapshot of the current book"),
    ("Charge-off rate by industry/size/vintage", "Lagging", "Realised write-offs"),
    ("Vintage cohort charge-off curves", "Lagging", "Cumulative realised losses by age"),
    ("Loan-age transition (when charge-offs occur)", "Lagging", "Realised default timing"),
    ("Stage proxy (performing vs defaulted)", "Lagging", "Terminal status only"),
    ("Problem-exposure layer (DELINQ/PSTDUE/LIQUID)", "Leading",
     "Pre-charge-off pipeline; IN LIQUIDATION ~ certain future charge-off"),
    ("Origination volume/mix trend by approval year", "Leading",
     "Mix shift in what is being written leads the future charge-off rate"),
    ("Vintage-over-vintage early-MOB charge-off", "Leading",
     "Young cohort deteriorating faster than predecessors at the same age"),
]


def metric_classification() -> pd.DataFrame:
    """Return the leading/lagging classification of each monitoring metric."""
    return pd.DataFrame(
        _METRIC_CLASSIFICATION, columns=["metric", "type", "rationale"]
    )


def origination_trend(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Origination volume + mix trend by approval fiscal year (a leading view).

    Per approval FY: loans originated, gross approval ($), year-on-year exposure
    growth, the largest originated sector and its share, and the share of
    origination in the larger size bands (a ticket-size mix signal).
    """
    cfg = config or load_config()
    bands = cfg["size_bands"]["labels"]
    # Treat the top two size bands as "large" tickets for the mix signal.
    large_bands = set(bands[-2:])

    work = df.copy()
    work["_is_large"] = work["size_band"].astype("string").isin(large_bands)

    rows = []
    for fy, cohort in work.groupby("vintage", observed=True):
        exposure = float(cohort[_EXPOSURE].sum())
        sector_exposure = cohort.groupby("naics_sector")[_EXPOSURE].sum()
        top_sector = sector_exposure.idxmax()
        top_share = float(sector_exposure.max() / exposure) if exposure else 0.0
        large_share = float(cohort.loc[cohort["_is_large"], _EXPOSURE].sum() / exposure) if exposure else 0.0
        rows.append({
            "vintage": int(fy),
            "loans_originated": int(len(cohort)),
            "exposure": exposure,
            "top_sector": top_sector,
            "top_sector_share": round(top_share, 4),
            "large_ticket_share": round(large_share, 4),
        })

    out = pd.DataFrame(rows).sort_values("vintage").reset_index(drop=True)
    out["exposure_yoy_growth"] = out["exposure"].pct_change().round(4)
    _log.info("Origination trend: %d approval-year cohorts", len(out))
    return out


def vintage_over_vintage_early_mob(
    df: pd.DataFrame, config: dict | None = None
) -> pd.DataFrame:
    """Early-MOB charge-off per vintage with the vintage-over-vintage delta.

    For each cohort observable at the early-MOB reference checkpoint (default 24
    months), report the cumulative charge-off rate at that age, the prior
    cohort's rate at the same age, and the ratio. A ratio > 1 means the cohort
    is deteriorating faster than its immediate predecessor did when equally
    young — a leading signal ahead of the final charge-off rate.
    """
    cfg = config or load_config()
    ref = int(cfg["vintage"].get("early_mob_reference", 24))
    curves = vint.compute_vintage_curves(df, config=cfg)
    col = f"MOB_{ref:03d}"
    if curves.empty or col not in curves.columns:
        return pd.DataFrame(
            columns=["vintage", "early_mob_chargeoff", "prior_vintage_rate",
                     "vintage_over_vintage_ratio", "reference_mob"]
        )

    series = curves[col].dropna()
    out = pd.DataFrame({
        "vintage": series.index.astype(int),
        "early_mob_chargeoff": series.values,
    }).sort_values("vintage").reset_index(drop=True)
    out["prior_vintage_rate"] = out["early_mob_chargeoff"].shift(1)
    out["vintage_over_vintage_ratio"] = (
        out["early_mob_chargeoff"] / out["prior_vintage_rate"]
    ).round(2)
    out["reference_mob"] = ref
    _log.info(
        "Vintage-over-vintage early-MOB (%dm): %d observable cohorts",
        ref, len(out),
    )
    return out
