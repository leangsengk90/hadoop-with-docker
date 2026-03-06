# Create HDFS input directory and upload the dataset.
hdfs dfs -mkdir -p /data/superstore/input/
hdfs dfs -put Sample-Superstore.csv /data/superstore/input/

# Run Hadoop Streaming with the Python mapper and reducer.
mapred streaming \
  --input /data/superstore/input/Sample-Superstore.csv \
  --output /data/superstore/output \
  --mapper "python3 mapper.py" \
  --reducer "python3 reducer.py" \
  --file mapper.py \
  --file reducer.py

# Pull results to local file and render the visualization.
hdfs dfs -cat /data/superstore/output/part-00000 > part-00000
python3 visualize.py