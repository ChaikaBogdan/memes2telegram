# syntax=docker/dockerfile:1
# https://docs.docker.com/go/dockerfile-reference/
# https://docs.docker.com/go/dockerfile-user-best-practices/
# Use an official Python base image with the desired version
FROM python:3.11.9-slim-bookworm

# Set environment variable to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
# Stop complaining about superuser package instalation
ENV PIP_ROOT_USER_ACTION=ignore

# Install deps without recommended and suggested packages
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    xz-utils \
    fortune-mod \
    fortunes \
    figlet \
    cowsay \
    # Clean up after package installation
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz /tmp
RUN tar -xJf /tmp/ffmpeg-master-latest-linux64-gpl.tar.xz -C /tmp
RUN mv /tmp/ffmpeg-master-latest-linux64-gpl/bin/* /usr/local/bin/
RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffplay /usr/local/bin/ffprobe && ffmpeg -version
RUN rm /tmp/ffmpeg-master-latest-linux64-gpl.tar.xz && rm -r /tmp/ffmpeg-master-latest-linux64-gpl/

# Set the working directory inside the container
WORKDIR /bot

# Install Poetry
RUN python -m pip install --upgrade pip wheel setuptools && python -m pip install poetry

COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry install --no-root

ENTRYPOINT ["poetry"]
