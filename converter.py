import logging
import os
import uuid
from pathlib import Path
from PIL import Image
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


def _get_converted_name(filename: str, ext: str, prefix: str = "converted_") -> str:
    stem = Path(filename).stem
    return f"{prefix}{stem}.{ext}"


def convert2MP4(filename):
    if not filename:
        return None
    converted_name = _get_converted_name(filename, "mp4")
    temp_audio_filename = str(uuid.uuid4())
    num_threads = max(1, os.cpu_count() - 1)
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
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            ],
            audio_codec="aac",  # Ensure audio codec is set if the input video has audio
            temp_audiofile=f"{temp_audio_filename}.m4a",  # Temporary audio file to avoid issues
            remove_temp=True,  # Remove the temporary file after use
            threads=num_threads,  # Number of threads to use for encoding
            preset="medium",  # Preset for encoding speed vs. quality balance
            logger=None,
        )
    except Exception:
        logger.exception("Cannot convert movie from %s to %s", filename, converted_name)
        converted_name = None
    return converted_name


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
