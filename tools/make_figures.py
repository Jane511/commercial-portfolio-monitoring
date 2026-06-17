"""
tools/make_figures.py — regenerate the README charts for this repo.

Every figure is built from the committed result tables in outputs/tables/
(aggregated portfolio metrics only — exposures, rates, shares; never loan-level
records), so the charts regenerate reproducibly with:

    python tools/make_figures.py

Outputs PNGs into outputs/charts/.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
FIG = ROOT / "outputs" / "charts"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130,
    "font.size": 12.5, "axes.titlesize": 15, "axes.titleweight": "bold",
    "axes.labelsize": 12.5, "axes.grid": True, "grid.alpha": 0.25,
    "axes.spines.top": False, "axes.spines.right": False,
})
BLUE, RED, GREY = "#2166ac", "#b2182b", "#bdbdbd"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name)
    plt.close(fig)
    print("wrote", FIG / name)


# 1. Exposure concentration by industry (top 10) + HHI -----------------------
ind = pd.read_csv(TAB / "02_concentration_industry.csv").sort_values("exposure_share", ascending=True).tail(10)
hhi = pd.read_csv(TAB / "02_concentration_hhi_summary.csv").set_index("dimension")
hhi_ind = hhi.loc["industry", "hhi"]
top10 = hhi.loc["industry", "top10_exposure_share"]
fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.barh(ind.industry, ind.exposure_share * 100, color=BLUE, edgecolor="white")
for y, v in enumerate(ind.exposure_share * 100):
    ax.text(v, y, f" {v:.1f}%", va="center", fontsize=10)
ax.set_xlabel("share of total exposure (%)")
ax.set_title(f"Exposure concentration by industry (top 10)\nHHI {hhi_ind:.2f} — Moderate · top-10 = {top10*100:.0f}% of book",
             fontsize=13)
ax.grid(axis="y", alpha=0)
save(fig, "concentration_by_industry.png")

# 2. Charge-off rate by approval-year vintage (line) -------------------------
vin = pd.read_csv(TAB / "03_chargeoff_by_vintage.csv").sort_values("vintage")
fig, ax = plt.subplots(figsize=(8.4, 4.8))
seasoned = vin[vin.fully_seasoned]
green = vin[~vin.fully_seasoned]
ax.plot(seasoned.vintage, seasoned.chargeoff_rate_count * 100, "o-", color=RED,
        linewidth=2, label="fully seasoned")
ax.plot(green.vintage, green.chargeoff_rate_count * 100, "o--", color=GREY,
        linewidth=2, label="not yet fully seasoned")
ax.set_xlabel("approval-year vintage")
ax.set_ylabel("charge-off rate by count (%)")
ax.set_title("Charge-off rate by vintage — crisis cohorts spike ~5×")
ax.legend(frameon=False)
ax.set_xticks(vin.vintage[::2])
save(fig, "chargeoff_by_vintage.png")

# 3. Charge-off rate by industry (top 10, sorted) ----------------------------
ci = pd.read_csv(TAB / "03_chargeoff_by_industry.csv")
ci = ci.sort_values("chargeoff_rate_count", ascending=True).tail(10)
fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.barh(ci.industry, ci.chargeoff_rate_count * 100, color=RED, edgecolor="white")
for y, v in enumerate(ci.chargeoff_rate_count * 100):
    ax.text(v, y, f" {v:.1f}%", va="center", fontsize=10)
ax.set_xlabel("charge-off rate by count (%)")
ax.set_title("Charge-off rate by industry (top 10)")
ax.grid(axis="y", alpha=0)
save(fig, "chargeoff_by_industry.png")

PURPLE, GREEN = "#762a83", "#1b7837"


def _barh_labels(ax, values, fmt="{:.1f}%"):
    for y, v in enumerate(values):
        ax.text(v, y, " " + fmt.format(v), va="center", fontsize=9.5)


# 4. Average PD and LGD by sector (paired panel) -----------------------------
# Same sectors, same order, so PD and LGD are read side by side.
cp = pd.read_csv(TAB / "09_credit_risk_parameters_by_industry.csv")
top = cp.nlargest(12, "ead_total").sort_values("pd_count")
fig, (axp, axl) = plt.subplots(1, 2, figsize=(13.5, 6.2), sharey=True)
axp.barh(top.segment, top.pd_count * 100, color=RED, edgecolor="white")
_barh_labels(axp, top.pd_count * 100)
axp.set_xlabel("PD — default rate by count (%)")
axp.set_title("Average PD by sector")
axp.grid(axis="y", alpha=0)
axl.barh(top.segment, top.lgd * 100, color=BLUE, edgecolor="white")
_barh_labels(axl, top.lgd * 100)
axl.set_xlabel("LGD — loss given default (%)")
axl.set_title("Average LGD by sector")
axl.grid(axis="y", alpha=0)
fig.suptitle("Credit-risk parameters by sector — top 12 by exposure (same order)",
             fontsize=15, fontweight="bold")
save(fig, "pd_lgd_by_sector.png")

# 5. Expected-loss rate by sector --------------------------------------------
el = cp.nlargest(12, "ead_total").sort_values("el_rate")
fig, ax = plt.subplots(figsize=(10.0, 5.6))
ax.barh(el.segment, el.el_rate * 100, color=PURPLE, edgecolor="white")
_barh_labels(ax, el.el_rate * 100)
ax.set_xlabel("expected-loss rate, % of exposure  (= PD($) × LGD)")
ax.set_title("Expected-loss rate by sector")
ax.grid(axis="y", alpha=0)
save(fig, "el_by_sector.png")

# 6. Parameter stress — downturn vs through-the-cycle ------------------------
st = pd.read_csv(TAB / "09_credit_risk_parameters_stress.csv").set_index("metric_key")
vint = str(st["crisis_vintages"].iloc[0])
keys = ["pd_count", "lgd", "el_rate"]
labels = ["PD\n(default rate)", "LGD\n(loss given default)", "EL rate\n(expected loss)"]
ttc = [st.loc[k, "through_the_cycle"] * 100 for k in keys]
cri = [st.loc[k, "crisis_downturn"] * 100 for k in keys]
mult = [st.loc[k, "stress_multiplier"] for k in keys]
x = np.arange(len(keys))
w = 0.38
fig, ax = plt.subplots(figsize=(8.8, 5.4))
ax.bar(x - w / 2, ttc, w, label="through-the-cycle (FY2000–2019)", color=BLUE)
b2 = ax.bar(x + w / 2, cri, w, label=f"crisis / downturn ({vint})", color=RED)
for xi, c, m in zip(x, cri, mult):
    ax.text(xi + w / 2, c, f"{m:.1f}×", ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("rate (%)")
ax.set_title("Parameter stress test — downturn vs through-the-cycle")
ax.legend(frameon=False)
ax.grid(axis="x", alpha=0)
save(fig, "parameters_stress.png")

print("\nAll figures written to", FIG)
