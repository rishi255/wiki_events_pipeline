# export producer requirements.txt from uv
uv export --group producer --no-dev --format requirements.txt --output-file producer/requirements.txt

# export consumer requirements.txt from uv
uv export --group consumer --no-dev --format requirements.txt --output-file consumer/requirements.txt