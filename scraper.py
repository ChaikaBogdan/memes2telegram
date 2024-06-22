import asyncio
import shutil
import uuid
import re
import os
import logging
from functools import partial
from urllib.parse import urlparse
from pathlib import Path
import httpx
import validators
from bs4 import BeautifulSoup
from tempfile import gettempdir, mkdtemp
import instaloader

BOT_NAME = "@memes2telegram_bot"
BOT_SUPPORTED_VIDEOS = {"video/mp4", "image/gif", "video/webm"}
BOT_SUPPORTED_IMAGES = {"image/jpeg", "image/png", "image/webp"}
DTF_HOSTS = {
    "leonardo.osnova.io",
}
KNOWN_VIDEO_EXTENSIONS = {".mp4", ".webm", ".gif"}
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


def _get_referer_headers(url: str) -> dict[str, str]:
    parsed_url = urlparse(url)
    referer_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    host_url = urlparse(referer_url).netloc
    return {"Host": host_url, "Referer": referer_url}


async def get_headers(client, url, timeout: int = 10):
    headers = _get_referer_headers(url)
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


def is_9gag_video(url):
    if not url:
        return False
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    if host in NINE_GAG_HOSTS:
        return False
    path = parsed_url.path
    return path.endswith(".mp4") or path.endswith(".webm")


def parse_filename(url):
    url_parts = url.split("/")
    filename = url_parts[-1]
    return filename


def parse_extension(url):
    filename = os.path.basename(url)
    extension = os.path.splitext(filename)[1]
    if extension not in KNOWN_VIDEO_EXTENSIONS:
        return ".mp4"
    return extension


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
    file_name = str(uuid.uuid4())
    extension = parse_extension(file_url)
    if is_dtf_video(file_url):
        file_name = get_uuid(file_url)
        extension = ".mp4"
    if is_9gag_video(file_url):
        extension = ".webm"
    return os.path.join(gettempdir(), f"{file_name}{extension}")


async def download_file(url, timeout=60):
    filename = _generate_filename(url)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        headers = await get_headers(client, url)
        if not is_downloadable(headers):
            raise ScraperException(f"Can't download file from {url}")
        request_headers = _get_referer_headers(url)
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
is_tiktok_post = partial(_is_valid_post, TIKTOK_PATHS)


def _is_post_pic(tag):
    src = tag.get("src", "")
    return "/pics/post/" in src


def _get_post_pics(html_doc):
    soup = BeautifulSoup(html_doc, "html.parser")
    img_tags = soup.find_all("img")
    return [img["src"][2:] for img in img_tags if _is_post_pic(img)]


async def get_post_pics(post_url, timeout=30):
    request_headers = _get_referer_headers(post_url)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(post_url, headers=request_headers, timeout=timeout)
    response.raise_for_status()
    html_doc = response.content
    loop = asyncio.get_event_loop()
    post_pics = await loop.run_in_executor(None, _get_post_pics, html_doc)
    return post_pics


def _get_instagram_video(reel_url):
    shortcode = reel_url.split("/")[-2]
    tmp_folder = mkdtemp()
    L = instaloader.Instaloader(
        download_videos=True,
        download_comments=False,
        download_video_thumbnails=False,
        download_pictures=False,
        save_metadata=False,
        compress_json=False,
    )
    L.dirname_pattern = tmp_folder
    L.filename_pattern = shortcode
    post = instaloader.Post.from_shortcode(L.context, shortcode)

    try:
        L.download_post(post, target=shortcode)
        print(os.listdir(tmp_folder))
        for filename in os.listdir(tmp_folder):
            if filename.endswith(".mp4"):
                mp4_path = os.path.join(tmp_folder, filename)
                final_path = os.path.join(os.getcwd(), filename)
                shutil.move(mp4_path, final_path)
                return final_path
    finally:
        shutil.rmtree(tmp_folder)
    return None


async def get_instagram_video(reel_url):
    loop = asyncio.get_event_loop()
    file_name = await loop.run_in_executor(None, _get_instagram_video, reel_url)
    return file_name
