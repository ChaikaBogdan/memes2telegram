FROM python:slim-bullseye
WORKDIR /app
COPY . .
RUN apt update && apt install ffmpeg --no-install-recommends -y
RUN ffmpeg -version
RUN pip install -r requirements.txt
CMD ["python", "main.py"]