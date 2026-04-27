"""
Generate 10 business-analytics notebooks (SparkSQL + Matplotlib).
Run: python3 gen_analytics.py
"""
import json, uuid, os

OUT = os.path.dirname(os.path.abspath(__file__))

# ── reusable SparkSession setup (shared across all notebooks) ─────────────────
SETUP = '''\
import os, sys

os.environ["JAVA_HOME"]             = "/usr/local/java"
os.environ["SPARK_HOME"]            = "/usr/local/spark"
os.environ["HADOOP_CONF_DIR"]       = "/usr/local/hadoop/etc/hadoop"
os.environ["PYSPARK_PYTHON"]        = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import findspark
findspark.init()

from pyspark.sql import SparkSession

spark = SparkSession.getActiveSession()
if spark is None:
    spark = (SparkSession.builder
        .appName("__NAME__")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate())

spark.sparkContext.setLogLevel("WARN")

HDFS_BASE = "hdfs:///data"

def load_csv(name, renames):
    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .csv(f"{HDFS_BASE}/{name}.csv"))
    for old, new in renames.items():
        df = df.withColumnRenamed(old, new)
    df.createOrReplaceTempView(name)
    return df

load_csv("customers",   {"Customer ID":"customer_id","Customer Name":"customer_name","Segment":"segment"})
load_csv("orders",      {"Order ID":"order_id","Order Date":"order_date","Ship Date":"ship_date",
                          "Ship Mode":"ship_mode","Customer ID":"customer_id","Postal Code":"postal_code"})
load_csv("order_items", {"Row ID":"row_id","Order ID":"order_id","Product ID":"product_id",
                          "Sales":"sales","Quantity":"quantity","Discount":"discount","Profit":"profit"})
load_csv("products",    {"Product ID":"product_id","Product Name":"product_name",
                          "Category":"category","Sub-Category":"sub_category"})
load_csv("locations",   {"Postal Code":"postal_code","City":"city","State":"state",
                          "Country":"country","Region":"region"})

import matplotlib.pyplot as plt
%matplotlib inline
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np

plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
print("Ready.")
'''

# ── notebook definitions (title, description, query, viz) ────────────────────
NOTEBOOKS = [

# ── 01 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "01_Monthly_Sales_Trend.ipynb",
  title    = "01 — Monthly Sales & Profit Trend",
  desc     = "Track revenue and profit over time to spot seasonal patterns and growth trajectories.",
  query = """\
df = spark.sql('''
    SELECT
        DATE_FORMAT(TO_DATE(o.order_date, "M/d/yyyy"), "yyyy-MM") AS month,
        ROUND(SUM(oi.sales),  2) AS total_sales,
        ROUND(SUM(oi.profit), 2) AS total_profit
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY month
    ORDER BY month
''').toPandas()
print(df.head())
""",
  viz = """\
fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()

ax1.fill_between(df["month"], df["total_sales"], alpha=0.18, color="#1f77b4")
ax1.plot(df["month"], df["total_sales"],  marker="o", color="#1f77b4", lw=2, label="Sales")
ax2.plot(df["month"], df["total_profit"], marker="s", color="#d62728", lw=2, ls="--", label="Profit")

step = max(1, len(df) // 12)
ax1.set_xticks(range(0, len(df), step))
ax1.set_xticklabels(df["month"].iloc[::step], rotation=45, ha="right")
ax1.set_xlabel("Month"); ax1.set_ylabel("Total Sales ($)", color="#1f77b4")
ax2.set_ylabel("Total Profit ($)", color="#d62728")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))

lines1, lab1 = ax1.get_legend_handles_labels()
lines2, lab2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, lab1+lab2, loc="upper left")
ax1.set_title("Monthly Sales & Profit Trend", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 02 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "02_Regional_Sales_Performance.ipynb",
  title    = "02 — Regional Sales Performance",
  desc     = "Compare revenue, profit, and order volume across the four sales regions.",
  query = """\
df = spark.sql('''
    SELECT
        l.region,
        ROUND(SUM(oi.sales),  2)          AS total_sales,
        ROUND(SUM(oi.profit), 2)          AS total_profit,
        COUNT(DISTINCT o.order_id)        AS total_orders,
        ROUND(AVG(oi.sales), 2)           AS avg_item_value
    FROM orders o
    JOIN order_items oi ON o.order_id    = oi.order_id
    JOIN locations   l  ON o.postal_code = l.postal_code
    GROUP BY l.region
    ORDER BY total_sales DESC
''').toPandas()
print(df)
""",
  viz = """\
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colors = ["#1f77b4","#ff7f0e","#2ca02c","#d62728"]
w = 0.35; x = range(len(df))

axes[0].bar([i - w/2 for i in x], df["total_sales"],  w, label="Sales",  color=colors, alpha=0.85)
axes[0].bar([i + w/2 for i in x], df["total_profit"], w, label="Profit", color=colors, alpha=0.5)
axes[0].set_xticks(list(x)); axes[0].set_xticklabels(df["region"], rotation=15)
axes[0].set_title("Sales & Profit by Region", fontweight="bold"); axes[0].set_ylabel("Amount ($)")
axes[0].legend(); axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))

