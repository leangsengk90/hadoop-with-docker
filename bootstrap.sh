#!/bin/bash

service ssh start
ssh-keyscan namenode resourcemanager datanode1 datanode2 >> ~/.ssh/known_hosts 2>/dev/null

# Force the environment to load
export JAVA_HOME=/usr/local/java
export HADOOP_CONF_DIR=/usr/local/hadoop/etc/hadoop

if [ "$NODE_TYPE" = "namenode" ]; then
    if [ ! -d "/usr/local/hadoop/hadoop_data/hdfs/namenode" ]; then
        /usr/local/hadoop/bin/hdfs namenode -format -force
    fi
    /usr/local/hadoop/sbin/start-dfs.sh
fi

if [ "$NODE_TYPE" = "resourcemanager" ]; then
    sleep 10
    /usr/local/hadoop/sbin/start-yarn.sh
fi

tail -f /dev/null
