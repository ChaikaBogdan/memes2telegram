import asyncio
import shutil
import uuid
import re
import os
import logging
import time
from functools import partial
from urllib.parse import urlparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import httpx
import validators
from bs4 import BeautifulSoup
from tempfile import gettempdir, mkdtemp
import instaloader
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from yt_dlp.postprocessor import PostProcessor

BOT_NAME = "@memes2telegram_bot"
BOT_SUPPORTED_VIDEOS = {"video/mp4", "image/gif", "video/webm"}
BOT_SUPPORTED_IMAGES = {"image/jpeg", "image/png", "image/webp"}
DTF_HOSTS = {
    "leonardo.osnova.io",
}
YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
}
KNOWN_VIDEO_EXTENSIONS = {".mp4", ".webm", ".gif"}
KNOWN_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
NINE_GAG_HOSTS = {
    "img-9gag-fun.9cache.com",
}
INSTAGRAM_PATHS = {
    "instagram.com/",
}
JOYREACTIOR_PATHS = {
    "reactor.cc/post",
}
TIKTOK_PATHS = {
    "tiktok.com/",
}
VK_PATHS = {"vk.com/video", "vk.com/clip-"}
UUID_PATTERN = re.compile(r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}")

logger = logging.getLogger(__name__)


def get_content_type(headers):
    return headers.get("content-type", "").lower()


def _is_content_type_supported(supported_values, headers):
    return get_content_type(headers) in supported_values


is_downloadable_video = partial(_is_content_type_supported, BOT_SUPPORTED_VIDEOS)
is_downloadable_image = partial(_is_content_type_supported, BOT_SUPPORTED_IMAGES)
is_downloadable = partial(
    _is_content_type_supported, BOT_SUPPORTED_VIDEOS | BOT_SUPPORTED_IMAGES
)


class ScraperException(Exception):
    pass


class UploadIsTooBig(ScraperException):
    pass


def check_filesize(converted: str, max_file_size_mb: int = 50) -> None:
    file_size_megabytes = os.path.getsize(converted) / (1024 * 1024)
    if file_size_megabytes > max_file_size_mb:
        raise UploadIsTooBig(
            f"File size {file_size_megabytes:.2f} MB exceeds the {max_file_size_mb} MB upload limit"
        )


def _get_referer_headers(url: str) -> dict[str, str]:
    parsed_url = urlparse(url)
    referer_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    host_url = urlparse(referer_url).netloc
    return {"Host": host_url, "Referer": referer_url}