axes[1].pie(df["total_orders"], labels=df["region"], autopct="%1.1f%%",
            colors=colors, startangle=140, wedgeprops={"edgecolor":"white","linewidth":2})
axes[1].set_title("Order Count Share by Region", fontweight="bold")

plt.suptitle("Regional Sales Performance", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 03 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "03_Product_Category_Analysis.ipynb",
  title    = "03 — Product Category Revenue Analysis",
  desc     = "Break down sales and profit by product category and sub-category to guide assortment decisions.",
  query = """\
cat_df = spark.sql('''
    SELECT p.category,
           ROUND(SUM(oi.sales),  2) AS total_sales,
           ROUND(SUM(oi.profit), 2) AS total_profit
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category ORDER BY total_sales DESC
''').toPandas()

sub_df = spark.sql('''
    SELECT p.category, p.sub_category,
           ROUND(SUM(oi.sales),  2) AS total_sales,
           ROUND(SUM(oi.profit), 2) AS total_profit
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category, p.sub_category ORDER BY total_sales DESC
''').toPandas()
print(sub_df.head(10))
""",
  viz = """\
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
cat_colors = ["#1f77b4","#ff7f0e","#2ca02c"]

axes[0].barh(cat_df["category"][::-1], cat_df["total_sales"][::-1],  color=cat_colors[::-1], alpha=0.85, label="Sales")
axes[0].barh(cat_df["category"][::-1], cat_df["total_profit"][::-1], color=cat_colors[::-1], alpha=0.4,  label="Profit")
axes[0].set_title("Sales vs Profit by Category", fontweight="bold"); axes[0].set_xlabel("Amount ($)")
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}")); axes[0].legend()

top15 = sub_df.head(15)
short = [n[:30]+"…" if len(n)>30 else n for n in top15["sub_category"]]
axes[1].barh(short[::-1], top15["total_sales"][::-1], color="#1f77b4", alpha=0.82)
axes[1].set_title("Top 15 Sub-Categories by Sales", fontweight="bold"); axes[1].set_xlabel("Total Sales ($)")
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))

plt.suptitle("Product Category Revenue Analysis", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 04 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "04_Customer_Segment_Analysis.ipynb",
  title    = "04 — Customer Segment Analysis",
  desc     = "Revenue, profit, order frequency, and average sale value split by customer segment.",
  query = """\
df = spark.sql('''
    SELECT
        c.segment,
        COUNT(DISTINCT c.customer_id) AS num_customers,
        COUNT(DISTINCT o.order_id)    AS total_orders,
        ROUND(SUM(oi.sales),  2)      AS total_sales,
        ROUND(SUM(oi.profit), 2)      AS total_profit,
        ROUND(AVG(oi.sales),  2)      AS avg_item_value
    FROM customers c
    JOIN orders      o  ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    GROUP BY c.segment ORDER BY total_sales DESC
''').toPandas()
print(df)
""",
  viz = """\
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
colors = ["#1f77b4","#ff7f0e","#2ca02c"]

axes[0].pie(df["total_sales"], labels=df["segment"], autopct="%1.1f%%",
            colors=colors, startangle=140, wedgeprops={"edgecolor":"white","linewidth":2})
axes[0].set_title("Sales Share by Segment", fontweight="bold")

axes[1].bar(df["segment"], df["total_profit"], color=colors, alpha=0.85, edgecolor="white", lw=1.5)
for i,(s,v) in enumerate(zip(df["segment"],df["total_profit"])):
    axes[1].text(i, v+max(df["total_profit"])*0.01, f"${v:,.0f}", ha="center", fontsize=9)
axes[1].set_title("Total Profit by Segment", fontweight="bold"); axes[1].set_ylabel("Profit ($)")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))

