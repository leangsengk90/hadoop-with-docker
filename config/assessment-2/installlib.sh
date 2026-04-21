#!/bin/bash
docker exec namenode pip install matplotlib pandas 
docker exec datanode1 pip install matplotlib pandas 
docker exec datanode2 pip install matplotlib pandas