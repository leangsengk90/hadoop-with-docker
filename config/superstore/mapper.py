import sys

for line in sys.stdin:
    # Clean and split the CSV line
    parts = line.strip().split(',')
    if len(parts) >= 18:
        region = parts[12]
        try:
            sales = float(parts[17])
            print(f"{region}\t{sales}")
        except ValueError:
            continue
