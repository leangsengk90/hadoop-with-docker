#!/bin/bash
hdfs dfs -cat /data/superstore/output/part-00000
hdfs dfs -get -f /data/superstore/output/part-00000 .