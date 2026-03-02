#!/usr/bin/env python3
import sys
import csv
# Use csv.reader to handle quoted fields and commas correctly
# We use sys.stdin as the input stream
reader = csv.reader(sys.stdin)

for row in reader:
    # 1. Skip the Header: Check if the first column is the header name
    if not row or row[0] == "Row ID":
        continue
    # 2. Extract Data: Region is index 12, Sales is index 17
    try:
        if len(row) >= 18:
            region = row[12]
            sales = row[17]
            # Output to Reducer: Region (Key) and Sales (Value)
            print(f"{region}\t{sales}")
    except (IndexError, ValueError):
        # Skip lines that are malformed
        continue