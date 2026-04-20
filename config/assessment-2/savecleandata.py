# 1. Customers Table
customers = df[['Customer ID', 'Customer Name', 'Segment']].drop_duplicates()

# 2. Products Table
# Handling multiple names for the same Product ID by taking the first occurrence
products = df[['Product ID', 'Product Name', 'Category', 'Sub-Category']].drop_duplicates(subset='Product ID', keep='first')

# 3. Locations Table
locations = df[['Postal Code', 'City', 'State', 'Country', 'Region']].drop_duplicates()

# 4. Orders Table
orders = df[['Order ID', 'Order Date', 'Ship Date', 'Ship Mode', 'Customer ID', 'Postal Code']].drop_duplicates()

# 5. OrderItems Table
order_items = df[['Row ID', 'Order ID', 'Product ID', 'Sales', 'Quantity', 'Discount', 'Profit']]

# Save to CSV
customers.to_csv('customers.csv', index=False)
products.to_csv('products.csv', index=False)
locations.to_csv('locations.csv', index=False)
orders.to_csv('orders.csv', index=False)
order_items.to_csv('order_items.csv', index=False)

# Summary of generated tables
summary = {
    "Customers": customers.shape,
    "Products": products.shape,
    "Locations": locations.shape,
    "Orders": orders.shape,
    "OrderItems": order_items.shape
}
print(summary)