#!/bin/bash
hadoop fs -mkdir -p /data/superstore/input/
hadoop fs -put Sample-Superstore.csv /data/superstore/input/
