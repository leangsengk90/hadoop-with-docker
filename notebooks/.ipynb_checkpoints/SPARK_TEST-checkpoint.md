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
    df = spark.createDataset([("Alice", 1), ("Bob", 2)], ["name", "id"]).toDF()
    df.show()

    # Stop Spark
    spark.stop()
    ```

## Installed Components:

- **Spark:** 3.5.1
- **Jupyter:** Notebook with `findspark`, `pyspark` installed.
- **Python:** 3.x
