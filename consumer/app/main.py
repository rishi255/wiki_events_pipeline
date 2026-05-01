"""
Minimal Spark Structured Streaming POC

Reads raw JSON from the `wiki_raw_events` Kafka topic and writes it back to
`wiki_curated_events` with no schema transformation. This keeps the Spark
consumer lightweight for the POC.
"""

import os
import time

import yaml
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

IS_CONTAINER = os.getenv("KAFKA_BOOTSTRAP_SERVERS") is not None

# use Docker service name when running in container, otherwise localhost
KAFKA_BOOTSTRAP_SERVERS = (
    os.getenv("KAFKA_BOOTSTRAP_SERVERS") if IS_CONTAINER else "localhost:9092"
)

CONFIG_FILE_PATH = "./app/config.yaml" if IS_CONTAINER else "./config.yaml"

with open(CONFIG_FILE_PATH, "r") as f:
    config = yaml.safe_load(f)

RAW_TOPIC = config["TOPIC"]

CHECKPOINT_PATH = "./checkpoints/curated_checkpoint"

if os.name == "nt" and not os.environ.get("HADOOP_HOME"):
    print(
        "WARNING: Windows detected. If Spark fails to start, set HADOOP_HOME to a folder "
        "containing winutils.exe, or run the app inside Docker."
    )

# Create the Spark Session
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("wiki_events_pipeline")
    .config("spark.streaming.stopGracefullyOnShutdown", True)
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1")
    .config("spark.sql.shuffle.partitions", 4)
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print(f"📖 Reading from Kafka topic: {RAW_TOPIC}")
# Create the kafka_df to read from kafka

raw_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", RAW_TOPIC)
    .option("startingOffsets", "earliest")
    .option("header", "true")
    .load()
)

# View schema for raw kafka_df
raw_df.printSchema()
# raw_df.show()

simple_df = raw_df.selectExpr("CAST(value AS STRING) AS value")

# print(f"📝 Writing to Kafka topic: {CURATED_TOPIC}")
print(f"📝 Writing Kafka transformed output to console...")
# Write the output to console sink to check the output

query = (
    simple_df.writeStream.format("console")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .start()
    .awaitTermination()
)

print("✅ Spark Structured Streaming Consumer Started")
print(f"   Reading from:  {RAW_TOPIC}")
# print(f"   Writing to:    {CURATED_TOPIC}")
print(f"   Checkpoint:    {CHECKPOINT_PATH}")

try:
    while query.isActive:
        progress = query.lastProgress
        if progress:
            print(
                f"📊 Rows processed: {progress.get('numInputRows', 0)}, "
                f"Rows written: {progress.get('numSinkRows', 0)}"
            )
        time.sleep(10)
except KeyboardInterrupt:
    print("\n⏹️ Stopping stream...")
    query.stop()
    print("✅ Stream stopped successfully")
