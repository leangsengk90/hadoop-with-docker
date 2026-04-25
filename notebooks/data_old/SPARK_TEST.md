# Spark and Jupyter Integration Test

To verify that Spark and Jupyter are correctly integrated, follow these steps:

1.  **Start the cluster:**

    ```bash
    docker-compose up -d --build
    ```

2.  **Access Jupyter Notebook:**
    Open your browser and go to `http://localhost:8889`.

3.  **Check Spark Master UI:**
    Open `http://localhost:8080`. You should see `namenode:7077` as the Spark Master and at least two workers connected.

4.  **Run a PySpark test in a Jupyter Notebook:**
    Create a new Python 3 notebook and run:

    ```python
    import findspark
    findspark.init()

    from pyspark.sql import SparkSession

    # Initialize Spark Session
    spark = SparkSession.builder \
        .appName("Jupyter Spark Test") \
        .master("spark://namenode:7077") \
        .getOrCreate()

    # Test Spark
    data = [("Alice", 1), ("Bob", 2)]
    columns = ["name", "id"]
    df = spark.createDataFrame(data, columns)
    df.show()

    # Stop Spark
    spark.stop()
    ```

5.  **Word Count using Spark RDDs:**
    Run this snippet in a new notebook cell to perform a word count:

    ```python
    import findspark
    findspark.init()

    from pyspark import SparkContext

    # Create SparkContext (required for RDD API)
    sc = SparkContext(appName="RDD Word Count", master="spark://namenode:7077")

    # Path to the text file (using file:// to specify local container path)
    input_file = "file:///usr/local/hadoop/etc/hadoop/homework-sparkrdd/BattleCreekDec19_2019.txt"

    # Process: Read -> Split -> Map (tuple) -> Reduce by word -> Print top 10
    try:
        counts = sc.textFile(input_file) \
                   .flatMap(lambda line: line.split(" ")) \
                   .filter(lambda word: word != "") \
                   .map(lambda word: (word.lower().strip(), 1)) \
                   .reduceByKey(lambda a, b: a + b)

        for word, count in counts.takeOrdered(10, key=lambda x: -x[1]):
            print(f"'{word}': {count}")
    finally:
        sc.stop()
    ```

## Installed Components:

- **Spark:** 3.5.1
- **Jupyter:** Notebook with `findspark`, `pyspark` installed.
- **Python:** 3.x
