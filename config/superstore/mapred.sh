mapred streaming \
  --input /data/superstore/input/Sample-Superstore.csv \
  --output /data/superstore/output \
  --mapper "python3 mapper.py" \
  --reducer "python3 reducer.py" \
  --file mapper.py \
  --file reducer.py