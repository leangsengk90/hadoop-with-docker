#!/usr/bin/env python3
"""Regenerate all 10 analytics notebooks with clean, beautiful charts."""

import json, uuid, os

BASE = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# Helpers to build ipynb structure
# ─────────────────────────────────────────────────────────────────────────────

def _uid():
    return uuid.uuid4().hex[:8]

def md_cell(src):
    return {"cell_type": "markdown", "id": _uid(), "metadata": {},
            "source": src}

def code_cell(src):
    return {"cell_type": "code", "execution_count": None, "id": _uid(),
            "metadata": {}, "outputs": [], "source": src}

def notebook(cells):
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                          "name": "python3"},
            "language_info": {"name": "python", "version": "3.8.0"}
        },
        "cells": cells
    }

def save(name, cells):
    path = os.path.join(BASE, name)
    with open(path, "w") as f:
        json.dump(notebook(cells), f, indent=1)
    print(f"  ✓ {name}")

# ─────────────────────────────────────────────────────────────────────────────
# SHARED SETUP CELL (reused in every notebook)
# ─────────────────────────────────────────────────────────────────────────────

SETUP = """\
from pyhive import hive
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns

# ── Global style ──────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams.update({
    "figure.dpi": 120,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
})
PALETTE = sns.color_palette("muted")

def get_conn():
    return hive.connect(host="hive-server2", port=10000,
                        database="default", auth="NONE")

def fetch_df(cur, sql):
    cur.execute(sql)
    cols = [d[0].split(".")[-1] for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)

def fmt_usd(v):
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.0f}"

conn = get_conn()
cur  = conn.cursor()
print("Connected.")
"""

CLOSE = """\
cur.close()
conn.close()
print("Done.")
"""

# ═════════════════════════════════════════════════════════════════════════════
# 01 — Sales Overview
# ═════════════════════════════════════════════════════════════════════════════

NB01_KPI = """\
# ── KPI Summary ───────────────────────────────────────────────────────────────
kpi = fetch_df(cur, \"\"\"
    SELECT
        COUNT(DISTINCT o.order_id)                   AS total_orders,
        COUNT(DISTINCT o.customer_id)                AS total_customers,
        ROUND(SUM(oi.sales), 2)                      AS total_revenue,
        ROUND(AVG(oi.sales), 2)                      AS avg_item_sales,
        ROUND(SUM(oi.profit), 2)                     AS total_profit,
        ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2)  AS profit_margin_pct
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
\"\"\")

row = kpi.iloc[0]
kpis = [
    ("Total Orders",     f"{int(row.total_orders):,}",    "#4C72B0"),
    ("Unique Customers", f"{int(row.total_customers):,}", "#DD8452"),
    ("Total Revenue",    fmt_usd(row.total_revenue),      "#55A868"),
    ("Total Profit",     fmt_usd(row.total_profit),       "#C44E52"),
    ("Avg Line Sales",   fmt_usd(row.avg_item_sales),     "#937860"),
    ("Profit Margin",    f"{row.profit_margin_pct:.1f}%", "#8172B2"),
]

fig, axes = plt.subplots(1, 6, figsize=(18, 2.5))
fig.suptitle("Business KPI Dashboard", fontsize=14, fontweight="bold", y=1.02)
for ax, (label, value, color) in zip(axes, kpis):
    ax.set_facecolor(color)
    ax.axis("off")
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=18,
            fontweight="bold", color="white", transform=ax.transAxes)
    ax.text(0.5, 0.20, label, ha="center", va="center", fontsize=9,
            color="white", transform=ax.transAxes, alpha=0.9)
plt.tight_layout()
plt.show()
"""

NB01_MONTHLY = """\
# ── Monthly Sales Trend ───────────────────────────────────────────────────────
monthly = fetch_df(cur, \"\"\"
    SELECT SUBSTR(o.order_date,1,7) AS month,
           ROUND(SUM(oi.sales),2)   AS revenue,
           ROUND(SUM(oi.profit),2)  AS profit
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY SUBSTR(o.order_date,1,7)
    ORDER BY month
\"\"\")

tick_positions = list(range(0, len(monthly), 3))
tick_labels    = [monthly["month"].iloc[i] for i in tick_positions]

fig, ax = plt.subplots(figsize=(15, 4.5))
ax.fill_between(range(len(monthly)), monthly["revenue"],
                alpha=0.12, color=PALETTE[0])
ax.plot(range(len(monthly)), monthly["revenue"], marker="o", markersize=4,
        color=PALETTE[0], linewidth=2, label="Revenue")
ax.fill_between(range(len(monthly)), monthly["profit"],
                alpha=0.12, color=PALETTE[1])
ax.plot(range(len(monthly)), monthly["profit"], marker="s", markersize=4,
        color=PALETTE[1], linewidth=2, label="Profit")
ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, rotation=40, ha="right", fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_usd(x)))
ax.set_title("Monthly Revenue vs Profit Trend")
ax.set_xlabel("Month")
ax.set_ylabel("USD")
ax.legend(frameon=False)
ax.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
"""

