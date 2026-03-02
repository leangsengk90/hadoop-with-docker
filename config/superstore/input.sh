#!/bin/bash
hdfs dfs -mkdir -p /data/superstore/input/
hdfs dfs -put Sample-Superstore.csv /data/superstore/input/
