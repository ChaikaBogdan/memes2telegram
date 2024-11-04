import html
from io import BytesIO
import logging
import math
import os
import json
import sys
import traceback
import subprocess
import asyncio
import httpx
from telegram import Update, InputMediaPhoto, InputMediaDocument
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import validators
from dotenv import load_dotenv
from cachetools import cached, TTLCache
from converter import convert2MP4, convert2JPG, convert2LOG
from scraper import (
    _get_referer_headers,
    is_big,
    is_link,
    is_joyreactor_post,
    is_instagram_post,
    is_instagram_album,
    is_instagram_reel,
    is_youtube_video,
    is_tiktok_post,
    is_bot_message,
    is_private_message,
    link_to_bot,
    get_headers,
    get_post_pics,
    remove_file,
    download_file,
    download_image,
    get_content_type,
    get_filename_from_url,
    is_downloadable,
    is_downloadable_image,
    is_downloadable_video,
    is_generic_video,
    is_generic_image,
    get_instagram_video,
    get_youtube_video,
    get_instagram_pics,
)
from randomizer import sword, fortune
from PIL import Image

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


JOY_PUBLIC_DOMAINS = {
    "joyreactor.cc",
}
NSFW_FLAGS = {
    "porn",
    "r34",
    "yiff",
    "furry",
    "spoiler",
    "ero",
}
CACHE_CONFIG = dict(maxsize=100, ttl=43200)
SEND_CONFIG = dict(read_timeout=30, write_timeout=30, pool_timeout=30)

_cached_sword = cached(cache=TTLCache(**CACHE_CONFIG))(sword)
_cached_fortune = cached(cache=TTLCache(**CACHE_CONFIG))(fortune)

POST_PROCESSING_JOBS = {"_send_media_group", "send_post_images_as_album"}


def get_bot_token(env_key: str = "BOT_TOKEN") -> str:
    val = os.getenv(env_key)
    if val is None:
        logger.error("%s not provided by environment", env_key)
        sys.exit(os.EX_CONFIG)
    return val


async def _mark(key: str, coro) -> tuple:
    return key, await coro


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = None
    message_data = None
    error = context.error
    logger.error("Exception while handling bot task:", exc_info=error)
    if not isinstance(update, Update):
        job = getattr(context, "job", None)
        if job:
            chat_id = job.chat_id
            if job.data:
                message_data = job.data
    else:
        chat_id = update.effective_chat.id
        message_data = update.to_dict()
    if not chat_id:
        logger.error("No chat id to send exception to")
        return
    caption = "An exception was raised while handling bot task"
    exception_data = {}
    if message_data:
        exception_data["message.json.txt"] = json.dumps(
            message_data, indent=2, ensure_ascii=False
        )
    tb_list = traceback.format_exception(None, error, error.__traceback__)
    if tb_list:
        tb_str = "".join(tb_list)
        exception_data["traceback.txt"] = tb_str
    if not exception_data:
        logger.warning("No exception data")
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
        )
        return
    exception_logs = {
        log_name: (filename, open(filename, "rb"))
        for log_name, filename in await asyncio.gather(
            *[
                _mark(key, convert2LOG(content))
                for key, content in exception_data.items()
            ]
        )
    }
    if len(exception_logs) > 1:
        logs = list(exception_logs.items())
        last_log = logs.pop()
        media = [
            InputMediaDocument(file_handle, filename=log_name)
            for log_name, (_, file_handle) in logs
        ]
        log_name, (_, file_handle) = last_log
        media.append(
            InputMediaDocument(file_handle, filename=log_name, caption=caption)
        )
        await context.bot.send_media_group(
            chat_id,
            media,
        )
        for filename, file_handle in exception_logs.values():
            file_handle.close()
            remove_file(filename)
    else:
        log_name, (filename, file_handle) = exception_logs.popitem()
        await context.bot.send_document(
            chat_id,
            caption=caption,
            document=file_handle,
            filename=log_name,
        )
        file_handle.close()
        remove_file(filename)


class ProcessException(Exception):
    pass


