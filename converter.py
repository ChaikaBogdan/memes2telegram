from pathlib import Path
from ffmpeg import FFmpeg

from celery import Celery

app = Celery('converter', broker='redis://localhost:6379/0')

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
                    "movflags": "faststart",
                    "vf": "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                    "crf": "26",
                },
            )
        )

        ffmpeg.execute()
        return converted_name
    except Exception:
        return None
