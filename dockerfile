FROM python:slim-bullseye
WORKDIR /app
COPY . .
RUN apt update && apt install ffmpeg --no-install-recommends -y
RUN pip install -r requirements.txt
CMD ["python" "--version"]
CMD ["ffmpeg" "-version"]
CMD ["python", "main.py"]