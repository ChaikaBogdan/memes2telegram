FROM python:3.11.2-slim-bullseye
WORKDIR /usr/src/app
COPY . .
RUN apt update && apt upgrade
RUN apt install ffmpeg --no-install-recommends -y
RUN pip install --no-cache-dir -r requirements.txt
