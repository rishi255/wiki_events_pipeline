# NOTE: This Dockerfile is being run with the context set to its parent folder
# This is why all the COPY and RUN commands etc are relative to the parent of the "consumer" folder.

FROM python:3.11-slim

# Adds metadata to image.
LABEL maintainer="Rishikesh Rachchh"

# dont write pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# dont buffer to stdout/stderr
ENV PYTHONUNBUFFERED 1
# required by PySpark / JVM
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="$JAVA_HOME/bin:$PATH"

# Sets the user name to use when running the image.
USER root
RUN apt update && \
    apt install --no-install-recommends -y build-essential gcc default-jdk && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Make a directory for our app
WORKDIR /consumer

# Install dependencies
COPY ./consumer/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY ./consumer/app ./app

# copy config file
COPY ./config.yaml ./app/

# Run the application
CMD ["python", "./app/main.py"]