async def check_link(link: str) -> tuple[str, dict]:
    if not link:
        return "Empty message!", {}
    if not is_link(link):
        return "Not a link!", {}
    if is_tiktok_post(link):
        return None, {}
    if is_joyreactor_post(link):
        return None, {}
    if is_instagram_post(link):
        return None, {}
    if is_youtube_video(link):
        return None, {}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = await get_headers(client, link)
        except Exception:
            logger.exception(
                "Can't get headers for %s - assuming it's valid link", link
            )
            return None, {}
    if not is_downloadable(headers):
        content_type = get_content_type(headers)
        return f"Can't download {link} - {content_type} unknown!", headers
    if is_big(headers):
        return f"Can't download this {link} - file is too big!", headers
    return None, headers


async def send_converted_video(context: ContextTypes.DEFAULT_TYPE):
    original = None
    converted = None
    job = context.job
    chat_id = job.chat_id
    data = job.data["data"]
    is_file_name = job.data["is_file_name"]
    caption = job.data.get("caption")
    if is_file_name:
        original = data
    else:
        original = await download_file(data)
    is_nsfw = any(flag in data for flag in NSFW_FLAGS)
    try:
        converted = await convert2MP4(original)
        file_size_megabytes = os.path.getsize(converted) / (1024 * 1024)
        if file_size_megabytes > 50:
            raise ProcessException(
                f"The mp4 size is {file_size_megabytes:.2f} MB, which exceeds the 50 MB video upload limit."
            )
        with open(converted, "rb") as video:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video,
                supports_streaming=True,
                read_timeout=180,
                write_timeout=180,
                pool_timeout=180,
                disable_notification=True,
                has_spoiler=is_nsfw,
                caption=caption,
            )
    except Exception:
        raise
    finally:
        if original:
            remove_file(original)
        if converted:
            remove_file(converted)


async def send_converted_image(context: ContextTypes.DEFAULT_TYPE):
    original = None
    converted = None
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    try:
        original = await download_file(link)
        if not original:
            raise ProcessException(f"Can't download image from {link}")
        converted = await convert2JPG(original)
        if not converted:
            raise ProcessException(f"Can't convert the image from {link}")
        with open(converted, "rb") as media:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=media,
                disable_notification=True,
                **SEND_CONFIG,
            )
    except Exception:
        raise
    finally:
        if original:
            remove_file(original)
        if converted:
            remove_file(converted)


async def get_image_dimensions(client, image_url, timeout=10):
    request_headers = _get_referer_headers(image_url)
    async with client.stream(
        "GET", image_url, headers=request_headers, timeout=timeout
    ) as response:
        response.raise_for_status()
        content = await response.aread()
        with BytesIO(content) as f:
            image = Image.open(f)
            width, height = image.size
            return width, height


async def image2photo(client, image_link, caption="", force_sending_link=False):
    media = image_link
    is_nsfw = any(flag in image_link for flag in NSFW_FLAGS)

    if not validators.url(image_link):
        media = "https://" + str(image_link)
    width, height = await get_image_dimensions(client, media)
    is_longpost = (height * width) >= (1920 * 1080)
    if not force_sending_link or is_longpost:
        try:
            media = await download_image(client, media)
        except Exception:
            logger.exception("Can't convert image to photo from %s", media)
    if is_longpost:
        return InputMediaDocument(
            media=media, filename=get_filename_from_url(image_link), caption=caption
        )
    return InputMediaPhoto(media=media, caption=caption, has_spoiler=is_nsfw)


async def images2album(images_links, link):
    is_public_domain = any(domain in link for domain in JOY_PUBLIC_DOMAINS)
    if images_links:
        first_image_link, rest_images_links = images_links[0], images_links[1:]
        async with httpx.AsyncClient(follow_redirects=True) as client:
            first_photo = await image2photo(
                client,
                first_image_link,
                caption=link,
                force_sending_link=is_public_domain,
            )
            photos = [first_photo]
            rest_photos = await asyncio.gather(
                *[
                    image2photo(client, image_link, None, is_public_domain)
                    for image_link in rest_images_links
                ]
            )
            photos.extend(rest_photos)
        return photos
    return []


