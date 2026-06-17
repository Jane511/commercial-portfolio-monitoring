"""Empirical credit-risk parameters (PD / LGD / EAD / EL) from realised outcomes.

These are *realised, through-the-cycle* parameters read straight off the SBA
outcome data — **not** a fitted obligor-level rating model. They are the
calibration anchors / assumption inputs a deal-pricing or ECL/RWA model would
consume::

    PD  — probability of default  = observed default (charge-off) frequency
    LGD — loss given default       = realised loss severity on defaulted loans
                                     (charge-off $ / exposure of those loans)
    EAD — exposure at default      = gross approval (SBA has no running balance,
                                     so origination exposure is the EAD proxy)
    EL  — expected loss            = PD x LGD x EAD  (== realised charge-off $)

The definitions reuse the same primitives as ``chargeoff`` / ``report`` so the
numbers reconcile exactly with the charge-off and stage-proxy tables:

    PD (count, obligor-weighted)   defaults / loans
    PD ($, exposure-weighted)      defaulted EAD / total EAD
    LGD                            charge-off $ on defaults / defaulted EAD
    EL rate                        charge-off $ on defaults / total EAD
                                     ( == PD($) x LGD == dollar charge-off rate )

NOTE (scope): this is parameter *extraction* from observed defaults, not a
model. There is no scorecard, no obligor-level PD prediction and therefore no
model-performance / backtesting layer here — that lives in the sister modelling
repos. What this gives a pricing or provisioning model is the historical
loss-experience anchor it must be calibrated against.
"""
from __future__ import annotations

import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)

_EXPOSURE = "grossapproval"
_GUARANTEE = "sbaguaranteedapproval"
_LOSS = "grosschargeoffamount"

# Column order for the wide per-segment parameter tables.
_PARAM_COLUMNS = [
    "loan_count", "defaults",
    "ead_total", "ead_avg", "ead_avg_defaulted",
    "pd_count", "pd_dollar",
    "lgd", "el_amount", "el_rate", "el_per_loan",
]


def _parameter_frame(df: pd.DataFrame, group_col: str | None, label: str) -> pd.DataFrame:
    """PD / LGD / EAD / EL for each group (whole book when *group_col* is None)."""
    d = df.copy()
    d["_def_ead"] = d[_EXPOSURE].where(d["is_default"], 0.0)
    d["_def_loss"] = d[_LOSS].where(d["is_default"], 0.0)

    if group_col is None:
        d["_seg"] = label
        gcol = "_seg"
    else:
        gcol = group_col

    g = d.groupby(gcol, dropna=False, observed=True).agg(
        loan_count=(_EXPOSURE, "size"),
        defaults=("is_default", "sum"),
        ead_total=(_EXPOSURE, "sum"),
        ead_defaulted=("_def_ead", "sum"),
        el_amount=("_def_loss", "sum"),
    )

    # Parameters. Guard the defaulted-only ratios against zero-default segments.
    g["pd_count"] = (g["defaults"] / g["loan_count"]).round(4)
    g["pd_dollar"] = (g["ead_defaulted"] / g["ead_total"]).round(4)
    g["lgd"] = (g["el_amount"] / g["ead_defaulted"].where(g["ead_defaulted"] > 0)).round(4)
    g["ead_avg"] = (g["ead_total"] / g["loan_count"]).round(0)
    g["ead_avg_defaulted"] = (g["ead_defaulted"] / g["defaults"].where(g["defaults"] > 0)).round(0)
    g["el_rate"] = (g["el_amount"] / g["ead_total"]).round(4)
    g["el_per_loan"] = (g["el_amount"] / g["loan_count"]).round(0)

    out = g.reset_index().rename(columns={gcol: "segment"})
    return out[["segment", *_PARAM_COLUMNS]]


def credit_risk_parameters(df: pd.DataFrame) -> pd.DataFrame:
    """Portfolio-level empirical PD / LGD / EAD / EL (one row).

    Adds the SBA guaranteed share, which determines how much of the (gross,
    whole-loan) LGD is borne by the lender vs transferred to the SBA guarantee.
    """
    out = _parameter_frame(df, None, "Total portfolio")
    total_ead = float(df[_EXPOSURE].sum())
    guaranteed = float(df[_GUARANTEE].sum())
    out["guaranteed_exposure"] = round(guaranteed, 0)
    out["guarantee_ratio"] = round(guaranteed / total_ead, 4) if total_ead else float("nan")
    # Indicative lender-retained LGD: the share of each loss NOT covered by the
    # guarantee. Approximate — the guarantee applies to the guaranteed portion.
    out["lgd_net_of_guarantee"] = (out["lgd"] * (1 - out["guarantee_ratio"])).round(4)
    _log.info(
        "Credit-risk parameters: PD(count)=%.2f%%  PD($)=%.2f%%  LGD=%.1f%%  "
        "EAD(avg)=$%s  EL rate=%.2f%%",
        out["pd_count"].iloc[0] * 100, out["pd_dollar"].iloc[0] * 100,
        out["lgd"].iloc[0] * 100, f"{out['ead_avg'].iloc[0]:,.0f}",
        out["el_rate"].iloc[0] * 100,
    )
    return out


def credit_risk_parameters_by_size_band(df: pd.DataFrame) -> pd.DataFrame:
    """PD / LGD / EAD / EL by loan-size band, in natural (small -> large) order."""
    out = _parameter_frame(df, "size_band", "size_band")
    if isinstance(df["size_band"].dtype, pd.CategoricalDtype):
        order = list(df["size_band"].cat.categories)
        out["segment"] = pd.Categorical(out["segment"], categories=order, ordered=True)
        out = out.sort_values("segment").reset_index(drop=True)
    return out


def credit_risk_parameters_by_industry(df: pd.DataFrame) -> pd.DataFrame:
    """PD / LGD / EAD / EL by NAICS sector, largest exposure first."""
    out = _parameter_frame(df, "naics_sector", "naics_sector")
    return out.sort_values("ead_total", ascending=False).reset_index(drop=True)


def credit_risk_parameters_by_product(df: pd.DataFrame) -> pd.DataFrame:
    """PD / LGD / EAD / EL by SBA 7(a) product family, largest exposure first.

    "Product" here is the SBA 7(a) ``subprogram`` grouped into families
    (Standard 7(a), SBA Express, CAPLines, Export, …). This is small-business
    lending throughout — the dataset carries no residential / commercial-property
    mortgage product.
    """
    out = _parameter_frame(df, "product_type", "product_type")
    return out.sort_values("ead_total", ascending=False).reset_index(drop=True)


def credit_risk_parameters_by_structure(df: pd.DataFrame) -> pd.DataFrame:
    """PD / LGD / EAD / EL by loan structure and by collateral, stacked.

    Two pricing-relevant binary cuts in one table: term loan vs revolving line
    of credit, and secured vs unsecured. A leading ``cut`` column names which
    dimension each row belongs to.
    """
    parts = []
    for col, cut in (("loan_structure", "Loan structure"),
                     ("collateral_status", "Collateral")):
        frame = _parameter_frame(df, col, col)
        frame.insert(0, "cut", cut)
        parts.append(frame.sort_values("ead_total", ascending=False))
    return pd.concat(parts, ignore_index=True)
