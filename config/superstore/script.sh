#!/bin/bash
hadoop fs -mkdir -p /data/superstore/
hadoop fs -put superstore_no_header.csv /data/superstore/
