from pathlib import Path
from ffmpeg import FFmpeg
from PIL import Image
from celery import Celery

app = Celery("converter", broker="redis://localhost:6379/0")


@app.task
def convert2mp4(filename):
    if not filename:
        return None
    try:
        converted_name = f"converted_{Path(filename).stem}.mp4"
        ffmpeg = (
            FFmpeg()
            .option("y")
            .input(filename)
            .output(
                converted_name,
                vcodec="libx264",
                pix_fmt="yuv420p",
                loglevel="quiet",
                **{
                    "profile:v": "main",
                    "level": "3.1",
                    "movflags": "faststart",
                    "crf": "18",
                },
            )
        )

        ffmpeg.execute()
        return converted_name
    except Exception:
        return None


@app.task
def convert2png(filename):
    try:
        converted_name = f"converted_{Path(filename).stem}.png"
        with Image.open(filename) as im:
            im.save(converted_name, "PNG")
            return converted_name
    except Exception as e:
        print(f"Error converting to PNG: {e}")
        return None
