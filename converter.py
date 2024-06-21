import logging
import tempfile
import os
from PIL import Image
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

NUM_THREADS = max(1, os.cpu_count() - 1)


def _get_converted_name(ext: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
    tmp_name = tmp_file.name
    tmp_file.close()
    os.unlink(tmp_name)
    return tmp_name


def convert2MP4(filename: str) -> str:
    converted_name = _get_converted_name("mp4")
    temp_audio_filename = _get_converted_name("m4a")
    clip = VideoFileClip(filename)
    width, height = clip.size
    # Check if video needs resizing
    if width > 1280 or height > 1280:
        # Determine target dimensions while preserving aspect ratio
        if width >= height:
            # Landscape or square video, resize width to 1280
            clip_rescaled = clip.resize(width=1280)
        else:
            # Portrait video, resize height to 1280
            clip_rescaled = clip.resize(height=1280)
    else:
        # Scale using "scale=trunc(iw/2)*2:trunc(ih/2)*2" preserving aspect ratio
        clip_rescaled = clip.resize(width=clip.w // 2 * 2, height=clip.h // 2 * 2)
    clip_rescaled.write_videofile(
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
            "29",
            "-b:v",
            "500",
            "-pix_fmt",
            "yuv420p",
        ],
        audio_codec="aac",  # Ensure audio codec is set if the input video has audio
        temp_audiofile=f"{temp_audio_filename}.m4a",  # Temporary audio file to avoid issues
        remove_temp=True,  # Remove the temporary file after use
        threads=NUM_THREADS,  # Number of threads to use for encoding
        preset="slow",  # Preset for encoding speed vs. quality balance
        logger=None,
    )
    return converted_name


def convert2JPG(filename: str) -> str:
    converted_name = _get_converted_name("jpg")
    with Image.open(filename) as im:
        im.save(converted_name, "JPEG")
    return converted_name
