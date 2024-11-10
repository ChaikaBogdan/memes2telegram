import asyncio
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

from utils import run_command, which

logger = logging.getLogger(__name__)


def _get_converted_name(ext: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=f".{ext}") as tmp_file:
        return tmp_file.name


async def convert2MP4(filename: str) -> str:
    converted_name = _get_converted_name("mp4")
    ffmpeg_args = [
        "-i",
        filename,
        "-profile:v",
        "main",
        "-level",
        "3.1",
        "-movflags",
        "+faststart",
        "-crf",
        "29",
        "-c:a",
        "aac",
        "-b:v",
        "500k",
        "-pix_fmt",
        "yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-fps_mode",
        "auto",
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        converted_name
    ]
    ffmpeg_cmd = await which("ffmpeg")
    await run_command(ffmpeg_cmd, *ffmpeg_args)
    return converted_name


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


def _convert2LOG(content: str) -> str:
    converted_name = _get_converted_name("log")
    with open(converted_name, "w") as tmp_file:
        tmp_file.write(content)
    return converted_name


async def convert2LOG(content: str) -> str:
    loop = asyncio.get_event_loop()
    # io operation here using threads
    with ThreadPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _convert2LOG, content)
