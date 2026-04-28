#!/bin/bash

# Define the HDFS target directory
HDFS_DIR="/data/hive"

# 1. Create the directory in HDFS
# The -p flag ensures no error if the directory already exists
echo "Creating directory $HDFS_DIR in HDFS..."
hdfs dfs -mkdir -p $HDFS_DIR

# 2. List of normalized files to upload
files=(
    "customers.csv"
    "products.csv"
    "locations.csv"
    "orders.csv"
    "order_items.csv"
)

# 3. Loop through the files and put them into HDFS
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Uploading $file to $HDFS_DIR..."
        hdfs dfs -put -f "$file" $HDFS_DIR/
    else
        echo "Warning: $file not found in local directory. Skipping..."
    fi
done

# 4. Verify the upload
echo "Upload complete. Contents of HDFS $HDFS_DIR:"
hdfs dfs -ls $HDFS_DIR