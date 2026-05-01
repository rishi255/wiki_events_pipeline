# Wiki Events Pipeline — Technical Design

## Overview

This repository implements a small Docker-based real-time streaming pipeline using:

- Kafka (Confluent Platform with KRaft mode)
- Python producer application (`producer/app/main.py`)
- PySpark structured streaming consumer application (`consumer/app/main.py`)

The producer ingests Wikimedia Server-Sent Events (SSE) from the public Wikipedia event stream and publishes raw JSON events into a Kafka topic. The consumer reads that Kafka topic with PySpark Structured Streaming and writes a simplified stream output to the console.

## Architecture

### Services

- `kafka-kraft`
  - Image: `confluentinc/cp-kafka:8.2.0`
  - Runs a single-node Kafka broker and controller in KRaft mode.
  - Exposes Kafka listeners inside Docker at `kafka-kraft:29092` and host-mapped listener at `localhost:9092`.
  - Network: `broker-kafka`

- `python-producer`
  - Builds from `producer/Dockerfile`.
  - Uses `kafka-python` and `requests`.
  - Reads from Wikimedia SSE endpoint configured in `config.yaml`.
  - Produces events to Kafka topic `wiki_raw_events`.
  - Uses `KAFKA_BOOTSTRAP_SERVERS` environment variable inside Docker.

- `python-consumer`
  - Builds from `consumer/Dockerfile`.
  - Uses `pyspark` to start a SparkSession in local mode.
  - Reads from Kafka topic `wiki_raw_events` using Spark Kafka connector package.
  - Writes raw values to the console sink with checkpointing.

### Data flow

1. Producer connects to Wikimedia SSE at `https://stream.wikimedia.org/v2/stream/recentchange`.
2. Raw JSON events are filtered by server and event type, then published to Kafka topic `wiki_raw_events`.
3. Consumer starts a Spark Structured Streaming job.
4. Spark reads from the `wiki_raw_events` topic using `spark.readStream.format("kafka")`.
5. The consumer converts Kafka message payloads to string and writes them to the console.

## Key files

- `docker-compose.yml`
  - Defines the Kafka broker and both Python services.
  - Uses Docker network `broker-kafka`.
  - Passes `KAFKA_BOOTSTRAP_SERVERS` to producer and consumer.

- `config.yaml`
  - Defines the SSE source URL and Kafka topic.
  - Contains allowed server names and event types.

- `producer/Dockerfile`
  - Installs Python dependencies for the producer.
  - Copies `producer/app/main.py` and `config.yaml`.

- `consumer/Dockerfile`
  - Installs Python dependencies for the consumer.
  - Intended to install Java for PySpark.
  - Copies `consumer/app/main.py` and `config.yaml`.

- `consumer/app/main.py`
  - Configures SparkSession with `.master("local[*]")` and `spark.jars.packages`.
  - Reads Kafka source stream and writes to console.

## Implementation details

### Producer

- Uses a long-lived HTTP connection to the SSE endpoint.
- Reads event lines and parses `data:` payloads into JSON.
- Applies filter logic in `event_matches_filters()`.
- Publishes allowed events into Kafka using `KafkaProducer`.
- Logs event details on each successful send.

### Consumer

- Loads `config.yaml` and reads `TOPIC`.
- Creates SparkSession using:
  - `spark.sql.shuffle.partitions=4`
  - `spark.streaming.stopGracefullyOnShutdown=true`
  - `spark.jars.packages=org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1`
- Reads Kafka stream with `startingOffsets=earliest`.
- Converts `value` bytes to string and writes output to console.
- Uses a checkpoint directory at `./checkpoints/curated_checkpoint`.

## Consumer error analysis

The error observed when launching the consumer is:

```text
JAVA_HOME is not set
... PySparkRuntimeError: [JAVA_GATEWAY_EXITED] Java gateway process exited before sending its port number.
```

### Root cause

- The consumer image was built from `python:3.11-slim`.
- `consumer/Dockerfile` installed Python dependencies but did not install Java.
- PySpark requires a JVM to start the SparkContext.
- Without Java installed and `JAVA_HOME` configured, the Spark JVM gateway cannot launch.

### Fix applied

Updated `consumer/Dockerfile` to install Java and set `JAVA_HOME`:

- `default-jdk`
- `ENV JAVA_HOME=/usr/lib/jvm/default-java`
- `ENV PATH="$JAVA_HOME/bin:$PATH"`

This should allow PySpark to start successfully inside the consumer container.

## How to run

1. Build and start services:

    ```bash
    docker compose up --build
    ```

2. Verify `python-producer` connects to Kafka and produces messages.
3. Verify `python-consumer` starts Spark and begins reading from `wiki_raw_events`.

## Notes

- The consumer currently writes output to the console, not back into Kafka.
- The Kafka connector jar package is downloaded by Spark at runtime from Maven.
- If the consumer still fails after the Java fix, ensure network access from the container for artifact download and verify Spark package compatibility with the installed PySpark version.
