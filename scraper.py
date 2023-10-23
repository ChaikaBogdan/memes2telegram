import uuid
import re
import os
from urllib.parse import urlparse
from pathlib import Path
import requests
import validators
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import logging

BOT_NAME = "@memes2telegram_bot"
BOT_SUPPORTED_VIDEOS = ["video/mp4", "image/gif", "video/webm"]
BOT_SUPPORTED_IMAGES = ["image/jpeg", "image/png"]


def is_downloadable_video(headers):
    return headers.get("content-type", "").lower() in BOT_SUPPORTED_VIDEOS


def is_downloadable_image(headers):
    return headers.get("content-type", "").lower() in BOT_SUPPORTED_IMAGES


def get_headers(url):
    return requests.head(url, allow_redirects=True, timeout=5).headers


def is_big(headers, size_limit_mb=200):
    size_limit_bytes = size_limit_mb * 1024 * 1024
    content_length = int(headers.get("content-length", 0))
    return content_length > size_limit_bytes


def is_dtf_video(url):
    if not url:
        return False
    host = urlparse(url).hostname
    allowlist = [
        "leonardo.osnova.io",
    ]
    return host in allowlist


def parse_filename(url):
    url_parts = url.split("/")
    filename = url_parts[-1]
    return filename


def parse_extension(url):
    filename = os.path.basename(url)
    extension = os.path.splitext(filename)[1]
    if extension not in [".mp4", ".webm", ".gif"]:
        return ".mp4"
    return extension


def get_uuid(url):
    return re.search(r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}", url).group()


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


def download_file(url):
    def generate_filename(file_url):
        if is_dtf_video(file_url):
            return get_uuid(file_url) + ".mp4"
        else:
            extension = parse_extension(file_url)
            return str(uuid.uuid4()) + extension

    headers = get_headers(url)
    if not is_downloadable_video(headers):
        raise Exception("Cannot download")
    filename = generate_filename(url)
    try:
        with open(filename, "wb") as file:
            file.write(
                requests.get(url, allow_redirects=True, stream=True, timeout=60).content
            )
        return filename
    except Exception as error:
        logging.error(error)
        remove_file(filename)
        return None


def download_image(url, timeout=10):
    def is_post_image(headers):
        content_type = headers.get("content-type", "").lower()
        return content_type.startswith("image/")

    if not validators.url(url):
        return None

    response = requests.get(url, allow_redirects=True, timeout=timeout)
    if is_post_image(response.headers):
        return response.content

    return None


def remove_file(filename):
    if filename:
        file_path = Path(filename)
        if file_path.is_file():
            file_path.unlink()


def is_joyreactor_post(url):
    if not url:
        return False
    allowlist = [
        "reactor.cc/post",
    ]
    return any(substring in url for substring in allowlist)


def is_instagram_post(url):
    if not url:
        return False
    allowlist = [
        "instagram.com/",
    ]
    return any(substring in url for substring in allowlist)


def is_tiktok_post(url):
    if not url:
        return False
    allowlist = [
        "tiktok.com/",
    ]
    return any(substring in url for substring in allowlist)


def get_post_pics(post_url, timeout=30):
    def is_post_pic(tag):
        src = tag.get("src", "")
        return "/pics/post/" in src

    html_doc = requests.get(post_url, allow_redirects=True, timeout=timeout).content
    soup = BeautifulSoup(html_doc, "html.parser")
    img_tags = soup.find_all("img")
    post_pics = [img["src"][2:] for img in img_tags if is_post_pic(img)]
    return post_pics


def get_instagram_video(post_url, browser):
    if not browser:
        return None
    try:
        browser.get(post_url)
        wait = WebDriverWait(browser, 60)
        wait.until(ec.presence_of_element_located((By.TAG_NAME, "video")))
        html_doc = browser.page_source
        soup = BeautifulSoup(html_doc, "html.parser")
        video = soup.find("video")
        return video["src"] if video else None
    except Exception:
        return None
    finally:
        browser.quit()


def get_tiktok_video(post_url, browser):
    if not browser:
        return None
    try:
        browser.get(post_url)
        wait = WebDriverWait(browser, 60)
        wait.until(ec.presence_of_element_located((By.TAG_NAME, "video")))
        html_doc = browser.page_source
        soup = BeautifulSoup(html_doc, "html.parser")
        video = soup.find("video")
        return video["src"] if video else None
    except Exception:
        return None
    finally:
        browser.quit()


def split2albums(items, size=10):
    return [items[i:i + size] for i in range(0, len(items), size)]
