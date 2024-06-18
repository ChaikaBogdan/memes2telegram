import logging
import os
import sys
from functools import partial
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
    is_webp_image,
    is_bot_message,
    is_private_message,
    link_to_bot,
    get_headers,
    get_post_pics,
    remove_file,
    download_file,
    download_image,
    is_image,
    is_downloadable_video,
    get_instagram_video,
)
from randomizer import sword, fortune

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# TODO: use https://docs.python.org/3/library/configparser.html
JOY_PUBLIC_DOMAINS = {
    "joyreactor.cc",
}
CACHE_CONFIG = dict(maxsize=100, ttl=43200)
SEND_CONFIG = dict(read_timeout=20, write_timeout=20, pool_timeout=20)

_cached_sword = cached(cache=TTLCache(**CACHE_CONFIG))(sword)
_cached_fortune = cached(cache=TTLCache(**CACHE_CONFIG))(fortune)


def _get_env_val(key: str) -> str:
    val = os.getenv(key)
    if val is None:
        logger.error("%s not provided by environment", key)
        sys.exit(os.EX_CONFIG)
    return val


get_bot_token = partial(_get_env_val, "BOT_TOKEN")


class ProcessException(Exception):
    pass


def check_link(link):
    if not link:
        return "Empty message!"
    if not is_link(link):
        return "Not a link!"
    if is_instagram_post(link):
        return None
    if is_joyreactor_post(link):
        return None
    if is_tiktok_post(link):
        return None
    if is_image(link):
        return None
    headers = get_headers(link)
    if not is_downloadable_video(headers):
        return "Cannot download video!"
    if is_big(headers):
        return "Its so fucking big!"
    return None


async def send_converted_video(context: ContextTypes.DEFAULT_TYPE):
    original = None
    converted = None
    job = context.job
    chat_id = job.chat_id
    data = job.data["data"]
    is_file_name = job.data["is_file_name"]
    try:
        if is_file_name:
            original = data
        else:
            original = download_file(data)
        if not original:
            raise ProcessException(f"Cannot download video from {data}")
        converted = convert2MP4(original)
        if not converted:
            raise ProcessException(f"Cannot convert video from {original}")
        with open(converted, "rb") as video:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video,
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                pool_timeout=120,
                disable_notification=True,
            )
    except Exception as exc:
        logger.exception("Cannot send video from %s", original)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{exc}\n{original}",
        )
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
        original = download_file(link)
        if not original:
            raise ProcessException("Cannot download image from %s", link)
        converted = convert2JPG(original)
        if not converted:
            raise ProcessException("Cannot convert the image from %s", link)

        with open(converted, "rb") as media:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=media,
                disable_notification=True,
                **SEND_CONFIG,
            )
    except Exception as exc:
        logger.exception("Cannot send image from %s", link)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{exc}\n{link}",
        )
    finally:
        if original:
            remove_file(original)
        if converted:
            remove_file(converted)


def image2photo(image_link, caption="", force_sending_link=False):
    media = image_link
    if not validators.url(image_link):
        image_link = "https://" + str(image_link)
        media = image_link
    if not force_sending_link:
        try:
            media = download_image(image_link)
        except Exception:
            logger.exception("Cannot convert image to photo from %s", image_link)
    return InputMediaPhoto(media=media, caption=caption)


def images2album(images_links, link):
    is_public_domain = any(domain in link for domain in JOY_PUBLIC_DOMAINS)
    if images_links:
        photos = [
            image2photo(
                images_links[0],
                caption=link,
                force_sending_link=is_public_domain,
            )
        ]
        photos.extend(
            image2photo(image_link, None, is_public_domain)
            for image_link in images_links[1:]
        )
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
    caption = f"{link} ({batch_number}/{batches_count})"
    send_kwargs = dict(
        disable_notification=True,
        chat_id=chat_id,
        **SEND_CONFIG,
    )
    batch = batches[batch_index]
    await context.bot.send_media_group(
        media=images2album(batch, caption),
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
    send_kwargs = dict(
        disable_notification=True,
        chat_id=chat_id,
        **SEND_CONFIG,
    )
    images_links = get_post_pics(link)
    if not images_links:
        await context.bot.send_message(
            chat_id=chat_id, text=f"No pictures inside the {link} post!"
        )
        return
    images_count = len(images_links)
    batches = [
        images_links[i : i + album_size] for i in range(0, images_count, album_size)
    ]
    batches_count = len(batches)
    if batches_count == 1:
        await context.bot.send_media_group(
            media=images2album(batches[0], link),
            **send_kwargs,
        )
        return
    context.job_queue.run_once(
        _send_send_media_group,
        1,
        chat_id=chat_id,
        data=dict(link=link, delay=6, batches=batches, batch_index=0),
    )

def _check_link(text: str) -> str:
    link = link_to_bot(text)
    error = check_link(link)
    if error:
        return None
    return link


async def send_instagram_video(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    link = job.data["link"]
    reel_filename = get_instagram_video(link)
    if not reel_filename:
        raise ProcessException(f"Restricted or not reel {link}")
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
    link = _check_link(text)
    if not link:
        return
    chat_id = update.effective_chat.id
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
        elif is_tiktok_post(link):
            raise ProcessException("TikTok videos are not yet supported!")
        elif is_webp_image(link):
            jobs.run_once(
                send_converted_image, 1, chat_id=chat_id, data=dict(link=link)
            )
        else:
            jobs.run_once(
                send_converted_video,
                1,
                chat_id=chat_id,
                data=dict(data=link, is_file_name=False),
            )
    except Exception as exc:
        logger.exception("Cannot process send message from %s", link)
        await context.bot.send_message(chat_id=chat_id, text=f"{exc}\n{link}")
    finally:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message.message_id,
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
    application.run_polling(
        poll_interval=5,
        bootstrap_retries=3,
        drop_pending_updates=True,
    )
