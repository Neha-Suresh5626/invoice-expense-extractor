"""
utils/analytics.py
Calculates summary stats and generates charts (matplotlib).
Charts saved to static/charts/ so Flask can serve them.
"""

import os
import matplotlib
matplotlib.use("Agg")          # non-interactive backend (no display needed)
import matplotlib.pyplot as plt

from utils.db import get_totals, get_category_totals, get_all_invoices

CHARTS_DIR = os.path.join("static", "charts")


def get_summary() -> dict:
    """Return aggregate stats for the dashboard template."""
    totals = get_totals()
    categories = get_category_totals()
    invoices = get_all_invoices()
    handwritten = sum(1 for i in invoices if i["is_handwritten"])

    return {
        "total_invoices": totals.get("total_invoices", 0),
        "total_spend":    round(totals.get("total_spend", 0), 2),
        "total_gst":      round(totals.get("total_gst", 0), 2),
        "avg_invoice":    round(totals.get("avg_invoice", 0), 2),
        "handwritten":    handwritten,
        "categories":     categories,
        "recent":         invoices[:5],
    }


def generate_charts():
    """Generate expense_chart.png and gst_chart.png into static/charts/."""
    os.makedirs(CHARTS_DIR, exist_ok=True)
    categories = get_category_totals()

    if not categories:
        _placeholder_chart("No data yet", os.path.join(CHARTS_DIR, "expense_chart.png"))
        _placeholder_chart("No data yet", os.path.join(CHARTS_DIR, "gst_chart.png"))
        return

    labels = [c["category"] for c in categories]
    values = [c["total"] for c in categories]

    # ── Bar chart: Expense by Category ──────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color="#2563EB", edgecolor="white", linewidth=0.8)
    ax.set_title("Expense by Category", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Amount (₹)")
    ax.set_xlabel("Category")
    ax.tick_params(axis="x", rotation=25, labelsize=8)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"₹{val:,.0f}", ha="center", va="bottom", fontsize=7)
    plt.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "expense_chart.png"), dpi=130)
    plt.close(fig)

    # ── Pie chart: GST vs Non-GST spend ─────────────────────────────
    totals   = get_totals()
    gst      = totals.get("total_gst", 0)
    spend    = totals.get("total_spend", 0)
    non_gst  = max(spend - gst, 0)

    fig2, ax2 = plt.subplots(figsize=(5, 4))
    wedge_sizes  = [gst, non_gst] if gst > 0 else [1]
    wedge_labels = ["GST", "Net Amount"] if gst > 0 else ["No GST data"]
    wedge_colors = ["#F59E0B", "#10B981"] if gst > 0 else ["#E2E8F0"]

    ax2.pie(wedge_sizes, labels=wedge_labels, colors=wedge_colors,
            autopct="%1.1f%%" if gst > 0 else None,
            startangle=140, pctdistance=0.8,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax2.set_title("GST vs Net Amount", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    fig2.savefig(os.path.join(CHARTS_DIR, "gst_chart.png"), dpi=130)
    plt.close(fig2)


def _placeholder_chart(message: str, path: str):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.text(0.5, 0.5, message, ha="center", va="center",
            fontsize=14, color="#94A3B8", transform=ax.transAxes)
    ax.axis("off")
    fig.savefig(path, dpi=100)
    plt.close(fig)