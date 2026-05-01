# NOTE: This Dockerfile is being run with the context set to its parent folder
# This is why all the COPY and RUN commands etc are relative to the parent of the "producer" folder.

FROM python:3.11-slim

# Adds metadata to image.
LABEL maintainer="Rishikesh Rachchh"

# dont write pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# dont buffer to stdout/stderr
ENV PYTHONUNBUFFERED 1

# Sets the user name to use when running the image.
USER root
RUN apt update && \
    apt install --no-install-recommends -y build-essential gcc && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Make a directory for our app
WORKDIR /producer

# Install dependencies
COPY ./producer/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY ./producer/app ./app

# Copy config handler code
COPY ./common ./app/common

# copy config file
COPY ./config.yaml ./app/

# define path to find config.yaml in container (used by /common/config.py)
ENV CONFIG_FILE_PATH "./app/config.yaml"

# Run the application
CMD ["python", "./app/main.py"]