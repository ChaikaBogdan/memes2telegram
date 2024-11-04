import asyncio
import logging
import tempfile
import math
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from PIL import Image
from moviepy.editor import VideoFileClip, concatenate_videoclips

logger = logging.getLogger(__name__)

NUM_THREADS = max(1, os.cpu_count() - 1)


def _get_converted_name(ext: str, unlink: bool = True) -> str:
    tmp_file = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
    tmp_name = tmp_file.name
    if unlink:
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


def _convert2MP4(filename: str, min_fps: int = 24, min_duration: float = 1.0) -> str:
    # remove moviepy dependency and use ffmpeg directly
    # used mostly for .webm -> mp4, gif -> mp4
    converted_name = _get_converted_name("mp4")
    temp_audio_filename = _get_converted_name("m4a")
    clip = VideoFileClip(filename)
    clip_width, clip_height = clip.size
    new_clip_width, new_clip_height = _get_resized_clip_dimensions(
        clip_width, clip_height
    )
    fps = clip.fps
    if fps < min_fps:
        fps = min_fps
    duration = clip.duration
    if float(math.floor(duration)) < min_duration:
        loop_count = math.ceil(min_duration / duration)
        total_duration = duration * loop_count
        clips = [clip] * loop_count
        if duration < 1.0 and fps > loop_count:
            fps = math.floor(fps / loop_count)
        logger.info("Finished clip fps %d, total duration %f", fps, total_duration)
        video_clip = concatenate_videoclips(clips, method="chain").subclip(
            0, total_duration
        )
    else:
        video_clip = clip
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
        temp_audiofile=temp_audio_filename,  # Temporary audio file to avoid issues
        remove_temp=True,  # Remove the temporary file after use
        threads=NUM_THREADS,  # Number of threads to use for encoding
        preset="slow",  # Preset for encoding speed vs. quality balance
        logger=None,
    )
    video_clip.close()
    return converted_name


async def convert2MP4(filename: str) -> str:
    loop = asyncio.get_event_loop()
    # both io and cpu bound operations here
    with ProcessPoolExecutor(max_workers=1) as executor:
        converted_file_name = await loop.run_in_executor(executor, _convert2MP4, filename)
    return converted_file_name


def _convert2JPG(filename: str) -> str:
    converted_name = _get_converted_name("jpg")
    with Image.open(filename) as im:
        im.save(converted_name, "JPEG")
    return converted_name


async def convert2JPG(filename: str) -> str:
    loop = asyncio.get_event_loop()
    # io operation here using threads
    with ThreadPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _convert2JPG, filename)


def _convert2LOG(content: str):
    converted_name = _get_converted_name("log", unlink=False)
    with open(converted_name, "w") as tmp:
        tmp.write(content)
        tmp.seek(0)
    return converted_name


async def convert2LOG(content: str):
    loop = asyncio.get_event_loop()
    # io operation here using threads
    with ThreadPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _convert2LOG, content)
