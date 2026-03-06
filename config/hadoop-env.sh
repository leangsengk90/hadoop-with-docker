 # Java runtime for Hadoop processes.
export JAVA_HOME=/usr/local/java

# Run HDFS daemons as root inside the container.
export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
export HDFS_SECONDARYNAMENODE_USER=root

# Run YARN daemons as root inside the container.
export YARN_RESOURCEMANAGER_USER=root
export YARN_NODEMANAGER_USER=root
