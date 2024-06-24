import asyncio
import logging
import tempfile
import math
import os
from PIL import Image
from moviepy.editor import VideoFileClip, concatenate_videoclips

logger = logging.getLogger(__name__)

NUM_THREADS = max(1, os.cpu_count() - 1)


def _get_converted_name(ext: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
    tmp_name = tmp_file.name
    tmp_file.close()
    os.unlink(tmp_name)
    return tmp_name


def _get_number_rounded_up_to_even(number: int) -> int:
    return int(math.ceil(float(number) / 2.0) * 2.0)


def _get_resized_clip_dimensions(
    clip_width: int, clip_height: int, max_size: int = 1280
) -> tuple[int, int]:
    if _get_number_rounded_up_to_even(max_size) != max_size:
        raise ValueError("Clip resize max size should be number divisible by two")
    aspect_ratio = float(clip_width) / float(clip_height)
    resized_clip_width = _get_number_rounded_up_to_even(clip_width)
    resized_clip_height = _get_number_rounded_up_to_even(clip_height)
    if aspect_ratio == 1.0 and resized_clip_width > max_size:
        # square video
        return max_size, max_size
    elif aspect_ratio > 1.0 and resized_clip_width > max_size:
        # horizontal video
        resized_clip_width = max_size
        resized_clip_height = _get_number_rounded_up_to_even(max_size / aspect_ratio)
    elif aspect_ratio < 1.0 and resized_clip_height > max_size:
        # vertical video
        resized_clip_height = max_size
        resized_clip_width = _get_number_rounded_up_to_even(max_size * aspect_ratio)
    return resized_clip_width, resized_clip_height


def _convert2MP4(filename: str) -> str:
    converted_name = _get_converted_name("mp4")
    temp_audio_filename = _get_converted_name("m4a")
    clip = VideoFileClip(filename)
    clip_width, clip_height = clip.size
    fps = clip.fps
    if fps < 30:
        fps = 30
    duration = clip.duration
    if duration <= 1.0:
        # Loop the clip until its total duration is at least 5 second
        loop_count = int(5.0 / duration) + 1
        clips = [clip] * loop_count
        video_clip = concatenate_videoclips(clips, method="chain").subclip(0, 5.0)
    else:
        video_clip = clip
    new_clip_width, new_clip_height = _get_resized_clip_dimensions(
        clip_width, clip_height
    )
    resize_kwargs = {}
    resize_kwargs["width"] = new_clip_width
    resize_kwargs["height"] = new_clip_height
    ffmpeg_params = [
        "-profile:v",
        "main",
        "-level",
        "3.1",
        "-movflags",
        "faststart",
        "-crf",
        "29",
        "-b:v",
        "500k",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
    ]
    if new_clip_width != clip_width or new_clip_height != clip_height:
        ffmpeg_params.append("-vf")
        scale_param = f"scale={resize_kwargs['width']}:{resize_kwargs['height']}"
        ffmpeg_params.append(scale_param)
    video_clip.write_videofile(
        converted_name,
        codec="libx264",
        ffmpeg_params=ffmpeg_params,
        audio_codec="aac",  # Ensure audio codec is set if the input video has audio
        temp_audiofile=f"{temp_audio_filename}.m4a",  # Temporary audio file to avoid issues
        remove_temp=True,  # Remove the temporary file after use
        threads=NUM_THREADS,  # Number of threads to use for encoding
        preset="slow",  # Preset for encoding speed vs. quality balance
        logger=None,
    )
    video_clip.close()
    return converted_name


async def convert2MP4(filename: str) -> str:
    loop = asyncio.get_event_loop()
    converted_file_name = await loop.run_in_executor(None, _convert2MP4, filename)
    return converted_file_name


def _convert2JPG(filename: str) -> str:
    converted_name = _get_converted_name("jpg")
    with Image.open(filename) as im:
        im.save(converted_name, "JPEG")
    return converted_name


async def convert2JPG(filename: str) -> str:
    loop = asyncio.get_event_loop()
    converted_file_name = await loop.run_in_executor(None, _convert2JPG, filename)
    return converted_file_name
