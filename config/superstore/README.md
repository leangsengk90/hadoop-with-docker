# Superstore Streaming

Hadoop Streaming demo: sum sales by region and plot a chart.

## Run

```sh
cd /usr/local/hadoop/etc/hadoop/superstore
bash input.sh
bash mapred.sh
bash save.sh
python3 visualize.py
```

## Output

- HDFS: /data/superstore/output/part-00000
- Local: part-00000
- Chart: superstore_sales_by_region.png
