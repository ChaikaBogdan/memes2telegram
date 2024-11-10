# syntax=docker/dockerfile:1
# https://docs.docker.com/go/dockerfile-reference/
# https://docs.docker.com/go/dockerfile-user-best-practices/
# Use an official Python base image with the desired version
FROM python:3.11.10-slim-bookworm AS unpack
# Set environment variable to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install deps without recommended and suggested packages
RUN apt-get update && \
	apt-get install -y --no-install-recommends --no-install-suggests xz-utils \
	# Clean up after package installation
	&& apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz /tmp
RUN tar -xJf /tmp/ffmpeg-master-latest-linux64-gpl.tar.xz -C /tmp

FROM python:3.11.10-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
# Make async debug less painful
ENV PYTHONTRACEMALLOC=1
# Stop complaining about superuser package installation
ENV PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
    fortune-mod \
    fortunes \
    figlet \
    cowsay \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=unpack /tmp/ffmpeg-master-latest-linux64-gpl/bin/* /usr/local/bin/

RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffplay /usr/local/bin/ffprobe

# Set the working directory inside the container
WORKDIR /bot

COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN python -m pip install --upgrade pip wheel setuptools && \
	python -m pip install poetry && \
	poetry install --no-root

ENTRYPOINT ["poetry"]
