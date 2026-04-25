import json
import threading
import time
import requests
from kafka import KafkaProducer, KafkaConsumer

# -----------------------------------
# CONFIG
# -----------------------------------
SSE_URL = "https://stream.wikimedia.org/v2/stream/recentchange"

TOPIC = "wiki_raw_events"
BROKER = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# Optional filters
ALLOWED_SERVER_NAMES = {"en.wikipedia.org"}
ALLOWED_TYPES = set()  # {"new", "edit"}


# -----------------------------------
# FILTERING
# Keep raw payload unchanged
# -----------------------------------
def event_matches_filters(payload: dict) -> bool:
    meta = payload.get("meta", {})

    # Skip canary events
    if meta.get("domain") == "canary":
        return False

    stream = meta.get("stream")

    # Extensible dispatch for future streams
    if stream == "mediawiki.recentchange":
        return recentchange_filter(payload)

    # Unknown stream: allow by default
    return True


def recentchange_filter(payload: dict) -> bool:
    server_name = payload.get("server_name")
    event_type = payload.get("type")

    if ALLOWED_SERVER_NAMES and server_name not in ALLOWED_SERVER_NAMES:
        return False

    if ALLOWED_TYPES and event_type not in ALLOWED_TYPES:
        return False

    return True


# -----------------------------------
# PRODUCER
# SSE -> Kafka (raw events)
# -----------------------------------
def sse_to_kafka():
    headers = {
        "User-Agent": "WikiRealtimePipeline/1.0",
        "Accept": "text/event-stream",
    }

    while True:
        try:
            print("Connecting to Wikipedia SSE stream...")

            with requests.get(
                SSE_URL,
                headers=headers,
                stream=True,
                timeout=60,
            ) as r:

                r.raise_for_status()

                for line in r.iter_lines(decode_unicode=True):

                    if not line or not line.startswith("data:"):
                        continue

                    try:
                        payload = json.loads(line[5:].strip())

                        if not event_matches_filters(payload):
                            continue

                        # Raw event pushed unchanged
                        producer.send(TOPIC, payload)

                    except Exception as e:
                        print("Producer parse/send error:", e)

        except Exception as e:
            print("Reconnect after error:", e)
            time.sleep(5)


# -----------------------------------
# CONSUMER
# Raw topic reader with stream-aware display only
# -----------------------------------
def kafka_consumer():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKER,
        auto_offset_reset="latest",
        group_id="wiki-demo-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    print("Kafka consumer started...\n")

    for msg in consumer:
        data = msg.value
        stream = data.get("meta", {}).get("stream")

        if stream == "mediawiki.recentchange":
            print(
                f"[{data.get('server_name')}] "
                f"{data.get('type')} | "
                f"{data.get('user')} -> "
                f"{data.get('title')}"
            )
        else:
            print(f"[{stream}] event received")


# -----------------------------------
# MAIN
# -----------------------------------
if __name__ == "__main__":
    threading.Thread(target=sse_to_kafka, daemon=True).start()
    kafka_consumer()
