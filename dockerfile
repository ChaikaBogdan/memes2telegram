# Use an official Python base image with the desired version
FROM python:3.12.3-slim-bookworm

# Set environment variable to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /usr/src/app

# Install FFmpeg and Firefox without recommended packages
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg \
    firefox-esr \
    fortune-mod \
    cowsay \
    redis \
    # Clean up after package installation
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN python -m pip install --upgrade pip \
    && pip install poetry

# Copy only the pyproject.toml and poetry.lock files first to leverage Docker layer caching
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry install --no-root

# Copy the rest of the application files into the working directory
COPY . .

# Run the bot when the container starts
CMD ["poetry", "run", "python", "main.py"]