async def _send_media_group(context: ContextTypes.DEFAULT_TYPE, delay: int = 6):
    job = context.job
    chat_id = job.chat_id
    batch_index = job.data["batch_index"]
    link = job.data["link"]
    batches = job.data["batches"]
    batches_count = len(batches)
    batch_number = batch_index + 1
    if batches_count == 1:
        caption = f"{link}"
    else:
        caption = f"{link} ({batch_number}/{batches_count})"
    send_kwargs = dict(
        disable_notification=True,
        chat_id=chat_id,
        **SEND_CONFIG,
    )
    batch = batches[batch_index]
    media_items = await images2album(batch, caption)
    if not media_items:
        return
    current_media_type = type(media_items[0])
    media_type_batches = [[]]
    current_batch_index = 0
    for media_item in media_items:
        if not isinstance(media_item, current_media_type):
            current_batch_index += 1
            media_type_batches.append([])
            current_media_type = type(media_item)
        media_type_batches[current_batch_index].append(media_item)
    for media in media_type_batches:
        await context.bot.send_media_group(
            media=media,
            **send_kwargs,
        )
        await asyncio.sleep(delay)
    batch_index = batch_number
    if batch_index < batches_count:
        context.job_queue.run_once(
            _send_media_group,
            delay,
            chat_id=chat_id,
            data=dict(link=link, batches=batches, batch_index=batch_index),
        )


def _balance_batches(batches: list[list]) -> None:
    penultimate_batch = batches[-2]
    last_batch = batches[-1]
    last_batch_size = len(last_batch)
    penultimate_batch_size = len(penultimate_batch)
    if last_batch_size != penultimate_batch_size:
        total_size = last_batch_size + penultimate_batch_size
        start = math.ceil(total_size / 2)
        new_elems = penultimate_batch[start:penultimate_batch_size]
        for new_elem in reversed(new_elems):
            last_batch.insert(0, new_elem)
            penultimate_batch.pop()


async def send_post_images_as_album(
    context: ContextTypes.DEFAULT_TYPE, album_size: int = 10
):
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    images_links = await get_post_pics(link)
    if not images_links:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"No pictures inside the {link} post or login required!",
        )
        return
    images_count = len(images_links)
    batches = [
        images_links[i : i + album_size] for i in range(0, images_count, album_size)
    ]
    if len(batches) > 1:
        _balance_batches(batches)
    context.job_queue.run_once(
        _send_media_group,
        1,
        chat_id=chat_id,
        data=dict(link=link, batches=batches, batch_index=0),
    )


async def send_instagram_video(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    reel_filename = await get_instagram_video(link)
    if not reel_filename:
        raise ProcessException(f"Restricted or not reel {link}")
    file_size_megabytes = os.path.getsize(reel_filename) / (1024 * 1024)
    if file_size_megabytes > 50:
        raise ProcessException(
            f"The reel {link} size is {file_size_megabytes:.2f} MB, which probably won't fit into 50 MB upload limit."
        )
    context.job_queue.run_once(
        send_converted_video,
        1,
        chat_id=chat_id,
        data=dict(data=reel_filename, is_file_name=True, caption=link),
    )


async def send_instagram_album(
    context: ContextTypes.DEFAULT_TYPE, album_size: int = 10
):
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    images_links = await get_instagram_pics(link)
    if not images_links:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"No pictures inside the {link} post or login required!",
        )
        return

    images_count = len(images_links)
    batches = [
        images_links[i : i + album_size] for i in range(0, images_count, album_size)
    ]
    if len(batches) > 1:
        _balance_batches(batches)
    context.job_queue.run_once(
        _send_media_group,
        1,
        chat_id=chat_id,
        data=dict(link=link, batches=batches, batch_index=0),
    )


