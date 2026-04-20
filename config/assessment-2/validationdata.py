# Check if Product ID maps uniquely to name/category/subcategory
prod_check = df.groupby('Product ID')[['Product Name', 'Category', 'Sub-Category']].nunique()
print("Products with multiple names/categories:")
print(prod_check[prod_check.max(axis=1) > 1])

# Check if Customer ID maps uniquely to name/segment
cust_check = df.groupby('Customer ID')[['Customer Name', 'Segment']].nunique()
print("\nCustomers with multiple names/segments:")
print(cust_check[cust_check.max(axis=1) > 1])

# Check if Order ID maps uniquely to date/customer/location
order_check = df.groupby('Order ID')[['Order Date', 'Ship Date', 'Ship Mode', 'Customer ID', 'Postal Code']].nunique()
print("\nOrders with multiple dates/customers/locations:")
print(order_check[order_check.max(axis=1) > 1])