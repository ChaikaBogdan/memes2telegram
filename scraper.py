import requests, validators, re, os
from pathlib import Path
from bs4 import BeautifulSoup
import uuid

bot_name = '@memes2telegram_bot'
bot_supported_videos = ['video/mp4', 'image/gif', 'video/webm']
bot_supported_images = ['image/jpeg', 'image/png']


def is_downloadable_video(headers):
    return headers.get('content-type').lower() in bot_supported_videos


def is_downloadable_image(headers):
    return headers.get('content-type').lower() in bot_supported_images


def get_headers(url):
    return requests.head(url, allow_redirects=True).headers


def is_big(headers):
    return int(headers.get('content-length')) > 2e+8  # 200mb


def is_dtf_video(url):
    return 'https://leonardo.osnova.io' in url


def parse_filename(url):
    return url.rsplit('/', 1)[1]


def without_extension(filename):
    pathname, extension = os.path.splitext(filename)
    return pathname.split('/')[-1]


def get_uuid(url):
    return re.search(r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}", url).group()


def link_to_bot(text):
    return text.split(bot_name)[-1].strip()


def is_bot_message(text):
    return text[0:len(bot_name)] == bot_name


def is_link(message):
    return validators.url(message)


def download_file(url):
    if is_dtf_video(url):
        filename = get_uuid(url) + '.mp4'
    else:
        _, extension = os.path.splitext(parse_filename(url))
        filename = str(uuid.uuid4()) + extension
    with open(filename, 'wb') as file:
        file.write(requests.get(url, allow_redirects=True).content)
    return filename


def in_memory_download_file(url):
    if not is_link(url):
        return None
    return requests.get(url, allow_redirects=True).content


def download_image(url):
    if not is_link(url):
        return None
    if is_downloadable_image(get_headers(url)):
        return requests.get(url, allow_redirects=True).content
    return None


def remove_file(filename):
    file = Path(filename)
    if file.is_file():
        file.unlink()


def is_joyreactor_post(url):
    return 'reactor.cc/post/' in url


def get_post_pics(post_url):
    html_doc = requests.get(post_url, allow_redirects=True).content
    soup = BeautifulSoup(html_doc, 'html.parser')
    img_tags = soup.find_all('img')
    post_pics = []
    for img in img_tags:
        src = img['src']
        if "/pics/post/" in src:
            post_pics.append(src[2:])
    return post_pics


def split2albums(items):
    return [items[i:i + 10] for i in range(0, len(items), 10)]
