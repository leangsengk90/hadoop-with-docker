import findspark
findspark.init()

from pyspark import SparkContext, SparkConf

def main():
    # Configure Spark
    conf = SparkConf().setAppName("RDD Word Count").setMaster("spark://namenode:7077")
    sc = SparkContext(conf=conf)

    # Input file path (assumes file is in HDFS or local to container)
    input_path = "/usr/local/hadoop/etc/hadoop/homework-sparkrdd/BattleCreekDec19_2019.txt"
    
    try:
        # 1. Read the text file into an RDD
        text_rdd = sc.textFile(input_path)

        # 2. Split lines into words, map to (word, 1), and reduce by key
        word_counts = text_rdd.flatMap(lambda line: line.split(" ")) \
                             .map(lambda word: (word.lower(), 1)) \
                             .reduceByKey(lambda a, b: a + b)

        # 3. Collect and print the results (top 20 for brevity)
        print("--- Word Count Results (Top 20) ---")
        for word, count in word_counts.takeOrdered(20, key=lambda x: -x[1]):
            print(f"{word}: {count}")

        # Optional: Save output to a directory
        # word_counts.saveAsTextFile("/home/jovyan/notebooks/wordcount_output")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop Spark Context
        sc.stop()

if __name__ == "__main__":
    main()
