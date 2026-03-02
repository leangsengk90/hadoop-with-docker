import matplotlib.pyplot as plt

# Data from your Hadoop output: hadoop fs -cat /data/superstore/output/part-00000
regions = ['Central', 'East', 'South', 'West']
sales = [501239.89, 678781.24, 391721.91, 725457.82]

# Optional: Sort the data from highest to lowest sales for better visualization
data = sorted(zip(regions, sales), key=lambda x: x[1], reverse=True)
regions, sales = zip(*data)

# Create the figure
plt.figure(figsize=(10, 6))

# Create the bar chart with custom colors
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # Classic color palette
plt.bar(regions, sales, color=colors)

# Adding labels and title
plt.xlabel('Region', fontsize=12, fontweight='bold')
plt.ylabel('Total Sales ($)', fontsize=12, fontweight='bold')
plt.title('Total Sales by Region (Sample - Superstore)', fontsize=14, fontweight='bold')

# Remove scientific notation (e.g., 1e5) from the Y-axis
plt.ticklabel_format(style='plain', axis='y')

# Add exact value labels on top of each bar for clarity
for i, v in enumerate(sales):
    plt.text(i, v + 10000, f"${v:,.2f}", ha='center', fontweight='bold', fontsize=10)

# Add a light grid for readability
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Save the plot to a file
plt.tight_layout()
plt.savefig('superstore_sales_by_region.png')

# Show the plot
plt.show()