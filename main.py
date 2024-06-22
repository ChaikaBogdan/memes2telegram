import logging
import os
import json
import html
import sys
import traceback
import asyncio
import httpx
from telegram import Update, InputMediaPhoto
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
from converter import convert2MP4, convert2JPG
from scraper import (
    is_big,
    is_link,
    is_joyreactor_post,
    is_instagram_post,
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
    is_downloadable,
    is_downloadable_image,
    is_downloadable_video,
    get_instagram_video,
)
from randomizer import sword, fortune

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


JOY_PUBLIC_DOMAINS = {
    "joyreactor.cc",
}
CACHE_CONFIG = dict(maxsize=100, ttl=43200)
SEND_CONFIG = dict(read_timeout=30, write_timeout=30, pool_timeout=30)

_cached_sword = cached(cache=TTLCache(**CACHE_CONFIG))(sword)
_cached_fortune = cached(cache=TTLCache(**CACHE_CONFIG))(fortune)


def get_bot_token(env_key: str = "BOT_TOKEN") -> str:
    val = os.getenv(env_key)
    if val is None:
        logger.error("%s not provided by environment", env_key)
        sys.exit(os.EX_CONFIG)
    return val


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = None
    update_data_str = ""
    if not isinstance(update, Update):
        job = getattr(context, "job", None)
        if job:
            chat_id = job.chat_id
            if job.data:
                update_data_str = html.escape(
                    json.dumps(job.data, indent=2, ensure_ascii=False)
                )
    else:
        chat_id = update.effective_chat.id
        update_data_str = html.escape(
            json.dumps(update.to_dict(), indent=2, ensure_ascii=False)
        )
    logger.error("Exception while handling bot task:", exc_info=context.error)
    if not chat_id:
        logger.error("No chat id to send exception to")
        return
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_str = html.escape("".join(tb_list))
    message_lines = [
        "An exception was raised while handling bot task",
    ]
    if update_data_str:
        message_lines.append(f"<pre>update = {update_data_str[:1900]}</pre>")
    message_lines.append(f"<pre>{tb_str[:1900]}</pre>")
    message = "\n\n".join(message_lines).rstrip("\n")
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
    )


class ProcessException(Exception):
    pass


async def check_link(link: str) -> tuple[str, dict]:
    if not link:
        return "Empty message!", {}
    if not is_link(link):
        return "Not a link!", {}
    if is_tiktok_post(link):
        return "TikTok videos are not yet supported!", {}
    if is_joyreactor_post(link):
        return None, {}
    if is_instagram_post(link):
        return None, {}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        headers = await get_headers(client, link)
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
    if is_file_name:
        original = data
    else:
        original = await download_file(data)
    if not original:
        raise ProcessException(f"Can't download video from {data}")
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


async def image2photo(client, image_link, caption="", force_sending_link=False):
    media = image_link
    if not validators.url(image_link):
        image_link = "https://" + str(image_link)
        media = image_link
    if not force_sending_link:
        try:
            media = await download_image(client, image_link)
        except Exception:
            logger.exception("Can't convert image to photo from %s", image_link)
    return InputMediaPhoto(media=media, caption=caption)


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


async def _send_send_media_group(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    delay = job.data["delay"]
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
    media = await images2album(batch, caption)
    await context.bot.send_media_group(
        media=media,
        **send_kwargs,
    )
    batch_index = batch_number
    if batch_index < batches_count:
        context.job_queue.run_once(
            _send_send_media_group,
            delay,
            chat_id=chat_id,
            data=dict(link=link, delay=delay, batches=batches, batch_index=batch_index),
        )


async def send_post_images_as_album(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    album_size = job.data["album_size"]
    images_links = await get_post_pics(link)
    if not images_links:
        await context.bot.send_message(
            chat_id=chat_id, text=f"No pictures inside the {link} post!"
        )
        return
    images_count = len(images_links)
    batches = [
        images_links[i : i + album_size] for i in range(0, images_count, album_size)
    ]
    context.job_queue.run_once(
        _send_send_media_group,
        1,
        chat_id=chat_id,
        data=dict(link=link, delay=6, batches=batches, batch_index=0),
    )


async def send_instagram_video(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    reel_filename = await get_instagram_video(link)
    if not reel_filename:
        raise ProcessException(f"Restricted or not reel {link}")

    file_size_megabytes = os.path.getsize(reel_filename) / (1024 * 1024)
    if file_size_megabytes > 200:
        raise ProcessException(
            f"The reel size is {file_size_megabytes:.2f} MB, which probably won't fit into 50 MB upload limit."
        )
    context.job_queue.run_once(
        send_converted_video,
        1,
        chat_id=chat_id,
        data=dict(data=reel_filename, is_file_name=True),
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
            jobs.run_once(
                send_post_images_as_album,
                1,
                chat_id=chat_id,
                data=dict(link=link, album_size=10),
            )
        elif is_instagram_post(link):
            jobs.run_once(
                send_instagram_video, 1, chat_id=chat_id, data=dict(link=link)
            )
        elif is_downloadable_image(headers):
            jobs.run_once(
                send_converted_image, 1, chat_id=chat_id, data=dict(link=link)
            )
        elif is_downloadable_video(headers):
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
    application.add_handler(sword_handler)
    application.add_handler(fortune_handler)
    application.add_handler(converter_handler)
    application.add_error_handler(error_handler)
    application.run_polling(
        poll_interval=5,
        bootstrap_retries=3,
        drop_pending_updates=True,
    )