async def get_headers(client, url, timeout: int = 10):
    headers = _get_referer_headers(url)
    headers["User-Agent"] = "Mozilla/5.0"
    response = await client.head(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.headers


def is_big(headers, size_limit_mb=200):
    size_limit_bytes = size_limit_mb * 1024 * 1024
    content_length = int(headers.get("content-length", 0))
    return content_length > size_limit_bytes


def is_dtf_video(url):
    if not url:
        return False
    host = urlparse(url).hostname
    return host in DTF_HOSTS


def is_youtube_video(url):
    if not url:
        return False
    host = urlparse(url).hostname
    return host in YOUTUBE_HOSTS


def is_9gag_video(url):
    if not url:
        return False
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    if host in NINE_GAG_HOSTS:
        return False
    path = parsed_url.path
    return path.endswith(".mp4") or path.endswith(".webm")


def get_extension(url: str) -> str:
    filename = os.path.basename(url)
    return os.path.splitext(filename)[1]


def get_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return filename


def _link_has_extension(extensions: set[str], url: str) -> bool:
    return get_extension(url) in extensions


is_generic_video = partial(_link_has_extension, KNOWN_VIDEO_EXTENSIONS)
is_generic_image = partial(_link_has_extension, KNOWN_IMAGE_EXTENSIONS)


def parse_extension(url: str) -> str:
    extension = get_extension(url)
    if extension in KNOWN_VIDEO_EXTENSIONS:
        return extension
    return ".mp4"


def get_uuid(url):
    return re.search(UUID_PATTERN, url).group()


def link_to_bot(text):
    return text.split(BOT_NAME)[-1].strip()


def is_bot_message(text):
    return text.startswith(BOT_NAME)


def is_private_message(message):
    return message.chat.type == "private"


def is_link(message):
    try:
        return bool(validators.url(message))
    except validators.utils.ValidationError:
        return False


def _generate_filename(file_url):
    if is_dtf_video(file_url):
        file_name = get_uuid(file_url)
        extension = ".mp4"
    elif is_9gag_video(file_url):
        file_name = str(uuid.uuid4())
        extension = ".webm"
    elif is_youtube_video(file_url):
        file_name = str(uuid.uuid4())
        extension = ".mp4"
    else:
        file_name = str(uuid.uuid4())
        extension = ".mp4"
    return os.path.join(gettempdir(), f"{file_name}{extension}")


async def download_file(url, timeout=60):
    filename = _generate_filename(url)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = await get_headers(client, url)
        except Exception:
            logger.exception("Can't get headers for %s - assuming it's valid link", url)
        else:
            if not is_downloadable(headers):
                raise ScraperException(f"Can't download file from {url}")
        request_headers = _get_referer_headers(url)
        request_headers["User-Agent"] = "Mozilla/5.0"
        async with client.stream(
            "GET", url, headers=request_headers, timeout=timeout
        ) as response:
            response.raise_for_status()
            content = await response.aread()
            with open(filename, "wb") as file:
                file.write(content)
    return filename


async def download_image(client, url, timeout=30):
    request_headers = _get_referer_headers(url)
    request_headers.update(
        {
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-User": "?1",
            "Priority": "u=1",
        }
    )
    async with client.stream(
        "GET", url, headers=request_headers, timeout=timeout
    ) as response:
        response.raise_for_status()
        content_type = get_content_type(response.headers)
        if not content_type.startswith("image/"):
            raise ScraperException(
                f"Downloaded file from {url} is not an image, it's {content_type}"
            )
        content = await response.aread()
        return content


def remove_file(filename):
    if filename:
        file_path = Path(filename)
        if file_path.is_file():
            file_path.unlink()


def _is_valid_post(allowed_paths, url):
    if not url:
        return False
    return any(substring in url for substring in allowed_paths)


is_joyreactor_post = partial(_is_valid_post, JOYREACTIOR_PATHS)
is_instagram_post = partial(_is_valid_post, INSTAGRAM_PATHS)


def is_instagram_reel(url):
    return any(re.search(rf"{re.escape(path)}reel/", url) for path in INSTAGRAM_PATHS)


def is_instagram_album(url):
    return any(re.search(rf"{re.escape(path)}p/", url) for path in INSTAGRAM_PATHS)


is_tiktok_post = partial(_is_valid_post, TIKTOK_PATHS)
is_vk_video = partial(_is_valid_post, VK_PATHS)


def _is_post_pic(tag):
    src = tag.get("src", "")
    return "/pics/post/" in src


def _get_post_pics(html_doc):
    soup = BeautifulSoup(html_doc, "html.parser")
    img_tags = soup.find_all("img")
    images = [img["src"] for img in img_tags if _is_post_pic(img)]
    return list(dict.fromkeys(images))


async def get_post_pics(post_url, timeout=30):
    request_headers = _get_referer_headers(post_url)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(post_url, headers=request_headers, timeout=timeout)
    response.raise_for_status()
    html_doc = response.content
    loop = asyncio.get_event_loop()
    # cpu bound operations here
    with ProcessPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _get_post_pics, html_doc)


def _get_instagram_pics(album_url):
    shortcode = album_url.split("/")[-2]
    tmp_folder = mkdtemp()
    L = instaloader.Instaloader(
        download_videos=False,
        download_comments=False,
        download_video_thumbnails=False,
        download_pictures=False,
        save_metadata=False,
        compress_json=False,
    )
    L.dirname_pattern = tmp_folder
    L.filename_pattern = shortcode
    post = instaloader.Post.from_shortcode(L.context, shortcode)

    image_urls = []

    try:
        # Loop through all media in the post and collect image URLs
        for _, node in enumerate(post.get_sidecar_nodes(), start=1):
            if node.is_video:
                continue
            image_urls.append(node.display_url)

        # Check if the post itself is an image (not a sidecar)
        if not image_urls and not post.is_video:
            image_urls.append(post.url)
        return image_urls

    finally:
        shutil.rmtree(tmp_folder)


async def get_instagram_pics(album_url):
    loop = asyncio.get_event_loop()
    # i/o bound operations here
    with ThreadPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _get_instagram_pics, album_url)


