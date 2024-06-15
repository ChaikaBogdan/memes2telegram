import logging
import os
import subprocess
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
from converter import convert_movie_to_mp4, convert2JPG
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
        logging.error("%s not provided by environment", key)
        sys.exit(os.EX_CONFIG)
    return val


get_bot_token = partial(_get_env_val, "BOT_TOKEN")
get_dopamine_id = partial(_get_env_val, "DOPAMINE_ID")


def check_link(link):
    if not link:
        return "Empty message!"
    if not is_link(link):
        return "Not a link!"
    if is_instagram_post(link):
        return None
    elif is_joyreactor_post(link):
        return None
    elif is_tiktok_post(link):
        return None
    elif is_image(link):
        return None
    else:
        headers = get_headers(link)
        if not is_downloadable_video(headers):
            return "Cannot download video!"
        if is_big(headers):
            return "Its so fucking big!"
    return None


async def send_converted_video(context, update, link, file=False):
    original = None
    converted = None

    try:
        if not file:
            original = download_file(link) or None
        else:
            original = link
        if not original:
            raise Exception("Cannot download video")
        converted = convert_movie_to_mp4(original) or None
        if not converted:
            raise Exception("Cannot convert video")
        with open(converted, "rb") as video:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video,
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                pool_timeout=120,
                disable_notification=True,
            )
    except Exception as error:
        logging.error(error)
    finally:
        remove_file(original)
        remove_file(converted)


async def send_converted_image(context, update, link):
    original = None
    converted = None
    chat_id = update.effective_chat.id
    try:
        original = download_file(link)
        if original is None:
            raise ValueError("Cannot download image")

        converted = convert2JPG(original)
        if converted is None:
            raise ValueError("Cannot convert the image")

        with open(converted, "rb") as media:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=media,
                disable_notification=True,
                **SEND_CONFIG,
            )
    except Exception:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong. Please try again later.",
        )
    finally:
        if original:
            remove_file(original)
        if converted:
            remove_file(converted)


def image2photo(image_link, caption="", force_sending_link=False):
    if not validators.url(image_link):
        image_link = "https://" + str(image_link)
    if force_sending_link:
        return InputMediaPhoto(media=image_link, caption=caption)
    try:
        image_data = download_image(image_link)
        return InputMediaPhoto(media=image_data, caption=caption)
    except Exception:
        # If downloading fails, return the image data directly
        return InputMediaPhoto(media=image_link, caption=caption)


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


async def send_post_images_as_album(
    context, update, link, album_size=10, send_kwargs=None
):
    chat_id = update.effective_chat.id
    if send_kwargs is None:
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
    for batch_number, batch in enumerate(batches, 1):
        caption = f"{link} ({batch_number}/{batches_count})"
        await context.bot.send_media_group(
            media=images2album(batch, caption),
            **send_kwargs,
        )


def _check_link(text: str) -> str:
    link = link_to_bot(text)
    error = check_link(link)
    if error:
        return None
    return link


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    text = message.text
    if not is_bot_message(text):
        if not is_private_message(message):
            return
    chat_id = update.effective_chat.id
    try:
        link = _check_link(text)
        if not link:
            return
        if is_joyreactor_post(link):
            await send_post_images_as_album(context, update, link)
        elif is_instagram_post(link):
            reel_file = get_instagram_video(link)
            if not reel_file:
                raise Exception("Restricted or not reel")
            await send_converted_video(context, update, reel_file, True)
        elif is_tiktok_post(link):
            raise Exception("TikTok videos are not yet supported!")
        elif is_webp_image(link):
            await send_converted_image(context, update, link)
        else:
            await send_converted_video(context, update, link)
    except Exception as error:
        await context.bot.send_message(
            chat_id=chat_id, text=str(error) + "\n" + link
        )
    finally:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.message.message_id,
            **SEND_CONFIG,
        )


async def sword_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text=_cached_sword(update.effective_user.name),
        **SEND_CONFIG,
    )
    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.message.message_id,
        **SEND_CONFIG,
    )


async def fortune_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text=_cached_fortune(update.effective_user.name),
        parse_mode=ParseMode.HTML,
       **SEND_CONFIG,
    )
    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.message.message_id,
        **SEND_CONFIG,
    )


if __name__ == "__main__":
    load_dotenv()
    subprocess.run(["redis-cli", "FLUSHDB"])
    application = ApplicationBuilder().token(get_bot_token()).build()
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
        timeout=30,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30,
        drop_pending_updates=True,
    )
