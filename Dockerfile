FROM ubuntu:22.04
# Base OS with required packages for Java, SSH, and Hadoop tooling.
RUN apt-get update && apt-get install -y \
    openjdk-8-jdk openssh-server openssh-client curl sudo \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Jupyter Notebook and PySpark.
RUN pip3 install --no-cache-dir notebook pyspark findspark

# Create a stable JAVA_HOME symlink used by Hadoop.
RUN ACTUAL_PATH=$(readlink -f /usr/bin/java | sed "s:/bin/java::") && \
    ln -s $ACTUAL_PATH /usr/local/java

# SSH setup for intra-cluster communication.
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 0600 ~/.ssh/authorized_keys && \
    echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

# Download and install Hadoop.
ENV HADOOP_HOME=/usr/local/hadoop
RUN curl -L https://archive.apache.org/dist/hadoop/common/hadoop-3.4.0/hadoop-3.4.0.tar.gz | tar -xz -C /usr/local/ && \
    mv /usr/local/hadoop-3.4.0 $HADOOP_HOME

# Download and install Spark.
ENV SPARK_HOME=/usr/local/spark
RUN curl -L https://archive.apache.org/dist/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3.tgz | tar -xz -C /usr/local/ && \
    mv /usr/local/spark-3.5.1-bin-hadoop3 $SPARK_HOME

# Run Hadoop and Spark daemons as root in the container.
ENV HDFS_NAMENODE_USER=root
ENV HDFS_DATANODE_USER=root
ENV HDFS_SECONDARYNAMENODE_USER=root
ENV YARN_RESOURCEMANAGER_USER=root
ENV YARN_NODEMANAGER_USER=root
ENV SPARK_MASTER_USER=root
ENV SPARK_WORKER_USER=root

# Ensure Hadoop and Spark pick up JAVA_HOME.
RUN echo "export JAVA_HOME=/usr/local/java" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
RUN echo "export JAVA_HOME=/usr/local/java" >> $SPARK_HOME/conf/spark-env.sh

# Common environment variables for Hadoop and Spark tools.
ENV JAVA_HOME=/usr/local/java
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$SPARK_HOME/sbin
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV SPARK_CONF_DIR=$SPARK_HOME/conf
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Copy the startup script and make it executable.
COPY bootstrap.sh /usr/local/bin/bootstrap.sh
RUN chmod +x /usr/local/bin/bootstrap.sh

# Set working directory and container entrypoint.
WORKDIR $HADOOP_HOME
ENTRYPOINT ["/usr/local/bin/bootstrap.sh"]


