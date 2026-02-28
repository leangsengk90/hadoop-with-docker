import sys

current_region = None
total_sales = 0

for line in sys.stdin:
    region, sales = line.strip().split('\t')
    sales = float(sales)

    if current_region == region:
        total_sales += sales
    else:
        if current_region:
            print(f"{current_region}\t{total_sales}")
        current_region = region
        total_sales = sales

if current_region:
    print(f"{current_region}\t{total_sales}")
