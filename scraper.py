import shutil
import uuid
import re
import os
import logging
from functools import partial
from urllib.parse import urlparse
from pathlib import Path
import requests
import validators
from bs4 import BeautifulSoup
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


def is_image(link):
    headers = get_headers(link)
    return is_downloadable_image(headers)


def get_headers(url, timeout: int = 10):
    referer_url = get_referer(url)
    headers = {}
    headers["Referer"] = referer_url
    return requests.head(
        url, allow_redirects=True, headers=headers, timeout=timeout
    ).headers


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


def get_referer(url):
    # Add logic to determine the referer URL based on the file URL
    # For example, it might return the domain of the URL as a simple implementation
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def _generate_filename(file_url):
    if is_dtf_video(file_url):
        return get_uuid(file_url) + ".mp4"
    unique_file_name = str(uuid.uuid4())
    if is_9gag_video(file_url):
        return unique_file_name + ".webm"
    extension = parse_extension(file_url)
    return unique_file_name + extension


def download_file(url, timeout=60):
    headers = get_headers(url)
    if not is_downloadable(headers):
        raise ScraperException(f"Can't download file from {url}")
    referer_url = get_referer(url)
    headers = {}
    headers["Referer"] = referer_url
    filename = _generate_filename(url)
    response = requests.get(
        url,
        headers=headers,
        allow_redirects=True,
        stream=True,
        timeout=timeout,
    )
    response.raise_for_status()
    with open(filename, "wb") as file:
        file.write(response.content)
    return filename


def download_image(url, timeout=30):
    referer_url = get_referer(url) + "/"
    host_url = urlparse(referer_url).netloc
    headers = {}
    headers = {
        "Host": host_url,
        "Referer": referer_url,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-User": "?1",
        "Priority": "u=1",
    }
    print("HEADERS: " + str(headers))
    response = requests.get(
        url, headers=headers, allow_redirects=True, stream=True, timeout=timeout
    )
    response.raise_for_status()
    content_type = get_content_type(response.headers)
    if not content_type.startswith("image/"):
        raise ScraperException(
            f"Downloaded file from {url} is not an image, it's {content_type}"
        )
    return response.content


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


def is_webp_image(url):
    response = requests.head(url)
    content_type = get_content_type(response.headers)
    return content_type == "image/webp"


def _is_post_pic(tag):
    src = tag.get("src", "")
    return "/pics/post/" in src


def get_post_pics(post_url, timeout=30):
    html_doc = requests.get(post_url, allow_redirects=True, timeout=timeout).content
    soup = BeautifulSoup(html_doc, "html.parser")
    img_tags = soup.find_all("img")
    return [img["src"][2:] for img in img_tags if _is_post_pic(img)]


def get_instagram_video(reel_url):
    shortcode = reel_url.split("/")[-2]
    L = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    L.download_post(post, target=shortcode)
    for filename in os.listdir(shortcode):
        if filename.endswith(".mp4"):
            mp4_path = os.path.join(shortcode, filename)
            shutil.move(mp4_path, filename)
            shutil.rmtree(shortcode)
            return filename
    return None
