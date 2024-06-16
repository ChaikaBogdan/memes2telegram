import logging
from pathlib import Path
from PIL import Image
from celery import Celery
from moviepy.editor import VideoFileClip

app = Celery("converter", broker="redis://localhost:6379/0")
logger = logging.getLogger(__name__)


def _get_converted_name(filename: str, ext: str, prefix: str = "converted_") -> str:
    stem = Path(filename).stem
    return f"{prefix}{stem}.{ext}"


@app.task
def convert2mp4(filename):
    if not filename:
        return None
    converted_name = _get_converted_name(filename, "mp4")
    try:
        clip = VideoFileClip(filename)
        clip.write_videofile(
            converted_name,
            codec="libx264",
            ffmpeg_params=[
                "-profile:v",
                "main",
                "-level",
                "3.1",
                "-movflags",
                "faststart",
                "-crf",
                "18",
            ],
            audio_codec="aac",  # Ensure audio codec is set if the input video has audio
            temp_audiofile="temp-audio.m4a",  # Temporary audio file to avoid issues
            remove_temp=True,  # Remove the temporary file after use
            threads=4,  # Number of threads to use for encoding
            preset="medium",  # Preset for encoding speed vs. quality balance
            logger=None,
        )
    except Exception:
        logger.exception("Cannot convert movie from %s to %s", filename, converted_name)
        converted_name = None
    return converted_name


@app.task
def convert2JPG(filename):
    if not filename:
       return None
    converted_name = _get_converted_name(filename, "jpg")
    try:
        with Image.open(filename) as im:
            im.save(converted_name, "JPEG")
    except Exception:
        logger.exception("Cannot save image %s to %s", filename, converted_name)
        converted_name = None
    return converted_name
