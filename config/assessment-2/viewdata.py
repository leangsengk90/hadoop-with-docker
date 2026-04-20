import pandas as pd

# Load the data
df = pd.read_csv('Sample-Superstore.csv', encoding='latin1')

# Inspect columns and data types
print(df.info())
print(df.head())