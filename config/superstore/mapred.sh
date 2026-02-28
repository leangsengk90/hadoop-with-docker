mapred streaming \
  --input /data/superstore/superstore_no_header.csv \
  --output /data/superstore/superstore_output \
  --mapper "python3 mapper.py" \
  --reducer "python3 reducer.py" \
  --file mapper.py \
  --file reducer.py