async def send_youtube_video(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    video_filename = await get_youtube_video(link)
    context.job_queue.run_once(
        send_converted_video,
        1,
        chat_id=chat_id,
        data=dict(data=video_filename, is_file_name=True, caption=link),
    )


async def send_tiktok_video(context: ContextTypes.DEFAULT_TYPE):
    # YoutubeDL handle tiktok as well
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    video_filename = await get_youtube_video(link)
    context.job_queue.run_once(
        send_converted_video,
        1,
        chat_id=chat_id,
        data=dict(data=video_filename, is_file_name=True, caption=link),
    )


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    text = message.text
    if not is_bot_message(text):
        if not is_private_message(message):
            return
    link = link_to_bot(text)
    error, headers = await check_link(link)
    chat_id = update.effective_chat.id
    message_id = message.message_id
    if error:
        logger.error(error)
        await context.bot.send_message(
            chat_id=chat_id,
            text=error,
            **SEND_CONFIG,
        )
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
            **SEND_CONFIG,
        )
        return
    jobs = context.job_queue
    try:
        if is_joyreactor_post(link):
            running_jobs_count = sum(
                1 for job in jobs.jobs() if job.name in POST_PROCESSING_JOBS
            )
            jobs.run_once(
                send_post_images_as_album,
                5 * (running_jobs_count + 1),
                chat_id=chat_id,
                data=dict(link=link),
            )
        elif is_instagram_post(link):
            if is_instagram_reel(link):
                jobs.run_once(
                    send_instagram_video, 1, chat_id=chat_id, data=dict(link=link)
                )
            elif is_instagram_album:
                jobs.run_once(
                    send_instagram_album, 1, chat_id=chat_id, data=dict(link=link)
                )

        elif is_youtube_video(link):
            jobs.run_once(send_youtube_video, 1, chat_id=chat_id, data=dict(link=link))
        elif is_tiktok_post(link):
            jobs.run_once(send_tiktok_video, 1, chat_id=chat_id, data=dict(link=link))
        elif is_downloadable_image(headers) or is_generic_image(link):
            jobs.run_once(
                send_converted_image, 1, chat_id=chat_id, data=dict(link=link)
            )
        elif is_downloadable_video(headers) or is_generic_video(link):
            jobs.run_once(
                send_converted_video,
                1,
                chat_id=chat_id,
                data=dict(data=link, is_file_name=False),
            )
        else:
            error = f"No idea what to do with {link}"
            logger.error(error)
            await context.bot.send_message(
                chat_id=chat_id,
                text=error,
                **SEND_CONFIG,
            )
    except Exception:
        raise
    finally:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
            **SEND_CONFIG,
        )


async def _sword_size(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    user_name = job.data["user_name"]
    await context.bot.send_message(
        chat_id=chat_id,
        text=_cached_sword(user_name),
        **SEND_CONFIG,
    )


async def _nsfw_curtain(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    text = "NOT SAFE FOR WORK NOT SAFE FOR WORK NOT SAFE FOR WORK NOT SAFE FOR WORK"
    command = ["figlet", "-w", "30", "-c", text]
    figlet_process = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    figlet_line = figlet_process.stdout
    figlet_line = html.escape(figlet_line)
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Пригнись! Там женщина!<pre><code>{figlet_line}</code></pre>",
        parse_mode=ParseMode.HTML,
        **SEND_CONFIG,
    )


async def sword_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.name
    context.job_queue.run_once(
        _sword_size,
        1,
        chat_id=chat_id,
        data=dict(user_name=user_name),
    )
    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.message.message_id,
        **SEND_CONFIG,
    )


async def nsfw_curtain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_once(
        _nsfw_curtain,
        1,
        chat_id=chat_id,
    )
    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.message.message_id,
        **SEND_CONFIG,
    )


async def _fortune_cookie(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    user_name = job.data["user_name"]
    await context.bot.send_message(
        chat_id=chat_id,
        text=_cached_fortune(user_name),
        parse_mode=ParseMode.HTML,
        **SEND_CONFIG,
    )


async def fortune_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.name
    context.job_queue.run_once(
        _fortune_cookie,
        1,
        chat_id=chat_id,
        data=dict(user_name=user_name),
    )
    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.message.message_id,
        **SEND_CONFIG,
    )


if __name__ == "__main__":
    load_dotenv()
    application = (
        ApplicationBuilder()
        .token(get_bot_token())
        .pool_timeout(30)
        .connect_timeout(30)
        .write_timeout(30)
        .read_timeout(30)
        .build()
    )
    converter_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        process,
    )
    sword_handler = CommandHandler("sword", sword_size)
    fortune_handler = CommandHandler("fortune", fortune_cookie)
    curtain_handler = CommandHandler("nsfw", nsfw_curtain)
    application.add_handler(sword_handler)
    application.add_handler(fortune_handler)
    application.add_handler(curtain_handler)
    application.add_handler(converter_handler)
    application.add_error_handler(error_handler)
    application.run_polling(
        poll_interval=5,
        bootstrap_retries=3,
        drop_pending_updates=True,
    )