class FinishedVideoPostProcessor(PostProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_file_path = None
        self.title = None

    def run(self, info: dict) -> tuple[list, dict]:
        self.final_file_path = info["requested_downloads"][0]["filepath"]
        self.title = info.get("title", "")
        return [], info


class FinishedAudioPostProcessor(PostProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_file_path = None
        self.title = None

    def run(self, info: dict) -> tuple[list, dict]:
        self.final_file_path = info["filepath"]
        self.title = info["title"]
        return [], info


def _download_video(
    video_url: str, opts: dict, max_retries: int = 3, retry_delay_sec: int = 5
) -> str:
    finished_post_processor = FinishedVideoPostProcessor()
    with YoutubeDL(opts) as ydl:
        ydl.add_post_processor(finished_post_processor, when="after_video")
        try:
            error_code = ydl.download([video_url])
        except DownloadError as exc:
            raise ScraperException(f"Video {video_url} download error") from exc
        else:
            if error_code:
                raise ScraperException(
                    f"Video {video_url} download got error code {error_code}"
                )
    retries = 1
    while finished_post_processor.final_file_path is None:
        logger.warning(
            f"Try {retries} failed. Sleeping {retry_delay_sec} until video path is not set"
        )
        time.sleep(retry_delay_sec * retries)
        retries += 1
        if retries == max_retries:
            raise ScraperException(f"Video {video_url} won't download fully")
    try:
        check_filesize(finished_post_processor.final_file_path)
    except UploadIsTooBig:
        remove_file(finished_post_processor.final_file_path)
        raise
    return finished_post_processor.final_file_path, finished_post_processor.title


def _download_audio(
    audio_url: str, opts: dict, max_retries: int = 3, retry_delay_sec: int = 5
) -> tuple[str, str]:
    finished_post_processor = FinishedAudioPostProcessor()
    with YoutubeDL(opts) as ydl:
        ydl.add_post_processor(finished_post_processor)
        try:
            error_code = ydl.download([audio_url])
        except DownloadError as exc:
            raise ScraperException(f"Audio {audio_url} download error") from exc
        else:
            if error_code:
                raise ScraperException(
                    f"Audio {audio_url} download got error code {error_code}"
                )
    retries = 1
    while finished_post_processor.final_file_path is None:
        logger.warning(
            f"Try {retries} failed. Sleeping {retry_delay_sec} until audio path are not set"
        )
        time.sleep(retry_delay_sec * retries)
        retries += 1
        if retries == max_retries:
            raise ScraperException(f"Audio {audio_url} won't download fully")
    try:
        check_filesize(finished_post_processor.final_file_path)
    except UploadIsTooBig:
        remove_file(finished_post_processor.final_file_path)
        raise
    return finished_post_processor.final_file_path, finished_post_processor.title


def _get_youtube_video(youtube_url: str, max_filesize_mb: int = 50) -> str:
    size_filter = f"[filesize<{max_filesize_mb}M]"
    tmp_dir = gettempdir()
    formats = "/".join(
        (
            f"bestvideo*{size_filter}+bestaudio{size_filter}",
            f"best{size_filter}",
        )
    )
    opts = {
        "format": formats,
        "paths": {"home": tmp_dir, "temp": tmp_dir},
        "cachedir": False,
        "restrictfilenames": True,
        "noprogress": True,
        "no_color": True,
        "vcodec": "libx264",
        "acodec": "aac",
        "merge_output_format": "mp4",
        "max_filesize": (max_filesize_mb + 1) * 1024 * 1024,  # 51 mb
    }
    return _download_video(youtube_url, opts)


def _get_vk_video(vk_url: str, max_filesize_mb: int = 50) -> str:
    tmp_dir = gettempdir()
    opts = {
        "paths": {"home": tmp_dir, "temp": tmp_dir},
        "cachedir": False,
        "restrictfilenames": True,
        "noprogress": True,
        "no_color": True,
        "vcodec": "libx264",
        "acodec": "aac",
        "merge_output_format": "mp4",
        "max_filesize": (max_filesize_mb + 1) * 1024 * 1024,  # 51 mb
    }
    return _download_video(vk_url, opts)


def _get_instagram_video(reel_url: str, max_filesize_mb: int = 50) -> str:
    tmp_dir = gettempdir()
    opts = {
        "paths": {"home": tmp_dir, "temp": tmp_dir},
        "cachedir": False,
        "restrictfilenames": True,
        "noprogress": True,
        "no_color": True,
        "vcodec": "libx264",
        "acodec": "aac",
        "merge_output_format": "mp4",
        "max_filesize": (max_filesize_mb + 1) * 1024 * 1024,  # 51 mb
    }
    return _download_video(reel_url, opts)


def _get_youtube_audio(
    youtube_url: str, max_filesize_mb: int = 50, codec: str = "mp3"
) -> str:
    size_filter = f"[filesize<{max_filesize_mb}M]"
    tmp_dir = gettempdir()
    formats = "/".join(
        (
            f"bestaudio{size_filter}",
            f"best{size_filter}",
        )
    )
    opts = {
        "format": formats,
        "paths": {"home": tmp_dir, "temp": tmp_dir},
        "cachedir": False,
        "restrictfilenames": True,
        "noprogress": True,
        "no_color": True,
        "acodec": codec,
        "max_filesize": (max_filesize_mb + 1) * 1024 * 1024,  # 51 mb
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
            }
        ],
    }
    return _download_audio(youtube_url, opts)


async def get_youtube_video(youtube_url):
    loop = asyncio.get_event_loop()
    # both io and cpu bound operations here
    with ProcessPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _get_youtube_video, youtube_url)


async def get_youtube_audio(youtube_url):
    loop = asyncio.get_event_loop()
    # both io and cpu bound operations here
    with ProcessPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _get_youtube_audio, youtube_url)


async def get_vk_video(vk_url):
    loop = asyncio.get_event_loop()
    # both io and cpu bound operations here
    with ProcessPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _get_vk_video, vk_url)


async def get_instagram_video(reel_url):
    loop = asyncio.get_event_loop()
    # both io and cpu bound operations here
    with ProcessPoolExecutor(max_workers=1) as executor:
        return await loop.run_in_executor(executor, _get_instagram_video, reel_url)
