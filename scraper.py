import uuid
import re
import os
from urllib.parse import urlparse
from pathlib import Path
import requests
import validators
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BOT_NAME = '@memes2telegram_bot'
BOT_SUPPORTED_VIDEOS = ['video/mp4', 'image/gif', 'video/webm']
BOT_SUPPORTED_IMAGES = ['image/jpeg', 'image/png']


def is_downloadable_video(headers):
    return headers.get('content-type').lower() in BOT_SUPPORTED_VIDEOS


def is_downloadable_image(headers):
    return headers.get('content-type').lower() in BOT_SUPPORTED_IMAGES


def get_headers(url):
    return requests.head(url, allow_redirects=True, timeout = 5).headers


def is_big(headers):
    return int(headers.get('content-length')) > 2e+8  # 200mb


def is_dtf_video(url):
    host = urlparse(url).hostname
    allowlist = [
        "leonardo.osnova.io",
    ]
    if host and host in allowlist:
        return True
    return False


def parse_filename(url):
    return url.rsplit('/', 1)[1]


def without_extension(filename):
    pathname, _ = os.path.splitext(filename)
    return pathname.split('/')[-1]


def get_uuid(url):
    return re.search(r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}", url).group()


def link_to_bot(text):
    return text.split(BOT_NAME)[-1].strip()


def is_bot_message(text):
    return text[0:len(BOT_NAME)] == BOT_NAME

def is_private_message(message):
    return message.chat.type == 'private'

def is_link(message):
    return validators.url(message)


def download_file(url):
    if is_dtf_video(url):
        filename = get_uuid(url) + '.mp4'
    else:
        _, extension = os.path.splitext(parse_filename(url))
        filename = str(uuid.uuid4()) + extension
    with open(filename, 'wb') as file:
        file.write(requests.get(url, allow_redirects=True, timeout = 60).content)
    return filename


def in_memory_download_file(url):
    if not is_link(url):
        return None
    return requests.get(url, allow_redirects=True, timeout = 60).content


def download_image(url):
    if not is_link(url):
        return None
    if is_downloadable_image(get_headers(url)):
        return requests.get(url, allow_redirects=True, timeout = 10).content
    return None


def remove_file(filename):
    if not filename:
        return None
    file = Path(filename)
    if file.is_file():
        file.unlink()


def is_joyreactor_post(url):
    return 'reactor.cc/post/' in url

def is_instagram_post(url):
    return 'instagram.com/' in url

def get_post_pics(post_url):
    html_doc = requests.get(post_url, allow_redirects=True, timeout = 30).content
    soup = BeautifulSoup(html_doc, 'html.parser')
    img_tags = soup.find_all('img')
    post_pics = []
    for img in img_tags:
        src = img['src']
        if "/pics/post/" in src:
            post_pics.append(src[2:])
    return post_pics

def get_instagram_video(post_url):
    options = Options()
    options.headless = True
    options.log.level = 'fatal'
    browser = webdriver.Firefox(options=options)
    try:
        browser.get(post_url)
        wait = WebDriverWait(browser, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        html_doc = browser.page_source
        soup = BeautifulSoup(html_doc, 'html.parser')
        video = soup.find('video')
        return video['src']
    except Exception:
        return None
    finally:
        browser.quit()

def split2albums(items):
    return [items[i:i + 10] for i in range(0, len(items), 10)]
