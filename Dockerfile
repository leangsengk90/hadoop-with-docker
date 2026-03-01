FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openjdk-8-jdk openssh-server openssh-client curl sudo \
    && rm -rf /var/lib/apt/lists/*

# Universal Java Link
RUN ACTUAL_PATH=$(readlink -f /usr/bin/java | sed "s:/bin/java::") && \
    ln -s $ACTUAL_PATH /usr/local/java

# SSH Setup
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 0600 ~/.ssh/authorized_keys && \
    echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

# Hadoop Install
ENV HADOOP_HOME=/usr/local/hadoop
RUN curl -L https://archive.apache.org/dist/hadoop/common/hadoop-3.4.0/hadoop-3.4.0.tar.gz | tar -xz -C /usr/local/ && \
    mv /usr/local/hadoop-3.4.0 $HADOOP_HOME

# Define Hadoop Users (The fix for your error)
ENV HDFS_NAMENODE_USER=root
ENV HDFS_DATANODE_USER=root
ENV HDFS_SECONDARYNAMENODE_USER=root
ENV YARN_RESOURCEMANAGER_USER=root
ENV YARN_NODEMANAGER_USER=root

# Force Java path into hadoop-env
RUN echo "export JAVA_HOME=/usr/local/java" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh

ENV JAVA_HOME=/usr/local/java
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

COPY bootstrap.sh /usr/local/bin/bootstrap.sh
RUN chmod +x /usr/local/bin/bootstrap.sh

WORKDIR $HADOOP_HOME
ENTRYPOINT ["/usr/local/bin/bootstrap.sh"]
 