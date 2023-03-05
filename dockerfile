FROM python:3.11.2-slim-bullseye
ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /usr/src/app
COPY . .
RUN apt-get update && apt-get upgrade
RUN apt-get install ffmpeg --no-install-recommends -y
RUN pip install --no-cache-dir -r requirements.txt
