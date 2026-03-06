#!/bin/bash
# Bootstrap script to start the right Hadoop services per container.
# Start SSH for intra-cluster communication and trust local hosts.
service ssh start
ssh-keyscan namenode resourcemanager datanode1 datanode2 >> ~/.ssh/known_hosts 2>/dev/null
# Ensure core Hadoop environment variables are set.
export JAVA_HOME=/usr/local/java
export HADOOP_CONF_DIR=/usr/local/hadoop/etc/hadoop
# NameNode: format storage on first run, then start HDFS.
if [ "$NODE_TYPE" = "namenode" ]; then
    if [ ! -d "/usr/local/hadoop/hadoop_data/hdfs/namenode" ]; then
        # Format only if the NameNode directory does not exist.
        /usr/local/hadoop/bin/hdfs namenode -format -force
    fi
    /usr/local/hadoop/sbin/start-dfs.sh
fi
# ResourceManager: wait for HDFS, then start YARN.
if [ "$NODE_TYPE" = "resourcemanager" ]; then
    sleep 10
    /usr/local/hadoop/sbin/start-yarn.sh
fi
# Keep the container running.
tail -f /dev/null