x = range(len(df))
axes[2].bar([i-0.2 for i in x], df["num_customers"], 0.4, label="Customers", color="#9467bd", alpha=0.85)
axes[2].bar([i+0.2 for i in x], df["total_orders"],  0.4, label="Orders",    color="#8c564b", alpha=0.85)
axes[2].set_xticks(list(x)); axes[2].set_xticklabels(df["segment"])
axes[2].set_title("Customers & Orders by Segment", fontweight="bold"); axes[2].legend()

plt.suptitle("Customer Segment Analysis", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 05 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "05_Top_Products_Performance.ipynb",
  title    = "05 — Top Products Performance",
  desc     = "Identify the top 20 products by revenue and the top 15 by profit margin.",
  query = """\
top_sales = spark.sql('''
    SELECT p.product_name, p.category,
           ROUND(SUM(oi.sales),  2) AS total_sales,
           ROUND(SUM(oi.profit), 2) AS total_profit,
           SUM(oi.quantity)         AS total_qty
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.product_name, p.category ORDER BY total_sales DESC LIMIT 20
''').toPandas()

top_profit = spark.sql('''
    SELECT p.product_name, p.category,
           ROUND(SUM(oi.profit), 2) AS total_profit
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.product_name, p.category ORDER BY total_profit DESC LIMIT 15
''').toPandas()
print(top_sales[["product_name","category","total_sales"]].head())
""",
  viz = """\
from matplotlib.patches import Patch
cat_c = {"Technology":"#1f77b4","Furniture":"#ff7f0e","Office Supplies":"#2ca02c"}

fig, axes = plt.subplots(1, 2, figsize=(18, 8))

short_s = [n[:38]+"…" if len(n)>38 else n for n in top_sales["product_name"]]
c_s = [cat_c.get(c,"#999") for c in top_sales["category"]]
axes[0].barh(short_s[::-1], top_sales["total_sales"][::-1], color=c_s[::-1], alpha=0.85)
axes[0].set_title("Top 20 Products by Sales", fontweight="bold"); axes[0].set_xlabel("Total Sales ($)")
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
axes[0].legend(handles=[Patch(facecolor=v,label=k) for k,v in cat_c.items()], fontsize=8)

short_p = [n[:38]+"…" if len(n)>38 else n for n in top_profit["product_name"]]
c_p = [cat_c.get(c,"#999") for c in top_profit["category"]]
axes[1].barh(short_p[::-1], top_profit["total_profit"][::-1], color=c_p[::-1], alpha=0.85)
axes[1].set_title("Top 15 Products by Profit", fontweight="bold"); axes[1].set_xlabel("Total Profit ($)")
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
axes[1].legend(handles=[Patch(facecolor=v,label=k) for k,v in cat_c.items()], fontsize=8)

plt.suptitle("Top Products Performance", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 06 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "06_Discount_Impact_Analysis.ipynb",
  title    = "06 — Discount Impact on Profit Margins",
  desc     = "Quantify how increasing discount bands erode profit margins across all product categories.",
  query = """\
df = spark.sql('''
    SELECT
        CASE
            WHEN oi.discount = 0         THEN "0% None"
            WHEN oi.discount <= 0.10     THEN "1-10%"
            WHEN oi.discount <= 0.20     THEN "11-20%"
            WHEN oi.discount <= 0.30     THEN "21-30%"
            WHEN oi.discount <= 0.50     THEN "31-50%"
            ELSE                              ">50%"
        END AS discount_band,
        p.category,
        ROUND(AVG(oi.profit / oi.sales)*100, 2) AS avg_margin_pct,
        COUNT(*) AS transactions
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    WHERE oi.sales > 0
    GROUP BY discount_band, p.category ORDER BY discount_band
''').toPandas()

summary = spark.sql('''
    SELECT
        CASE
            WHEN oi.discount = 0     THEN "0% None"
            WHEN oi.discount <= 0.10 THEN "1-10%"
            WHEN oi.discount <= 0.20 THEN "11-20%"
            WHEN oi.discount <= 0.30 THEN "21-30%"
            WHEN oi.discount <= 0.50 THEN "31-50%"
            ELSE                          ">50%"
        END AS discount_band,
        ROUND(AVG(oi.profit / oi.sales)*100, 2) AS avg_margin_pct,
        COUNT(*) AS transactions
    FROM order_items oi WHERE oi.sales > 0
    GROUP BY discount_band ORDER BY discount_band
''').toPandas()
print(summary)
""",
  viz = """\
band_order = ["0% None","1-10%","11-20%","21-30%","31-50%",">50%"]
summary["discount_band"] = pd.Categorical(summary["discount_band"], categories=band_order, ordered=True)
summary = summary.sort_values("discount_band")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
bar_c = ["#2ca02c" if v >= 0 else "#d62728" for v in summary["avg_margin_pct"]]
axes[0].bar(summary["discount_band"], summary["avg_margin_pct"], color=bar_c, alpha=0.85, edgecolor="white")
axes[0].axhline(0, color="black", lw=0.9, ls="--")
axes[0].set_title("Avg Profit Margin % by Discount Band", fontweight="bold")
axes[0].set_xlabel("Discount Band"); axes[0].set_ylabel("Margin (%)")
axes[0].tick_params(axis="x", rotation=20)

pivot = df.pivot_table(index="category", columns="discount_band", values="avg_margin_pct")
pivot = pivot.reindex(columns=[c for c in band_order if c in pivot.columns])
im = axes[1].imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=-50, vmax=50)
axes[1].set_xticks(range(len(pivot.columns))); axes[1].set_xticklabels(pivot.columns, rotation=30, ha="right")
axes[1].set_yticks(range(len(pivot.index)));  axes[1].set_yticklabels(pivot.index)
axes[1].set_title("Margin % Heatmap: Category × Discount", fontweight="bold")
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        val = pivot.values[i, j]
        if not np.isnan(val):
            axes[1].text(j, i, f"{val:.1f}%", ha="center", va="center", fontsize=9,
                         color="white" if abs(val) > 30 else "black")
