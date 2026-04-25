import matplotlib.pyplot as plt

# 1. Initialize empty lists to store data
regions = []
sales = []

# 2. Read the file (make sure 'part-00000' is in the same folder)
file_path = 'part-00000' 

try:
    with open(file_path, 'r') as f:
        for line in f:
            # Clean whitespace and split by tabs/spaces
            parts = line.strip().split()
            if len(parts) == 2:
                regions.append(parts[0])
                sales.append(float(parts[1]))
except FileNotFoundError:
    print(f"Error: The file {file_path} was not found.")
    exit()

# 3. Sort the data from highest to lowest sales
data = sorted(zip(regions, sales), key=lambda x: x[1], reverse=True)
regions, sales = zip(*data)

# 4. Create the plot
plt.figure(figsize=(10, 6))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
plt.bar(regions, sales, color=colors)

# Labels and Title
plt.xlabel('Region', fontsize=12, fontweight='bold')
plt.ylabel('Total Sales ($)', fontsize=12, fontweight='bold')
plt.title('Total Sales by Region (Sample - Superstore)', fontsize=14, fontweight='bold')

# Remove scientific notation
plt.ticklabel_format(style='plain', axis='y')

# Add exact value labels on top
for i, v in enumerate(sales):
    plt.text(i, v + 10000, f"${v:,.2f}", ha='center', fontweight='bold')

plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# 5. Save and Show
plt.savefig('superstore_sales_by_region.png')
print("Visualization saved as superstore_sales_by_region.png")
plt.show()