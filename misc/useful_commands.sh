# export producer requirements.txt from uv
uv export --group producer --no-dev --format requirements.txt --output-file producer/requirements.txt

# export consumer requirements.txt from uv
uv export --group consumer --no-dev --format requirements.txt --output-file consumer/requirements.txt

# Start infrastructure first (Kafka broker)
docker compose -f docker-compose.infra.yml up

# Then ingestion (Kafka producer)
docker compose -f docker-compose.ingestion.yml up

# Then compute stack (Kafka consumer(s))
docker compose -f docker-compose.compute.yml up

# Finally analytics stack (ClickHouse DB and Grafana)
docker compose -f docker-compose.analytics.yml up