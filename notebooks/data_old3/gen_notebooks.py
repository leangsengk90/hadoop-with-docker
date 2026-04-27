#!/usr/bin/env python3
"""Generate 10 analytics notebooks using Spark local mode + CSV files.
   No Hive / hive-metastore required — reads CSVs directly from the mounted path."""

import json, uuid, os

BASE = os.path.dirname(os.path.abspath(__file__))

def _uid():
    return uuid.uuid4().hex[:8]

def md_cell(src):
    return {"cell_type": "markdown", "id": _uid(), "metadata": {}, "source": src}

def code_cell(src):
    return {"cell_type": "code", "execution_count": None, "id": _uid(),
            "metadata": {}, "outputs": [], "source": src}

def notebook(cells):
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.8.0"}
        },
        "cells": cells
    }

def save(name, cells):
    path = os.path.join(BASE, name)
    with open(path, "w") as f:
        json.dump(notebook(cells), f, indent=1)
    print(f"  ✓ {name}")

# ── Shared Setup Cell ─────────────────────────────────────────────────────────
# CSVs are at /usr/local/hadoop/etc/hadoop/assessment-2/ inside the container
# (host: ./config/assessment-2/ mapped to /usr/local/hadoop/etc/hadoop)
# Spark runs in local mode — no hive-metastore needed.

SETUP = """\
import os, sys
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns

os.environ['JAVA_HOME']             = '/usr/local/java'
os.environ['SPARK_HOME']            = '/usr/local/spark'
os.environ['HADOOP_CONF_DIR']       = '/usr/local/hadoop/etc/hadoop'
os.environ['PYSPARK_PYTHON']        = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

try:
    spark.stop()
except:
    pass

# Local mode — no Hive/hive-metastore dependency
spark = (SparkSession.builder
    .appName("Superstore Analytics")
    .master("local[*]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# ── Load CSVs and register temp views ─────────────────────────────────────────
DATA = "/usr/local/hadoop/etc/hadoop/assessment-2"

def load(filename, renames):
    df = spark.read.option("header", "true").option("inferSchema", "true") \\
             .csv(f"{DATA}/{filename}")
    for old, new in renames.items():
        df = df.withColumnRenamed(old, new)
    return df

customers  = load("customers.csv",  {"Customer ID": "customer_id",
                                      "Customer Name": "customer_name",
                                      "Segment": "segment"})
orders     = load("orders.csv",     {"Order ID": "order_id",
                                      "Order Date": "order_date",
                                      "Ship Date": "ship_date",
                                      "Ship Mode": "ship_mode",
                                      "Customer ID": "customer_id",
                                      "Postal Code": "postal_code"})
order_items = load("order_items.csv", {"Row ID": "row_id",
                                        "Order ID": "order_id",
                                        "Product ID": "product_id",
                                        "Sales": "sales",
                                        "Quantity": "quantity",
                                        "Discount": "discount",
                                        "Profit": "profit"})
products   = load("products.csv",   {"Product ID": "product_id",
                                      "Product Name": "product_name",
                                      "Category": "category",
                                      "Sub-Category": "sub_category"})
locations  = load("locations.csv",  {"Postal Code": "postal_code",
                                      "City": "city",
                                      "State": "state",
                                      "Country": "country",
                                      "Region": "region"})

customers.createOrReplaceTempView("customers")
orders.createOrReplaceTempView("orders")
order_items.createOrReplaceTempView("order_items")
products.createOrReplaceTempView("products")
locations.createOrReplaceTempView("locations")

print("Spark", spark.version, "ready — all tables loaded.")
spark.sql("SHOW TABLES").show()

# ── Global chart style ─────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams.update({
    "figure.dpi": 120,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
})
PALETTE = sns.color_palette("muted")

def fmt_usd(v):
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.0f}"
"""

