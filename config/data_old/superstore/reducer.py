#!/usr/bin/env python3
import sys
current_region = None
total_sales = 0.0
for line in sys.stdin:
    # Clean whitespace and split by the tab character
    line = line.strip()
    if not line:
        continue
    try:
        region, sales = line.split('\t', 1)
        sales = float(sales)
    except ValueError:
        continue
    # Hadoop sorts the keys before they reach the Reducer
    if current_region == region:
        total_sales += sales
    else:
        # If the region changed, print the previous region's total
        if current_region:
            print(f"{current_region}\t{round(total_sales, 2)}")
        current_region = region
        total_sales = sales
# Print the last region after the loop finishes
if current_region:
    print(f"{current_region}\t{round(total_sales, 2)}")