plt.colorbar(im, ax=axes[1], label="Margin %")
plt.suptitle("Discount Impact on Profit Margins", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 07 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "07_Shipping_Mode_Analysis.ipynb",
  title    = "07 — Shipping Mode Analysis",
  desc     = "Compare order volume, revenue, profit, and average days-to-ship across all shipping modes.",
  query = """\
df = spark.sql('''
    SELECT
        o.ship_mode,
        COUNT(DISTINCT o.order_id)  AS total_orders,
        ROUND(SUM(oi.sales),  2)    AS total_sales,
        ROUND(SUM(oi.profit), 2)    AS total_profit,
        ROUND(AVG(DATEDIFF(
            TO_DATE(o.ship_date,  "M/d/yyyy"),
            TO_DATE(o.order_date, "M/d/yyyy")
        )), 1)                      AS avg_days_to_ship
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.ship_mode ORDER BY total_sales DESC
''').toPandas()
print(df)
""",
  viz = """\
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
colors = ["#1f77b4","#ff7f0e","#2ca02c","#d62728"]

axes[0].pie(df["total_orders"], labels=df["ship_mode"], autopct="%1.1f%%",
            colors=colors, startangle=140, wedgeprops={"edgecolor":"white","linewidth":2})
axes[0].set_title("Order Volume Share by Ship Mode", fontweight="bold")

axes[1].bar(df["ship_mode"], df["total_sales"], color=colors, alpha=0.85, edgecolor="white")
for i,v in enumerate(df["total_sales"]):
    axes[1].text(i, v+max(df["total_sales"])*0.01, f"${v:,.0f}", ha="center", fontsize=8)
axes[1].set_title("Total Sales by Ship Mode", fontweight="bold"); axes[1].set_ylabel("Sales ($)")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
axes[1].tick_params(axis="x", rotation=15)

bars = axes[2].bar(df["ship_mode"], df["avg_days_to_ship"], color=colors, alpha=0.85, edgecolor="white")
for bar,v in zip(bars, df["avg_days_to_ship"]):
    axes[2].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.08, f"{v:.1f}d", ha="center", fontsize=10, fontweight="bold")
axes[2].set_title("Avg Days to Ship", fontweight="bold"); axes[2].set_ylabel("Days")
axes[2].tick_params(axis="x", rotation=15)

plt.suptitle("Shipping Mode Analysis", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 08 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "08_Top_Customers_Revenue.ipynb",
  title    = "08 — Top Customers by Revenue",
  desc     = "Rank the top 20 highest-value customers and visualise their order frequency and profitability.",
  query = """\
top_cust = spark.sql('''
    SELECT
        c.customer_name, c.segment,
        COUNT(DISTINCT o.order_id)                             AS total_orders,
        ROUND(SUM(oi.sales),  2)                               AS total_sales,
        ROUND(SUM(oi.profit), 2)                               AS total_profit,
        ROUND(SUM(oi.sales) / COUNT(DISTINCT o.order_id), 2)   AS avg_order_value
    FROM customers c
    JOIN orders      o  ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id    = oi.order_id
    GROUP BY c.customer_name, c.segment ORDER BY total_sales DESC LIMIT 20
''').toPandas()
print(top_cust[["customer_name","segment","total_sales","total_profit"]].head(10))
""",
  viz = """\
from matplotlib.patches import Patch
seg_c = {"Consumer":"#1f77b4","Corporate":"#ff7f0e","Home Office":"#2ca02c"}
c_list = [seg_c.get(s,"#999") for s in top_cust["segment"]]

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

short = [n[:30]+"…" if len(n)>30 else n for n in top_cust["customer_name"]]
axes[0].barh(short[::-1], top_cust["total_sales"][::-1], color=c_list[::-1], alpha=0.85)
axes[0].set_title("Top 20 Customers by Total Sales", fontweight="bold"); axes[0].set_xlabel("Total Sales ($)")
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
axes[0].legend(handles=[Patch(facecolor=v,label=k) for k,v in seg_c.items()], fontsize=9)

seg_num = {"Consumer":0,"Corporate":1,"Home Office":2}
sc = axes[1].scatter(top_cust["total_orders"], top_cust["total_sales"],
                     s=top_cust["total_profit"].clip(lower=1)*0.6,
                     c=[seg_num.get(s,0) for s in top_cust["segment"]],
                     cmap="Set1", alpha=0.75, edgecolors="white", linewidth=0.8)
for _,row in top_cust.iterrows():
    axes[1].annotate(row["customer_name"].split()[-1],
                     (row["total_orders"], row["total_sales"]), fontsize=7, alpha=0.8)
axes[1].set_xlabel("Total Orders"); axes[1].set_ylabel("Total Sales ($)")
axes[1].set_title("Orders vs Sales (bubble = profit)", fontweight="bold")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
axes[1].legend(handles=[Patch(facecolor=list(plt.cm.Set1.colors)[:3][i],label=k)
                         for k,i in seg_num.items()], fontsize=9)

plt.suptitle("Top 20 Customers Revenue Analysis", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 09 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "09_State_Sales_Performance.ipynb",
  title    = "09 — State-Level Sales Performance",
  desc     = "Rank all states by revenue and highlight profit margin to focus marketing investment.",
  query = """\
df = spark.sql('''
    SELECT
        l.state, l.region,
        COUNT(DISTINCT o.order_id)                          AS total_orders,
        ROUND(SUM(oi.sales),  2)                            AS total_sales,
        ROUND(SUM(oi.profit), 2)                            AS total_profit,
        ROUND(SUM(oi.profit)/SUM(oi.sales)*100, 2)          AS margin_pct
    FROM orders o
    JOIN order_items oi ON o.order_id    = oi.order_id
    JOIN locations   l  ON o.postal_code = l.postal_code
    GROUP BY l.state, l.region ORDER BY total_sales DESC
''').toPandas()
top20   = df.head(20)
bottom10 = df.tail(10)
print(df.head())
""",
  viz = """\
from matplotlib.patches import Patch
reg_c = {"West":"#1f77b4","East":"#ff7f0e","Central":"#2ca02c","South":"#d62728"}
legend_els = [Patch(facecolor=v,label=k) for k,v in reg_c.items()]

fig, axes = plt.subplots(2, 1, figsize=(16, 12))

ct = [reg_c.get(r,"#999") for r in top20["region"]]
axes[0].bar(top20["state"], top20["total_sales"], color=ct, alpha=0.85, edgecolor="white")
ax2 = axes[0].twinx()
ax2.plot(top20["state"], top20["margin_pct"], marker="D", color="black", lw=1.5, ms=5, label="Margin %")
ax2.axhline(0, color="red", lw=0.8, ls="--"); ax2.set_ylabel("Profit Margin %")
axes[0].set_title("Top 20 States by Sales  (◆ = profit margin %)", fontweight="bold")
axes[0].set_ylabel("Total Sales ($)")
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
axes[0].tick_params(axis="x", rotation=45); axes[0].legend(handles=legend_els, fontsize=8, loc="upper right")

cb = [reg_c.get(r,"#999") for r in bottom10["region"]]
axes[1].bar(bottom10["state"], bottom10["total_profit"], color=cb, alpha=0.85, edgecolor="white")
axes[1].axhline(0, color="red", lw=1, ls="--")
axes[1].set_title("10 Lowest-Sales States — Profit Check", fontweight="bold")
axes[1].set_ylabel("Total Profit ($)")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
axes[1].tick_params(axis="x", rotation=30); axes[1].legend(handles=legend_els, fontsize=8)

plt.suptitle("State-Level Sales Performance", fontsize=15, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

# ── 10 ────────────────────────────────────────────────────────────────────────
dict(
  filename = "10_Profitability_Dashboard.ipynb",
  title    = "10 — Profitability Dashboard",
  desc     = "Four-panel profit margin overview: by category, customer segment, region, and monthly trend.",
  query = """\
cat_m = spark.sql('''
    SELECT p.category,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct,
           ROUND(SUM(oi.profit),2) AS total_profit
    FROM order_items oi JOIN products p ON oi.product_id=p.product_id WHERE oi.sales>0
    GROUP BY p.category ORDER BY margin_pct DESC
''').toPandas()

seg_m = spark.sql('''
    SELECT c.segment,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct,
           ROUND(SUM(oi.profit),2) AS total_profit
    FROM customers c
    JOIN orders o ON c.customer_id=o.customer_id
    JOIN order_items oi ON o.order_id=oi.order_id WHERE oi.sales>0
    GROUP BY c.segment ORDER BY margin_pct DESC
''').toPandas()

reg_m = spark.sql('''
    SELECT l.region,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct,
           ROUND(SUM(oi.profit),2) AS total_profit
    FROM orders o
    JOIN order_items oi ON o.order_id=oi.order_id
    JOIN locations   l  ON o.postal_code=l.postal_code WHERE oi.sales>0
    GROUP BY l.region ORDER BY margin_pct DESC
''').toPandas()

mon_m = spark.sql('''
    SELECT DATE_FORMAT(TO_DATE(o.order_date,"M/d/yyyy"),"yyyy-MM") AS month,
           ROUND(SUM(oi.profit)/SUM(oi.sales)*100,2) AS margin_pct
    FROM orders o JOIN order_items oi ON o.order_id=oi.order_id WHERE oi.sales>0
    GROUP BY month ORDER BY month
''').toPandas()
print(cat_m)
""",
  viz = """\
fig, axes = plt.subplots(2, 2, figsize=(16, 11))

def bar_margin(ax, labels, vals, title):
    c = ["#2ca02c" if v >= 0 else "#d62728" for v in vals]
    ax.bar(labels, vals, color=c, alpha=0.85, edgecolor="white")
    for i,(l,v) in enumerate(zip(labels, vals)):
        ax.text(i, v + (0.4 if v >= 0 else -0.8), f"{v:.1f}%", ha="center", fontsize=9, fontweight="bold")
    ax.axhline(0, color="black", lw=0.8, ls="--")
    ax.set_title(title, fontweight="bold"); ax.set_ylabel("Margin %")

bar_margin(axes[0,0], cat_m["category"], cat_m["margin_pct"], "Profit Margin % by Category")
bar_margin(axes[0,1], seg_m["segment"],  seg_m["margin_pct"], "Profit Margin % by Segment")

reg_twin = axes[1,0].twinx()
axes[1,0].bar(reg_m["region"], reg_m["total_profit"], color="#1f77b4", alpha=0.45, label="Profit $")
reg_twin.plot(reg_m["region"], reg_m["margin_pct"], marker="D", color="#d62728", lw=2, ms=8, label="Margin %")
axes[1,0].set_title("Profit ($) & Margin % by Region", fontweight="bold")
axes[1,0].set_ylabel("Profit ($)", color="#1f77b4")
reg_twin.set_ylabel("Margin %", color="#d62728")
axes[1,0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))

axes[1,1].plot(mon_m["month"], mon_m["margin_pct"], marker="o", color="#2ca02c", lw=2)
axes[1,1].fill_between(mon_m["month"], mon_m["margin_pct"],
                        where=[v >= 0 for v in mon_m["margin_pct"]], alpha=0.2, color="#2ca02c")
axes[1,1].fill_between(mon_m["month"], mon_m["margin_pct"],
                        where=[v < 0  for v in mon_m["margin_pct"]], alpha=0.2, color="#d62728")
axes[1,1].axhline(0, color="black", lw=0.8, ls="--")
axes[1,1].set_title("Monthly Profit Margin % Trend", fontweight="bold"); axes[1,1].set_ylabel("Margin %")
step = max(1, len(mon_m)//10)
axes[1,1].set_xticks(range(0,len(mon_m),step))
axes[1,1].set_xticklabels(mon_m["month"].iloc[::step], rotation=45, ha="right")

plt.suptitle("Profitability Dashboard", fontsize=16, fontweight="bold")
plt.tight_layout(); plt.show()
"""),

]  # end NOTEBOOKS list


# ── helpers ───────────────────────────────────────────────────────────────────
def make_id():
    return uuid.uuid4().hex[:8]

def md_cell(src):
    return {"cell_type":"markdown","id":make_id(),"metadata":{},"source":src}

def code_cell(src):
    return {"cell_type":"code","execution_count":None,"id":make_id(),
            "metadata":{},"outputs":[],"source":src}

def write_nb(path, cells):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
            "language_info": {"name":"python","version":"3.10.0"}
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"  Created: {os.path.basename(path)}")


# ── generate ──────────────────────────────────────────────────────────────────
print(f"Writing {len(NOTEBOOKS)} notebooks to: {OUT}\n")
for nb in NOTEBOOKS:
    setup_code = SETUP.replace("__NAME__", nb["title"])
    cells = [
        md_cell(f"# {nb['title']}\n{nb['desc']}"),
        md_cell("## Setup — Spark Session & Load HDFS Tables"),
        code_cell(setup_code),
        md_cell("## Query"),
        code_cell(nb["query"].strip()),
        md_cell("## Visualisation"),
        code_cell(nb["viz"].strip()),
    ]
    path = os.path.join(OUT, nb["filename"])
    write_nb(path, cells)

print(f"\nDone — {len(NOTEBOOKS)} notebooks generated.")