CLOSE = """\
spark.stop()
print("Spark stopped.")
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 01 — Monthly Sales Trend
# ═══════════════════════════════════════════════════════════════════════════════

NB01 = """\
# ── Monthly Sales Trend ───────────────────────────────────────────────────────
monthly = spark.sql(\"\"\"
    SELECT SUBSTR(o.order_date, 1, 7)  AS month,
           ROUND(SUM(oi.sales),  2)    AS sales,
           ROUND(SUM(oi.profit), 2)    AS profit
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY SUBSTR(o.order_date, 1, 7)
    ORDER BY month
\"\"\").toPandas()

tick_pos    = list(range(0, len(monthly), 3))
tick_labels = [monthly["month"].iloc[i] for i in tick_pos]

fig, ax = plt.subplots(figsize=(13, 5))
ax.fill_between(range(len(monthly)), monthly["sales"],
                alpha=0.12, color=PALETTE[0])
ax.plot(range(len(monthly)), monthly["sales"], marker="o", markersize=4,
        color=PALETTE[0], linewidth=2, label="Sales")
ax.fill_between(range(len(monthly)), monthly["profit"],
                alpha=0.12, color=PALETTE[1])
ax.plot(range(len(monthly)), monthly["profit"], marker="s", markersize=4,
        color=PALETTE[1], linewidth=2, label="Profit")
ax.set_xticks(tick_pos)
ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.legend(frameon=False)
ax.set_title("Monthly Sales Trend")
ax.set_xlabel("Month")
ax.set_ylabel("USD")
ax.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
"""

save("01_Monthly_Sales_Trend.ipynb", [
    md_cell("# 01 — Monthly Sales Trend\nSales and profit plotted month-by-month across the full dataset period.\n"),
    code_cell(SETUP),
    code_cell(NB01),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 02 — Profitability by Region
# ═══════════════════════════════════════════════════════════════════════════════

NB02 = """\
# ── Profitability by Region ───────────────────────────────────────────────────
region = spark.sql(\"\"\"
    SELECT l.region,
           ROUND(SUM(oi.sales),  2)                    AS sales,
           ROUND(SUM(oi.profit), 2)                    AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2) AS margin_pct
    FROM orders o
    JOIN order_items oi ON o.order_id    = oi.order_id
    JOIN locations   l  ON o.postal_code = l.postal_code
    GROUP BY l.region
    ORDER BY profit DESC
\"\"\").toPandas()

colors = [PALETTE[1] if v >= 0 else PALETTE[3] for v in region["profit"]]

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(region["region"], region["profit"],
              color=colors, edgecolor="white", zorder=3)
for bar, mg in zip(bars, region["margin_pct"]):
    h      = bar.get_height()
    offset = max(abs(h) * 0.03, 500)
    sign   = 1 if h >= 0 else -1
    ax.text(bar.get_x() + bar.get_width()/2,
            h + sign * offset,
            f"{fmt_usd(h)}\\n({mg}% margin)",
            ha="center", va="bottom" if h >= 0 else "top",
            fontsize=9, fontweight="bold")
ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.set_title("Total Profit by Region")
ax.set_ylabel("Profit (USD)")
ax.set_xlabel("Region")
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

save("02_Regional_Profitability.ipynb", [
    md_cell("# 02 — Profitability by Region\nTotal sales, profit, and margin compared across geographic regions.\n"),
    code_cell(SETUP),
    code_cell(NB02),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 03 — Sales by Product Category
# ═══════════════════════════════════════════════════════════════════════════════

NB03 = """\
# ── Sales Distribution by Category ───────────────────────────────────────────
cat = spark.sql(\"\"\"
    SELECT p.category,
           ROUND(SUM(oi.sales),  2) AS sales,
           ROUND(SUM(oi.profit), 2) AS profit
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category
    ORDER BY sales DESC
\"\"\").toPandas()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Sales Distribution by Product Category",
             fontsize=14, fontweight="bold", y=1.02)

wedges, texts, autotexts = axes[0].pie(
    cat["sales"], labels=cat["category"],
    autopct="%1.1f%%", colors=PALETTE[:len(cat)],
    startangle=140,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    pctdistance=0.78,
)
for at in autotexts:
    at.set_fontsize(11); at.set_fontweight("bold")
axes[0].set_title("Sales Share")

bar_w = 0.35
x     = range(len(cat))
b1 = axes[1].bar([i - bar_w/2 for i in x], cat["sales"],
                 bar_w, color=PALETTE[0], label="Sales",  edgecolor="white")
b2 = axes[1].bar([i + bar_w/2 for i in x], cat["profit"],
                 bar_w, color=PALETTE[1], label="Profit", edgecolor="white")
for bar in b1:
    axes[1].text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 500,
                 fmt_usd(bar.get_height()),
                 ha="center", va="bottom", fontsize=8, color=PALETTE[0])
for bar in b2:
    axes[1].text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 200,
                 fmt_usd(bar.get_height()),
                 ha="center", va="bottom", fontsize=8, color=PALETTE[1])
axes[1].set_xticks(list(x))
axes[1].set_xticklabels(cat["category"], fontsize=10)
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
axes[1].legend(frameon=False)
axes[1].set_title("Sales & Profit (USD)")
axes[1].grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

save("03_Category_Sales_Mix.ipynb", [
    md_cell("# 03 — Sales by Product Category\nSales distribution and absolute revenue/profit across Furniture, Office Supplies, and Technology.\n"),
    code_cell(SETUP),
    code_cell(NB03),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 04 — Top 10 Most Profitable Products
# ═══════════════════════════════════════════════════════════════════════════════

NB04 = """\
# ── Top 10 Most Profitable Products ──────────────────────────────────────────
top_prod = spark.sql(\"\"\"
    SELECT p.product_name,
           p.category,
           ROUND(SUM(oi.profit), 2)                    AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2) AS margin_pct
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.product_name, p.category
    ORDER BY profit DESC
    LIMIT 10
\"\"\").toPandas()

cat_pal = {"Furniture": PALETTE[0], "Office Supplies": PALETTE[1],
           "Technology": PALETTE[2]}
colors  = [cat_pal.get(c, PALETTE[3]) for c in top_prod["category"][::-1]]

fig, ax = plt.subplots(figsize=(11, 5))
bars = ax.barh(top_prod["product_name"].str[:45][::-1],
               top_prod["profit"][::-1],
               color=colors, edgecolor="white")
for bar, margin in zip(bars, top_prod["margin_pct"][::-1]):
    ax.text(bar.get_width() + 30,
            bar.get_y() + bar.get_height()/2,
            f"{fmt_usd(bar.get_width())} ({margin}%)",
            va="center", fontsize=8)
handles = [mpatches.Patch(color=v, label=k) for k, v in cat_pal.items()]
ax.legend(handles=handles, frameon=False, fontsize=9)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Profit (USD)")
ax.set_title("Top 10 Most Profitable Products")
plt.tight_layout()
plt.show()
"""

save("04_Top_Profitable_Products.ipynb", [
    md_cell("# 04 — Top 10 Most Profitable Products\nHighest-profit products ranked with margin percentage, colored by category.\n"),
    code_cell(SETUP),
    code_cell(NB04),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 05 — Customer Segment Sales
# ═══════════════════════════════════════════════════════════════════════════════

NB05 = """\
# ── Sales & Profit by Customer Segment ───────────────────────────────────────
seg = spark.sql(\"\"\"
    SELECT c.segment,
           COUNT(DISTINCT o.order_id)                  AS orders,
           ROUND(SUM(oi.sales),  2)                    AS sales,
           ROUND(SUM(oi.profit), 2)                    AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2) AS margin_pct
    FROM customers c
    JOIN orders      o  ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    GROUP BY c.segment
    ORDER BY sales DESC
\"\"\").toPandas()

bar_w = 0.35
x     = range(len(seg))
fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar([i - bar_w/2 for i in x], seg["sales"],
            bar_w, color=PALETTE[0], label="Sales",  edgecolor="white", zorder=3)
b2 = ax.bar([i + bar_w/2 for i in x], seg["profit"],
            bar_w, color=PALETTE[1], label="Profit", edgecolor="white", zorder=3)
for bar in b1:
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 1000,
            fmt_usd(bar.get_height()),
            ha="center", va="bottom", fontsize=9, color=PALETTE[0])
for bar, mg in zip(b2, seg["margin_pct"]):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 300,
            f"{fmt_usd(bar.get_height())}\\n({mg}%)",
            ha="center", va="bottom", fontsize=8, color=PALETTE[1])
ax.set_xticks(list(x))
ax.set_xticklabels(seg["segment"], fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.legend(frameon=False)
ax.set_title("Sales by Customer Segment")
ax.set_ylabel("USD")
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

save("05_Segment_Sales.ipynb", [
    md_cell("# 05 — Customer Segment Sales Distribution\nSales and profit comparison across Consumer, Corporate, and Home Office segments.\n"),
    code_cell(SETUP),
    code_cell(NB05),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 06 — Discount Impact on Profit
# ═══════════════════════════════════════════════════════════════════════════════

NB06 = """\
import numpy as np

# ── Scatter: Discount vs Profit ───────────────────────────────────────────────
raw = spark.sql(\"\"\"
    SELECT ROUND(discount * 100, 0) AS discount_pct,
           ROUND(profit, 2)         AS profit
    FROM order_items
    LIMIT 3000
\"\"\").toPandas()

# ── Bucketed summary ──────────────────────────────────────────────────────────
buckets = spark.sql(\"\"\"
    SELECT
        CASE
            WHEN discount = 0    THEN '0%'
            WHEN discount <= 0.1 THEN '1-10%'
            WHEN discount <= 0.2 THEN '11-20%'
            WHEN discount <= 0.3 THEN '21-30%'
            WHEN discount <= 0.5 THEN '31-50%'
            ELSE '>50%'
        END AS bucket,
        ROUND(AVG(profit), 2)            AS avg_profit,
        ROUND(AVG(profit/sales)*100, 2)  AS avg_margin_pct
    FROM order_items
    GROUP BY
        CASE
            WHEN discount = 0    THEN '0%'
            WHEN discount <= 0.1 THEN '1-10%'
            WHEN discount <= 0.2 THEN '11-20%'
            WHEN discount <= 0.3 THEN '21-30%'
            WHEN discount <= 0.5 THEN '31-50%'
            ELSE '>50%'
        END
    ORDER BY avg_margin_pct DESC
\"\"\").toPandas()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Discount Impact on Profitability",
             fontsize=14, fontweight="bold", y=1.02)

axes[0].scatter(raw["discount_pct"], raw["profit"],
                alpha=0.25, s=10, color=PALETTE[0], edgecolors="none")
axes[0].axhline(0, color=PALETTE[3], linewidth=1.2, linestyle="--",
                label="Break-even")
m, b = np.polyfit(raw["discount_pct"], raw["profit"], 1)
xs   = sorted(raw["discount_pct"].unique())
axes[0].plot(xs, [m*x + b for x in xs], color=PALETTE[2],
             linewidth=2, label=f"Trend (slope={m:.1f})")
axes[0].legend(frameon=False)
axes[0].set_title("Discount % vs Profit per Line Item")
axes[0].set_xlabel("Discount (%)")
axes[0].set_ylabel("Profit (USD)")

bucket_colors = [PALETTE[1] if v >= 0 else PALETTE[3]
                 for v in buckets["avg_profit"]]
bar2 = axes[1].bar(buckets["bucket"], buckets["avg_profit"],
                   color=bucket_colors, edgecolor="white", zorder=3)
axes[1].axhline(0, color="grey", linewidth=0.8, linestyle="--")
for bar, mg in zip(bar2, buckets["avg_margin_pct"]):
    h      = bar.get_height()
    offset = 2 if h >= 0 else -8
    axes[1].text(bar.get_x() + bar.get_width()/2, h + offset,
                 f"{fmt_usd(h)}\\n({mg}% margin)",
                 ha="center", va="bottom", fontsize=8)
axes[1].set_title("Avg Profit by Discount Bucket")
axes[1].set_xlabel("Discount Range")
axes[1].set_ylabel("Avg Profit (USD)")
plt.xticks(rotation=20)
axes[1].grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

save("06_Discount_vs_Profit.ipynb", [
    md_cell("# 06 — Discount Impact on Profitability\nScatter plot of discount vs profit with trend line, plus average profit by discount bucket.\n"),
    code_cell(SETUP),
    code_cell(NB06),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 07 — Shipping Mode Performance
# ═══════════════════════════════════════════════════════════════════════════════

NB07 = """\
# ── Shipping Mode Performance ─────────────────────────────────────────────────
ship = spark.sql(\"\"\"
    SELECT o.ship_mode,
           COUNT(DISTINCT o.order_id)                  AS orders,
           ROUND(SUM(oi.sales),  2)                    AS sales,
           ROUND(SUM(oi.profit), 2)                    AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2) AS margin_pct
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.ship_mode
    ORDER BY sales DESC
\"\"\").toPandas()

bar_w = 0.35
x     = range(len(ship))
fig, ax1 = plt.subplots(figsize=(9, 5))
ax2 = ax1.twinx()
b1 = ax1.bar([i - bar_w/2 for i in x], ship["sales"],
             bar_w, color=PALETTE[0], label="Sales",  edgecolor="white", zorder=3)
b2 = ax1.bar([i + bar_w/2 for i in x], ship["profit"],
             bar_w, color=PALETTE[1], label="Profit", edgecolor="white", zorder=3)
ax2.plot(x, ship["orders"], color=PALETTE[2], marker="o",
         linewidth=2, markersize=7, label="# Orders", zorder=4)
for bar in b1:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=8, color=PALETTE[0])
for bar in b2:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=8, color=PALETTE[1])
for xi, oi_val in zip(x, ship["orders"]):
    ax2.text(xi, oi_val + 10, str(int(oi_val)),
             ha="center", va="bottom", fontsize=9,
             color=PALETTE[2], fontweight="bold")
handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2,
           loc="upper right", frameon=False, fontsize=9)
ax1.set_xticks(list(x))
ax1.set_xticklabels(ship["ship_mode"], fontsize=10)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax1.set_title("Sales by Shipping Mode")
ax1.set_ylabel("USD")
ax2.set_ylabel("# Orders")
ax1.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

save("07_Shipping_Mode_Sales.ipynb", [
    md_cell("# 07 — Shipping Mode Performance\nSales, profit, and order volume across all shipping modes.\n"),
    code_cell(SETUP),
    code_cell(NB07),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 08 — Top 10 Customers by Revenue
# ═══════════════════════════════════════════════════════════════════════════════

NB08 = """\
# ── Top 10 Customers by Revenue ──────────────────────────────────────────────
top_cust = spark.sql(\"\"\"
    SELECT c.customer_name,
           c.segment,
           COUNT(DISTINCT o.order_id)                  AS orders,
           ROUND(SUM(oi.sales),  2)                    AS sales,
           ROUND(SUM(oi.profit), 2)                    AS profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2) AS margin_pct
    FROM customers c
    JOIN orders      o  ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    GROUP BY c.customer_name, c.segment
    ORDER BY sales DESC
    LIMIT 10
\"\"\").toPandas()

seg_pal = {"Consumer": PALETTE[0], "Corporate": PALETTE[1],
           "Home Office": PALETTE[2]}
colors  = [seg_pal.get(s, PALETTE[3]) for s in top_cust["segment"][::-1]]

fig, ax = plt.subplots(figsize=(11, 5))
bars = ax.barh(top_cust["customer_name"][::-1],
               top_cust["sales"][::-1],
               color=colors, edgecolor="white")
for bar, margin in zip(bars, top_cust["margin_pct"][::-1]):
    ax.text(bar.get_width() + 200,
            bar.get_y() + bar.get_height()/2,
            f"{fmt_usd(bar.get_width())} ({margin}%)",
            va="center", fontsize=8)
handles = [mpatches.Patch(color=v, label=k) for k, v in seg_pal.items()]
ax.legend(handles=handles, frameon=False, fontsize=9, loc="lower right")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlabel("Revenue (USD)")
ax.set_title("Top 10 Customers by Revenue")
plt.tight_layout()
plt.show()
"""

save("08_Top_Customers_Revenue.ipynb", [
    md_cell("# 08 — Top 10 Customers by Revenue\nHighest-revenue customers with profit margin, colored by segment.\n"),
    code_cell(SETUP),
    code_cell(NB08),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 09 — Sales vs Profit by State (Top 20)
# ═══════════════════════════════════════════════════════════════════════════════

NB09 = """\
# ── Sales vs Profit — Top 20 States ──────────────────────────────────────────
states = spark.sql(\"\"\"
    SELECT l.state,
           ROUND(SUM(oi.sales),  2) AS sales,
           ROUND(SUM(oi.profit), 2) AS profit
    FROM orders o
    JOIN order_items oi ON o.order_id    = oi.order_id
    JOIN locations   l  ON o.postal_code = l.postal_code
    GROUP BY l.state
    ORDER BY sales DESC
    LIMIT 20
\"\"\").toPandas()

y     = range(len(states))
bar_w = 0.38
fig, ax = plt.subplots(figsize=(11, 8))
ax.barh([i + bar_w/2 for i in y], states["sales"][::-1],
        bar_w, color=PALETTE[0], label="Sales",  edgecolor="white")
ax.barh([i - bar_w/2 for i in y], states["profit"][::-1],
        bar_w, color=PALETTE[1], label="Profit", edgecolor="white")
ax.set_yticks(list(y))
ax.set_yticklabels(states["state"][::-1], fontsize=9)
for i, (sal, prof) in enumerate(zip(states["sales"][::-1],
                                     states["profit"][::-1])):
    ax.text(sal + 200, i + bar_w/2, fmt_usd(sal), va="center", fontsize=7.5)
    ax.text(prof + 200 if prof >= 0 else prof - 200,
            i - bar_w/2, fmt_usd(prof),
            va="center", fontsize=7.5,
            ha="left" if prof >= 0 else "right")
ax.axvline(0, color="grey", linewidth=0.8, linestyle="--")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax.legend(frameon=False)
ax.set_xlabel("USD")
ax.set_title("Sales vs Profit for Top 20 States")
ax.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
"""

save("09_State_Sales_Profit.ipynb", [
    md_cell("# 09 — Sales vs Profit by State\nTop 20 states by revenue, with profit bars side-by-side for quick comparison.\n"),
    code_cell(SETUP),
    code_cell(NB09),
    code_cell(CLOSE),
])

# ═══════════════════════════════════════════════════════════════════════════════
# 10 — Average Order Value (AOV) by Segment
# ═══════════════════════════════════════════════════════════════════════════════

NB10 = """\
# ── Average Order Value (AOV) by Segment ─────────────────────────────────────
aov = spark.sql(\"\"\"
    SELECT c.segment,
           ROUND(SUM(oi.sales)  / COUNT(DISTINCT o.order_id), 2) AS avg_order_value,
           ROUND(SUM(oi.profit) / COUNT(DISTINCT o.order_id), 2) AS avg_order_profit,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2)            AS margin_pct,
           COUNT(DISTINCT o.order_id)                             AS total_orders
    FROM customers c
    JOIN orders      o  ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    GROUP BY c.segment
    ORDER BY avg_order_value DESC
\"\"\").toPandas()

bar_w = 0.35
x     = range(len(aov))
fig, ax1 = plt.subplots(figsize=(9, 5))
ax2 = ax1.twinx()
b1 = ax1.bar([i - bar_w/2 for i in x], aov["avg_order_value"],
             bar_w, color=PALETTE[0], label="Avg Order Value",  edgecolor="white", zorder=3)
b2 = ax1.bar([i + bar_w/2 for i in x], aov["avg_order_profit"],
             bar_w, color=PALETTE[1], label="Avg Order Profit", edgecolor="white", zorder=3)
ax2.plot(x, aov["margin_pct"], color=PALETTE[2], marker="D",
         linewidth=2, markersize=8, label="Margin %", zorder=4)
for bar in b1:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=9,
             fontweight="bold", color=PALETTE[0])
for bar in b2:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
             fmt_usd(bar.get_height()),
             ha="center", va="bottom", fontsize=9,
             fontweight="bold", color=PALETTE[1])
for xi, mg in zip(x, aov["margin_pct"]):
    ax2.text(xi, mg + 0.5, f"{mg:.1f}%",
             ha="center", va="bottom", fontsize=9,
             color=PALETTE[2], fontweight="bold")
handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2,
           loc="upper right", frameon=False, fontsize=9)
ax1.set_xticks(list(x))
ax1.set_xticklabels(aov["segment"], fontsize=11)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_usd(v)))
ax1.set_title("Average Order Value (AOV) by Customer Segment")
ax1.set_ylabel("USD per Order")
ax2.set_ylabel("Profit Margin %")
ax1.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.show()
"""

save("10_AOV_By_Segment.ipynb", [
    md_cell("# 10 — Average Order Value (AOV) by Segment\nAverage revenue and profit per order for each customer segment, with margin trend.\n"),
    code_cell(SETUP),
    code_cell(NB10),
    code_cell(CLOSE),
])

print("\nAll 10 SparkSQL (local mode, CSV) notebooks generated successfully.")
