# Use an official Python base image with the desired version
FROM python:3.11.9-slim-bookworm

# Set environment variable to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /bot

# Install deps without recommended and suggested packages
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg \
    fortune-mod \
    fortunes \
    cowsay \
    # Clean up after package installation
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN python -m pip install --upgrade pip && python -m pip install poetry

COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry install --no-root

ENTRYPOINT ["poetry"]
