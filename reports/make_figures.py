"""
reports/make_figures.py — regenerate the README charts for this repo.

Every figure is built from the committed result tables in outputs/tables/
(aggregated portfolio metrics only — exposures, rates, shares; never loan-level
records), so the charts regenerate reproducibly with:

    python reports/make_figures.py

Outputs PNGs into reports/figures/.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
FIG = ROOT / "reports" / "figures"
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

print("\nAll figures written to", FIG)
