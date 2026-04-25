# Wikipedia Realtime Data Pipeline Project Context

## Project Goal

Build a realtime streaming analytics pipeline using Wikimedia EventStreams (SSE) as the live data source. The system should ingest Wikipedia edit events continuously, process them in near realtime, store analytics-ready data, and power a live dashboard showing metrics such as edits/sec, edits/minute, edits/hour, top pages, top wikis, and bot vs human activity.

This project is intended to be both:

* A strong data engineering portfolio project
* A practical end-to-end streaming system

---

## Live Data Source

### Wikimedia EventStreams

Public SSE endpoint currently used:

```text
https://stream.wikimedia.org/v2/stream/recentchange
```

Important notes:

* SSE = Server Sent Events over HTTP
* Client-side filtering is required for wiki/domain/type filters
* Canary events should be discarded (`meta.domain == "canary"`)
* Public source emits continuous realtime events

---

## High-Level Architecture

```text
Wikipedia EventStreams (SSE)
        ↓
Python Ingestion Service
(requests streaming consumer)
        ↓
Apache Kafka
(raw topic)
        ↓
PySpark Structured Streaming
(transformations + aggregations)
        ↓
Analytics Store
(ClickHouse or Apache Pinot)
        ↓
Grafana Dashboard
```

---

## Current Design Principles

### Bronze / Raw Layer

Keep ingestion raw and minimally opinionated.

Responsibilities:

* Connect to SSE stream
* Retry on disconnect
* Parse `data:` messages
* Apply lightweight optional filters
* Publish raw JSON unchanged to Kafka

Do **not** normalize, reshape, or mutate payloads in ingestion.

### Silver Layer

Done later in Spark.

Responsibilities:

* Parse schema
  n- Select useful fields
* Data quality checks
* Derivations
* Curated event model

### Gold Layer

Realtime metrics / aggregates.

Responsibilities:

* edits/sec
* edits/minute
* edits/hour
* top pages
* top domains
* bot ratios
* rolling windows

---

## Current Progress (Completed)

### 1. Kafka Running Locally

Kafka broker started via Docker.

Example:

```bash
docker run -d --name kafka -p 9092:9092 apache/kafka:latest
```

### 2. Python SSE Ingestion Working

Implemented stable ingestion using `requests` streaming.

Why `requests` chosen:

* Proven mature dependency
* Worked in environment where `aiohttp` got 403
* Simpler than niche SSE wrappers
* Reliable for chunked HTTP streams

### 3. Kafka Producer Working

Each Wikipedia event is published into topic:

```text
wiki_raw_events
```

### 4. Kafka Consumer Validation Working

Consumer reads topic and prints live events.

### 5. Optional Filtering Working

Supports filters such as:

* `server_name`
* event `type`
* canary removal

### 6. Decision Made: Keep Raw Payload Unchanged

No normalization in ingestion layer.

---

## Current Working Ingestion Flow

```text
Wikipedia SSE recentchange
→ requests.get(stream=True)
→ iter_lines()
→ parse JSON payload
→ optional filters
→ Kafka topic: wiki_raw_events
```

---

## Current Kafka Topic Strategy

### Existing

```text
wiki_raw_events
```

### Planned Future Topics

```text
wiki_curated_events
wiki_metrics_1s
wiki_metrics_1m
wiki_metrics_1h
```

---

## Why Raw Topic Matters

Use raw topic as source of truth.

Benefits:

* Replayable history
* Reprocessing later
* Debugging upstream issues
* Change downstream models safely
* Supports multiple consumers

---

## Next Steps (Priority Order)

## Phase 1: Spark Structured Streaming

Read from Kafka raw topic.

Tasks:

* Parse JSON schema
* Extract fields
* Use event timestamps
* Handle malformed rows
* Build curated dataframe

Suggested fields:

```text
event_time
server_name
title
user
type
bot
wiki
byte_delta
is_anonymous
```

Output:

```text
wiki_curated_events
```

---

## Phase 2: Realtime Aggregations

Use Spark window functions.

Metrics:

* edits per second
* edits per minute
* edits per hour
* edits by wiki
* bot vs human ratio
* unique users per minute
* top edited pages last 5 min

---

## Phase 3: Landing Database

Choose one.

### Option A: ClickHouse

Best for fastest implementation.

Pros:

* Simple setup
* Fast SQL analytics
* Great Grafana support

### Option B: Apache Pinot

Best for stronger streaming analytics portfolio value.

Pros:

* Built for realtime OLAP
* Great group-by latency
* Kafka-native ingestion

---

## Phase 4: Dashboard (Grafana)

Recommended dashboard panels:

### Core

* Current edits/sec
* edits/min trend line
* edits/hour cumulative
* top active wikis
* top edited pages
* bot traffic %

### Advanced

* anomaly spike alerts
* edit heatmap by time
* user activity leaderboard

---

## Recommended Immediate Milestone

Build this first:

```text
Kafka raw topic
→ Spark Structured Streaming
→ edits/minute metric
→ console sink
```

Then:

```text
→ ClickHouse/Pinot
→ Grafana
```

---

## Engineering Constraints / Lessons Learned

### 1. requests Worked Best in Current Environment

* `aiohttp` returned 403 from Wikimedia endpoint
* `requests` with User-Agent worked

### 2. Avoid Weak Dependencies

Rejected obscure SSE wrapper packages with low trust/adoption.

### 3. Keep Ingestion Simple

Project value is downstream analytics, not perfect ingestion tooling.

---

## Resume Narrative

Built an end-to-end realtime analytics pipeline that consumes Wikimedia live edit events via SSE, streams raw events into Kafka, processes data with Spark Structured Streaming, and powers operational dashboards for live editing activity.

---

## Current Recommended Tech Stack

```text
Python
requests
Kafka
PySpark Structured Streaming
ClickHouse or Apache Pinot
Grafana
Docker
```

---

## Future Optimizations (TODO)

1. Preserve raw ingestion architecture
2. Add modular configs
3. Add logging + metrics
4. Add Spark jobs cleanly
5. Dockerize full stack
6. Add schema management
7. Add Grafana provisioning
8. Keep code production-style and readable