NB01_ANNUAL = """\
# ── Annual Sales by Year ──────────────────────────────────────────────────────
yearly = fetch_df(cur, \"\"\"
    SELECT SUBSTR(o.order_date,1,4) AS year,
           ROUND(SUM(oi.sales),2)     AS revenue,
           ROUND(SUM(oi.profit),2)    AS profit,
           COUNT(DISTINCT o.order_id) AS orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY SUBSTR(o.order_date,1,4)
    ORDER BY year
\"\"\")

bar_width = 0.35
x         = range(len(yearly))

fig, ax1 = plt.subplots(figsize=(9, 5))
ax2 = ax1.twinx()

bars1 = ax1.bar([i - bar_width/2 for i in x], yearly["revenue"],
                bar_width, color=PALETTE[0], label="Revenue", zorder=3)
bars2 = ax1.bar([i + bar_width/2 for i in x], yearly["profit"],
                bar_width, color=PALETTE[1], label="Profit",  zorder=3)
ax2.plot(x, yearly["orders"], color=PALETTE[2], marker="D",
         linewidth=2, markersize=7, label="# Orders", zorder=4)

for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 2000,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=8, color=PALETTE[0])

for bar in bars2:
    ax1.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 500,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=8, color=PALETTE[1])

for xi, yi in zip(x, yearly["orders"]):
    ax2.text(xi, yi + 10, str(int(yi)),
             ha="center", va="bottom", fontsize=9,
             color=PALETTE[2], fontweight="bold")

handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2,
           loc="upper left", frameon=False, fontsize=9)

ax1.set_xticks(list(x))
ax1.set_xticklabels(yearly["year"], fontsize=11)
ax1.set_title("Annual Revenue, Profit & Order Volume")
ax1.set_ylabel("USD")
ax2.set_ylabel("# Orders")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax1.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

save("01_Sales_Overview.ipynb", [
    md_cell("# 01 — Sales Overview\n"
            "Key sales KPIs across the entire dataset: total revenue, orders, "
            "average order value, and monthly trends.\n"),
    code_cell(SETUP),
    code_cell(NB01_KPI),
    code_cell(NB01_MONTHLY),
    code_cell(NB01_ANNUAL),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 02 — Profit Analysis
# ═════════════════════════════════════════════════════════════════════════════

NB02_CAT = """\
# ── Profit Margin by Category ─────────────────────────────────────────────────
cat_profit = fetch_df(cur, \"\"\"
    SELECT p.category,
           ROUND(SUM(oi.sales),2)   AS revenue,
           ROUND(SUM(oi.profit),2)  AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category ORDER BY profit DESC
\"\"\")

colors = [PALETTE[1] if x >= 0 else PALETTE[3] for x in cat_profit["profit"]]
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
fig.suptitle("Category Profitability Overview", fontsize=15,
             fontweight="bold", y=1.02)

# Left: Revenue bars
axes[0].barh(cat_profit["category"][::-1], cat_profit["revenue"][::-1],
             color=PALETTE[0], edgecolor="white")
for i, val in enumerate(cat_profit["revenue"][::-1]):
    axes[0].text(val + 500, i, fmt_usd(val), va="center", fontsize=9)
axes[0].set_title("Revenue by Category")
axes[0].set_xlabel("Revenue (USD)")
axes[0].xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
axes[0].grid(axis="x", linestyle="--", alpha=0.4)

# Right: Profit bars with margin labels
axes[1].barh(cat_profit["category"][::-1], cat_profit["profit"][::-1],
             color=colors[::-1], edgecolor="white")
axes[1].axvline(0, color="grey", linewidth=0.8)
for i, (profit, margin) in enumerate(zip(cat_profit["profit"][::-1],
                                         cat_profit["margin_pct"][::-1])):
    offset = 200 if profit >= 0 else -200
    align  = "left" if profit >= 0 else "right"
    axes[1].text(profit + offset, i,
                 f"{fmt_usd(profit)} ({margin}%)",
                 va="center", fontsize=9, ha=align)
axes[1].set_title("Profit & Margin % by Category")
axes[1].set_xlabel("Profit (USD)")
axes[1].xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
axes[1].grid(axis="x", linestyle="--", alpha=0.4)

plt.tight_layout()
plt.show()
"""

NB02_SUB = """\
# ── Profit by Sub-Category ────────────────────────────────────────────────────
sub = fetch_df(cur, \"\"\"
    SELECT p.sub_category,
           ROUND(SUM(oi.profit),2) AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.sub_category ORDER BY profit ASC
\"\"\")

colors = [PALETTE[1] if x >= 0 else PALETTE[3] for x in sub["profit"]]
fig, ax = plt.subplots(figsize=(11, 7))
bars = ax.barh(sub["sub_category"], sub["profit"],
               color=colors, edgecolor="white", linewidth=0.5)
ax.axvline(0, color="grey", linewidth=1, linestyle="--")

for bar, margin in zip(bars, sub["margin_pct"]):
    w      = bar.get_width()
    offset = 80 if w >= 0 else -80
    align  = "left" if w >= 0 else "right"
    ax.text(w + offset, bar.get_y() + bar.get_height()/2,
            f"{fmt_usd(w)}  ({margin}%)",
            va="center", ha=align, fontsize=8)

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Profit (USD)")
ax.set_title("Profit & Margin % by Sub-Category", pad=12)
plt.tight_layout()
plt.show()
"""

NB02_LOSS = """\
# ── Top 20 Loss-Making Line Items ─────────────────────────────────────────────
losses = fetch_df(cur, \"\"\"
    SELECT oi.order_id, p.category, p.sub_category,
           ROUND(oi.sales,2)        AS sales,
           ROUND(oi.profit,2)       AS profit,
           ROUND(oi.discount*100,1) AS discount_pct
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    WHERE oi.profit < 0
    ORDER BY oi.profit ASC
    LIMIT 20
\"\"\")

# Bar chart: loss concentration per sub-category
loss_by_sub = losses.groupby("sub_category")["profit"].sum().sort_values()
fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.barh(loss_by_sub.index, loss_by_sub.values,
               color=PALETTE[3], edgecolor="white")
for bar in bars:
    ax.text(bar.get_width() - 30,
            bar.get_y() + bar.get_height()/2,
            fmt_usd(bar.get_width()),
            va="center", ha="right", fontsize=9,
            color="white", fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Total Loss (USD)")
ax.set_title("Loss Concentration by Sub-Category (sampled top 20)")
plt.tight_layout()
plt.show()
"""

save("02_Profit_Analysis.ipynb", [
    md_cell("# 02 — Profit Analysis\n"
            "Profitability deep-dive: margin by category, sub-category, "
            "region, and loss-making orders.\n"),
    code_cell(SETUP),
    code_cell(NB02_CAT),
    code_cell(NB02_SUB),
    code_cell(NB02_LOSS),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 03 — Customer Segmentation
# ═════════════════════════════════════════════════════════════════════════════

NB03_SEG = """\
# ── Revenue & Profit by Segment ───────────────────────────────────────────────
seg = fetch_df(cur, \"\"\"
    SELECT c.segment,
           COUNT(DISTINCT o.order_id)                AS orders,
           COUNT(DISTINCT o.customer_id)             AS customers,
           ROUND(SUM(oi.sales),2)                    AS revenue,
           ROUND(SUM(oi.profit),2)                   AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.segment ORDER BY revenue DESC
\"\"\")

seg_colors = [PALETTE[0], PALETTE[1], PALETTE[2]]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("Customer Segment Breakdown", fontsize=15,
             fontweight="bold", y=1.02)

for ax, col, title in zip(axes,
                           ["revenue", "profit", "orders"],
                           ["Revenue Share", "Profit Share", "Order Share"]):
    wedges, texts, autotexts = ax.pie(
        seg[col], labels=seg["segment"],
        autopct="%1.1f%%", colors=seg_colors,
        startangle=90, pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight("bold")
    ax.set_title(title)

plt.tight_layout()
plt.show()
"""

NB03_BAR = """\
# ── Revenue & Profit Bars by Segment ─────────────────────────────────────────
bar_w = 0.35
x     = range(len(seg))
fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar([i - bar_w/2 for i in x], seg["revenue"],
            bar_w, color=PALETTE[0], label="Revenue", zorder=3)
b2 = ax.bar([i + bar_w/2 for i in x], seg["profit"],
            bar_w, color=PALETTE[1], label="Profit", zorder=3)

for bar in b1:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 1000,
            fmt_usd(bar.get_height()),
            ha="center", va="bottom", fontsize=9, color=PALETTE[0])
for bar in b2:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 200,
            fmt_usd(bar.get_height()),
            ha="center", va="bottom", fontsize=9, color=PALETTE[1])

ax.set_xticks(list(x))
ax.set_xticklabels(seg["segment"], fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.legend(frameon=False)
ax.set_title("Revenue & Profit by Customer Segment")
ax.set_ylabel("USD")
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

NB03_AOV = """\
# ── Average Order Value per Segment ─────────────────────────────────────────-
aov = fetch_df(cur, \"\"\"
    SELECT c.segment,
           ROUND(SUM(oi.sales)/COUNT(DISTINCT o.order_id),2) AS avg_order_value,
           ROUND(SUM(oi.quantity)/COUNT(DISTINCT o.order_id),2) AS avg_items_per_order
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.segment
\"\"\")

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(aov["segment"], aov["avg_order_value"],
              color=[PALETTE[0], PALETTE[1], PALETTE[2]],
              edgecolor="white", zorder=3)
for bar in bars:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 5,
            fmt_usd(bar.get_height()),
            ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.set_title("Average Order Value by Customer Segment")
ax.set_ylabel("USD")
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

save("03_Customer_Segmentation.ipynb", [
    md_cell("# 03 — Customer Segmentation\n"
            "Revenue, profit and order frequency broken down by customer segment "
            "(Consumer, Corporate, Home Office).\n"),
    code_cell(SETUP),
    code_cell(NB03_SEG),
    code_cell(NB03_BAR),
    code_cell(NB03_AOV),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 04 — Product Performance
# ═════════════════════════════════════════════════════════════════════════════

NB04_REV = """\
# ── Top 10 Products by Revenue ───────────────────────────────────────────────
top_rev = fetch_df(cur, \"\"\"
    SELECT p.product_name, p.category,
           ROUND(SUM(oi.sales),2)  AS revenue,
           ROUND(SUM(oi.profit),2) AS profit,
           SUM(oi.quantity)        AS units_sold
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.product_name, p.category
    ORDER BY revenue DESC LIMIT 10
\"\"\")

cat_palette = {"Furniture": PALETTE[0], "Office Supplies": PALETTE[1],
               "Technology": PALETTE[2]}
colors = [cat_palette.get(c, PALETTE[3]) for c in top_rev["category"][::-1]]

fig, ax = plt.subplots(figsize=(11, 5))
bars = ax.barh(top_rev["product_name"].str[:42][::-1],
               top_rev["revenue"][::-1],
               color=colors, edgecolor="white")
for bar in bars:
    ax.text(bar.get_width() + 200,
            bar.get_y() + bar.get_height()/2,
            fmt_usd(bar.get_width()),
            va="center", fontsize=8)

handles = [mpatches.Patch(color=v, label=k) for k, v in cat_palette.items()]
ax.legend(handles=handles, frameon=False, fontsize=9)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Revenue (USD)")
ax.set_title("Top 10 Products by Revenue")
plt.tight_layout()
plt.show()
"""

NB04_PROF = """\
# ── Top 10 Products by Profit ────────────────────────────────────────────────
top_prof = fetch_df(cur, \"\"\"
    SELECT p.product_name, p.sub_category,
           ROUND(SUM(oi.profit),2) AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.product_name, p.sub_category
    ORDER BY profit DESC LIMIT 10
\"\"\")

fig, ax = plt.subplots(figsize=(11, 5))
bars = ax.barh(top_prof["product_name"].str[:42][::-1],
               top_prof["profit"][::-1],
               color=PALETTE[1], edgecolor="white")
for bar, margin in zip(bars, top_prof["margin_pct"][::-1]):
    ax.text(bar.get_width() + 30,
            bar.get_y() + bar.get_height()/2,
            f"{fmt_usd(bar.get_width())} ({margin}%)",
            va="center", fontsize=8)

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Profit (USD)")
ax.set_title("Top 10 Products by Profit")
plt.tight_layout()
plt.show()
"""

NB04_LOSS = """\
# ── Bottom 10 Products (Loss-Makers) ─────────────────────────────────────────
bot_prof = fetch_df(cur, \"\"\"
    SELECT p.product_name, p.sub_category,
           ROUND(SUM(oi.profit),2) AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.product_name, p.sub_category
    ORDER BY profit ASC LIMIT 10
\"\"\")

fig, ax = plt.subplots(figsize=(11, 5))
bars = ax.barh(bot_prof["product_name"].str[:42],
               bot_prof["profit"],
               color=PALETTE[3], edgecolor="white")
ax.axvline(0, color="grey", linewidth=0.8, linestyle="--")
for bar, margin in zip(bars, bot_prof["margin_pct"]):
    ax.text(bar.get_width() - 30,
            bar.get_y() + bar.get_height()/2,
            f"{fmt_usd(bar.get_width())} ({margin}%)",
            va="center", ha="right", fontsize=8,
            color="white", fontweight="bold")

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Profit (USD)")
ax.set_title("Bottom 10 Loss-Making Products")
plt.tight_layout()
plt.show()
"""

save("04_Product_Performance.ipynb", [
    md_cell("# 04 — Product Performance\n"
            "Top/bottom products by revenue and profit; "
            "quantity sold; category mix.\n"),
    code_cell(SETUP),
    code_cell(NB04_REV),
    code_cell(NB04_PROF),
    code_cell(NB04_LOSS),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 05 — Regional Sales
# ═════════════════════════════════════════════════════════════════════════════

NB05_REGION = """\
# ── Sales by Region ───────────────────────────────────────────────────────────
region = fetch_df(cur, \"\"\"
    SELECT l.region,
           ROUND(SUM(oi.sales),2)  AS revenue,
           ROUND(SUM(oi.profit),2) AS profit,
           COUNT(DISTINCT o.order_id) AS orders,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN locations l ON o.postal_code = l.postal_code
    GROUP BY l.region ORDER BY revenue DESC
\"\"\")

bar_w = 0.35
x     = range(len(region))
fig, ax1 = plt.subplots(figsize=(9, 5))
ax2 = ax1.twinx()

b1 = ax1.bar([i - bar_w/2 for i in x], region["revenue"],
             bar_w, color=PALETTE[0], label="Revenue", zorder=3)
b2 = ax1.bar([i + bar_w/2 for i in x], region["profit"],
             bar_w, color=PALETTE[1], label="Profit", zorder=3)
ax2.plot(x, region["margin_pct"], color=PALETTE[2], marker="o",
         linewidth=2, markersize=7, label="Margin %", zorder=4)

for bar in b1:
    ax1.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 1000,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=8, color=PALETTE[0])
for bar in b2:
    ax1.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 200,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=8, color=PALETTE[1])
for xi, mi in zip(x, region["margin_pct"]):
    ax2.text(xi, mi + 0.5, f"{mi:.1f}%",
             ha="center", va="bottom", fontsize=8,
             color=PALETTE[2], fontweight="bold")

handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2,
           loc="upper right", frameon=False, fontsize=9)
ax1.set_xticks(list(x))
ax1.set_xticklabels(region["region"], fontsize=11)
ax1.set_title("Revenue, Profit & Margin % by Region")
ax1.set_ylabel("USD")
ax2.set_ylabel("Margin %")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax1.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

NB05_STATES = """\
# ── Top 10 States by Revenue ─────────────────────────────────────────────────
states = fetch_df(cur, \"\"\"
    SELECT l.state,
           ROUND(SUM(oi.sales),2)  AS revenue,
           ROUND(SUM(oi.profit),2) AS profit
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN locations l ON o.postal_code = l.postal_code
    GROUP BY l.state ORDER BY revenue DESC LIMIT 10
\"\"\")

fig, ax = plt.subplots(figsize=(10, 5))
y = range(len(states))
ax.barh([i + 0.2 for i in y], states["revenue"][::-1],
        0.4, color=PALETTE[0], label="Revenue")
ax.barh([i - 0.2 for i in y], states["profit"][::-1],
        0.4, color=PALETTE[1], label="Profit", alpha=0.85)
ax.set_yticks(list(y))
ax.set_yticklabels(states["state"][::-1])

for i, (rev, prof) in enumerate(zip(states["revenue"][::-1],
                                    states["profit"][::-1])):
    ax.text(rev + 200, i + 0.2, fmt_usd(rev), va="center", fontsize=8)
    ax.text(prof + 200, i - 0.2, fmt_usd(prof), va="center",
            fontsize=8, color=PALETTE[1])

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.legend(frameon=False)
ax.set_xlabel("USD")
ax.set_title("Top 10 States: Revenue vs Profit")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

save("05_Regional_Sales.ipynb", [
    md_cell("# 05 — Regional Sales Analysis\n"
            "Sales, profit, and order volume broken down by region and state.\n"),
    code_cell(SETUP),
    code_cell(NB05_REGION),
    code_cell(NB05_STATES),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 06 — Shipping Analysis
# ═════════════════════════════════════════════════════════════════════════════

NB06_SHIP = """\
# ── Revenue & Profit by Ship Mode ─────────────────────────────────────────────
ship = fetch_df(cur, \"\"\"
    SELECT o.ship_mode,
           COUNT(DISTINCT o.order_id)  AS orders,
           ROUND(SUM(oi.sales),2)      AS revenue,
           ROUND(SUM(oi.profit),2)     AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.ship_mode ORDER BY revenue DESC
\"\"\")

bar_w = 0.35
x     = range(len(ship))
fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar([i - bar_w/2 for i in x], ship["revenue"],
            bar_w, color=PALETTE[0], label="Revenue", zorder=3)
b2 = ax.bar([i + bar_w/2 for i in x], ship["profit"],
            bar_w, color=PALETTE[1], label="Profit", zorder=3)

for bar in b1:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 500,
            fmt_usd(bar.get_height()),
            ha="center", va="bottom", fontsize=8, color=PALETTE[0])
for bar in b2:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 100,
            fmt_usd(bar.get_height()),
            ha="center", va="bottom", fontsize=8, color=PALETTE[1])

ax.set_xticks(list(x))
ax.set_xticklabels(ship["ship_mode"], fontsize=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.legend(frameon=False)
ax.set_title("Revenue & Profit by Ship Mode")
ax.set_ylabel("USD")
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

NB06_DAYS = """\
# ── Avg Shipping Days per Mode ────────────────────────────────────────────────
days = fetch_df(cur, \"\"\"
    SELECT ship_mode,
           ROUND(AVG(datediff(
               to_date(from_unixtime(unix_timestamp(ship_date,'M/d/yyyy'))),
               to_date(from_unixtime(unix_timestamp(order_date,'M/d/yyyy')))
           )),1) AS avg_ship_days,
           COUNT(DISTINCT order_id) AS orders
    FROM orders
    GROUP BY ship_mode ORDER BY avg_ship_days
\"\"\")

fig, ax = plt.subplots(figsize=(8, 4))
colors = [PALETTE[1] if d <= 3 else PALETTE[0] if d <= 5 else PALETTE[3]
          for d in days["avg_ship_days"][::-1]]
bars = ax.barh(days["ship_mode"][::-1], days["avg_ship_days"][::-1],
               color=colors, edgecolor="white")
for bar in bars:
    ax.text(bar.get_width() + 0.05,
            bar.get_y() + bar.get_height()/2,
            f"{bar.get_width():.1f} days",
            va="center", fontsize=10, fontweight="bold")

ax.set_xlabel("Average Days")
ax.set_title("Average Shipping Days by Ship Mode")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

save("06_Shipping_Analysis.ipynb", [
    md_cell("# 06 — Shipping Analysis\n"
            "Ship mode usage, average shipping days, "
            "and revenue/profit per shipping mode.\n"),
    code_cell(SETUP),
    code_cell(NB06_SHIP),
    code_cell(NB06_DAYS),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 07 — Discount Impact
# ═════════════════════════════════════════════════════════════════════════════

NB07_BUCKET = """\
# ── Profit by Discount Bucket ─────────────────────────────────────────────────
buckets = fetch_df(cur, \"\"\"
    SELECT
        CASE
            WHEN discount = 0    THEN '0% (No Discount)'
            WHEN discount <= 0.1 THEN '1-10%'
            WHEN discount <= 0.2 THEN '11-20%'
            WHEN discount <= 0.3 THEN '21-30%'
            WHEN discount <= 0.5 THEN '31-50%'
            ELSE '>50%'
        END AS discount_bucket,
        COUNT(*)                       AS line_items,
        ROUND(SUM(sales),2)            AS revenue,
        ROUND(SUM(profit),2)           AS profit,
        ROUND(AVG(profit/sales)*100,2) AS avg_margin_pct
    FROM order_items
    GROUP BY
        CASE
            WHEN discount = 0    THEN '0% (No Discount)'
            WHEN discount <= 0.1 THEN '1-10%'
            WHEN discount <= 0.2 THEN '11-20%'
            WHEN discount <= 0.3 THEN '21-30%'
            WHEN discount <= 0.5 THEN '31-50%'
            ELSE '>50%'
        END
    ORDER BY avg_margin_pct DESC
\"\"\")

profit_colors = [PALETTE[1] if v >= 0 else PALETTE[3]
                 for v in buckets["profit"]]
fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(buckets["discount_bucket"], buckets["profit"],
              color=profit_colors, edgecolor="white", zorder=3)
ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")

for bar, mg in zip(bars, buckets["avg_margin_pct"]):
    h = bar.get_height()
    offset = 500 if h >= 0 else -1500
    ax.text(bar.get_x() + bar.get_width()/2,
            h + offset,
            f"{fmt_usd(h)}\\n({mg}% margin)",
            ha="center", va="bottom", fontsize=8)

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.set_title("Total Profit by Discount Bucket")
ax.set_ylabel("Profit (USD)")
ax.set_xlabel("Discount Range")
plt.xticks(rotation=20)
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

NB07_SCATTER = """\
# ── Scatter: Discount % vs Profit per Line Item ───────────────────────────────
raw = fetch_df(cur, \"\"\"
    SELECT ROUND(discount*100, 0) AS discount_pct,
           ROUND(profit, 2)       AS profit
    FROM order_items LIMIT 2000
\"\"\")

fig, ax = plt.subplots(figsize=(9, 5))
ax.scatter(raw["discount_pct"], raw["profit"],
           alpha=0.35, s=12, color=PALETTE[0], edgecolors="none")
ax.axhline(0, color=PALETTE[3], linewidth=1.2, linestyle="--",
           label="Break-even")

# Compute and plot simple linear trend
import numpy as np
m, b = np.polyfit(raw["discount_pct"], raw["profit"], 1)
xs = sorted(raw["discount_pct"].unique())
ax.plot(xs, [m*x + b for x in xs], color=PALETTE[2],
        linewidth=2, linestyle="-", label=f"Trend  (slope={m:.1f})")

ax.set_title("Discount % vs Profit per Line Item")
ax.set_xlabel("Discount (%)")
ax.set_ylabel("Profit (USD)")
ax.legend(frameon=False)
plt.tight_layout()
plt.show()
"""

save("07_Discount_Impact.ipynb", [
    md_cell("# 07 — Discount Impact on Profitability\n"
            "How discounting erodes profit margins — "
            "bucketed analysis and correlation.\n"),
    code_cell(SETUP),
    code_cell(NB07_BUCKET),
    code_cell(NB07_SCATTER),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 08 — Top Customers
# ═════════════════════════════════════════════════════════════════════════════

NB08_TOP = """\
# ── Top 15 Customers by Lifetime Revenue ─────────────────────────────────────
top_cust = fetch_df(cur, \"\"\"
    SELECT c.customer_name, c.segment,
           COUNT(DISTINCT o.order_id)  AS total_orders,
           ROUND(SUM(oi.sales),2)      AS lifetime_revenue,
           ROUND(SUM(oi.profit),2)     AS lifetime_profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_name, c.segment
    ORDER BY lifetime_revenue DESC LIMIT 15
\"\"\")

seg_palette = {"Consumer": PALETTE[0], "Corporate": PALETTE[1],
               "Home Office": PALETTE[2]}
colors = [seg_palette.get(s, PALETTE[3]) for s in top_cust["segment"][::-1]]

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(top_cust["customer_name"][::-1],
               top_cust["lifetime_revenue"][::-1],
               color=colors, edgecolor="white")
for bar, margin in zip(bars, top_cust["margin_pct"][::-1]):
    ax.text(bar.get_width() + 200,
            bar.get_y() + bar.get_height()/2,
            f"{fmt_usd(bar.get_width())} ({margin}%)",
            va="center", fontsize=8)

handles = [mpatches.Patch(color=v, label=k) for k, v in seg_palette.items()]
ax.legend(handles=handles, frameon=False, fontsize=9, loc="lower right")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Lifetime Revenue (USD)")
ax.set_title("Top 15 Customers by Lifetime Revenue")
plt.tight_layout()
plt.show()
"""

NB08_PARETO = """\
# ── Pareto: Top 20% customers → % of revenue ─────────────────────────────────
all_cust = fetch_df(cur, \"\"\"
    SELECT c.customer_id,
           ROUND(SUM(oi.sales),2) AS revenue
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id ORDER BY revenue DESC
\"\"\")

df = all_cust.sort_values("revenue", ascending=False).reset_index(drop=True)
df["cum_rev_pct"]  = df["revenue"].cumsum() / df["revenue"].sum() * 100
df["customer_pct"] = (df.index + 1) / len(df) * 100

top20_rev = df[df["customer_pct"] <= 20]["cum_rev_pct"].max()
print(f"Top 20% of customers → {top20_rev:.1f}% of total revenue (Pareto)")

fig, ax = plt.subplots(figsize=(9, 5))
ax.fill_between(df["customer_pct"], df["cum_rev_pct"],
                alpha=0.12, color=PALETTE[0])
ax.plot(df["customer_pct"], df["cum_rev_pct"],
        color=PALETTE[0], linewidth=2)
ax.axvline(20, color=PALETTE[3], linestyle="--", linewidth=1.5,
           label="Top 20% customers")
ax.axhline(top20_rev, color=PALETTE[2], linestyle="--", linewidth=1.5,
           label=f"{top20_rev:.0f}% of revenue")
ax.annotate(f"  {top20_rev:.0f}%",
            xy=(20, top20_rev), fontsize=11,
            color=PALETTE[3], fontweight="bold")
ax.set_title("Pareto Chart: Cumulative Revenue by Customer %")
ax.set_xlabel("% of Customers")
ax.set_ylabel("Cumulative Revenue %")
ax.legend(frameon=False)
plt.tight_layout()
plt.show()
"""

save("08_Top_Customers.ipynb", [
    md_cell("# 08 — Top Customers & Customer Lifetime Value\n"
            "Identify highest-value customers by revenue, profit, "
            "and order frequency.\n"),
    code_cell(SETUP),
    code_cell(NB08_TOP),
    code_cell(NB08_PARETO),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 09 — Category Trends
# ═════════════════════════════════════════════════════════════════════════════

NB09_BAR = """\
# ── Annual Revenue by Category ────────────────────────────────────────────────
cat_year = fetch_df(cur, \"\"\"
    SELECT SUBSTR(o.order_date,1,4) AS year,
           p.category,
           ROUND(SUM(oi.sales),2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY SUBSTR(o.order_date,1,4), p.category
    ORDER BY year, category
\"\"\")

pivot = cat_year.pivot(index="year", columns="category",
                       values="revenue").fillna(0)

categories = pivot.columns.tolist()
years      = pivot.index.tolist()
bar_w      = 0.25
x          = range(len(years))

fig, ax = plt.subplots(figsize=(10, 5))
for k, (cat, col) in enumerate(zip(categories, PALETTE[:3])):
    offset = (k - 1) * bar_w
    bars   = ax.bar([i + offset for i in x], pivot[cat],
                    bar_w, color=col, label=cat, edgecolor="white", zorder=3)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 500,
                fmt_usd(bar.get_height()),
                ha="center", va="bottom", fontsize=7.5, color=col)

ax.set_xticks(list(x))
ax.set_xticklabels(years, fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.legend(frameon=False, title="Category")
ax.set_title("Annual Revenue by Product Category")
ax.set_ylabel("Revenue (USD)")
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

NB09_HEAT = """\
# ── Sub-Category Revenue Heatmap ─────────────────────────────────────────────
sub_year = fetch_df(cur, \"\"\"
    SELECT SUBSTR(o.order_date,1,4) AS year,
           p.sub_category,
           ROUND(SUM(oi.sales),2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY SUBSTR(o.order_date,1,4), p.sub_category
    ORDER BY year, sub_category
\"\"\")

heat = sub_year.pivot(index="sub_category", columns="year",
                      values="revenue").fillna(0)

fig, ax = plt.subplots(figsize=(9, 9))
im = ax.imshow(heat.values, aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(len(heat.columns)))
ax.set_xticklabels(heat.columns, fontsize=11)
ax.set_yticks(range(len(heat.index)))
ax.set_yticklabels(heat.index, fontsize=9)

for i in range(len(heat.index)):
    for j in range(len(heat.columns)):
        val = heat.values[i, j]
        ax.text(j, i, fmt_usd(val), ha="center", va="center",
                fontsize=8, fontweight="bold",
                color="white" if val > heat.values.max()*0.6 else "black")

plt.colorbar(im, ax=ax, label="Revenue (USD)", shrink=0.6)
ax.set_title("Sub-Category Revenue Heatmap by Year", pad=12)
plt.tight_layout()
plt.show()
"""

save("09_Category_Trends.ipynb", [
    md_cell("# 09 — Category & Sub-Category Trends Over Time\n"
            "How sales mix shifts across product categories year over year.\n"),
    code_cell(SETUP),
    code_cell(NB09_BAR),
    code_cell(NB09_HEAT),
    code_cell(CLOSE),
])

# ═════════════════════════════════════════════════════════════════════════════
# 10 — Marketing ROI
# ═════════════════════════════════════════════════════════════════════════════

NB10_MATRIX = """\
# ── Segment × Discount Tier Margin Heatmap ────────────────────────────────────
matrix_data = fetch_df(cur, \"\"\"
    SELECT c.segment,
           CASE
               WHEN oi.discount = 0    THEN 'No Discount'
               WHEN oi.discount <= 0.2 THEN 'Low (1-20%)'
               WHEN oi.discount <= 0.4 THEN 'Mid (21-40%)'
               ELSE 'High (>40%)'
           END AS discount_tier,
           COUNT(*)                        AS line_items,
           ROUND(SUM(oi.sales),2)          AS revenue,
           ROUND(SUM(oi.profit),2)         AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.segment,
        CASE
            WHEN oi.discount = 0    THEN 'No Discount'
            WHEN oi.discount <= 0.2 THEN 'Low (1-20%)'
            WHEN oi.discount <= 0.4 THEN 'Mid (21-40%)'
            ELSE 'High (>40%)'
        END
\"\"\")

tier_order = ["No Discount", "Low (1-20%)", "Mid (21-40%)", "High (>40%)"]
pivot_m    = matrix_data.pivot(index="segment", columns="discount_tier",
                               values="margin_pct")
pivot_m    = pivot_m.reindex(columns=tier_order)

fig, ax = plt.subplots(figsize=(9, 4))
im = ax.imshow(pivot_m.values, cmap="RdYlGn", vmin=-20, vmax=40,
               aspect="auto")
ax.set_xticks(range(len(pivot_m.columns)))
ax.set_xticklabels(pivot_m.columns, rotation=15, fontsize=10)
ax.set_yticks(range(len(pivot_m.index)))
ax.set_yticklabels(pivot_m.index, fontsize=10)

for i in range(len(pivot_m.index)):
    for j in range(len(pivot_m.columns)):
        val = pivot_m.values[i, j]
        txt = f"{val:.1f}%" if not (val != val) else "N/A"
        ax.text(j, i, txt, ha="center", va="center",
                fontsize=12, fontweight="bold",
                color="white" if abs(val) > 15 else "black")

plt.colorbar(im, ax=ax, label="Profit Margin %", orientation="vertical",
             fraction=0.04)
ax.set_title("Profit Margin % — Segment × Discount Tier")
plt.tight_layout()
plt.show()
"""

NB10_ROI = """\
# ── Sub-Category ROI % (Profit / Revenue) ─────────────────────────────────────
roi = fetch_df(cur, \"\"\"
    SELECT p.sub_category,
           ROUND(SUM(oi.sales),2)  AS revenue,
           ROUND(SUM(oi.profit),2) AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS roi_pct
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.sub_category
    ORDER BY roi_pct DESC
\"\"\")

colors = [PALETTE[1] if r >= 0 else PALETTE[3] for r in roi["roi_pct"][::-1]]
fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(roi["sub_category"][::-1], roi["roi_pct"][::-1],
               color=colors, edgecolor="white")
ax.axvline(0, color="grey", linewidth=0.8, linestyle="--")

for bar in bars:
    w       = bar.get_width()
    offset  = 0.4 if w >= 0 else -0.4
    align   = "left" if w >= 0 else "right"
    ax.text(w + offset, bar.get_y() + bar.get_height()/2,
            f"{w:.1f}%", va="center", ha=align, fontsize=9, fontweight="bold")

ax.set_xlabel("ROI %")
ax.set_title("Sub-Category ROI %  (Profit / Revenue × 100)")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

save("10_Marketing_ROI.ipynb", [
    md_cell("# 10 — Marketing ROI & Discount Effectiveness\n"
            "Which discounts drive volume without destroying margin? "
            "Segment × discount tier matrix and sub-category ROI.\n"),
    code_cell(SETUP),
    code_cell(NB10_MATRIX),
    code_cell(NB10_ROI),
    code_cell(CLOSE),
])

print("\nAll 10 notebooks regenerated successfully.")
