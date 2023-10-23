import logging
import os
import sys
from telegram import Update, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

from converter import convert2mp4
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
    is_downloadable_video,
    get_instagram_video,
)
from randomizer import sword, fortune
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def install_firefox_driver():
    try:
        driver_path = GeckoDriverManager().install()
        return driver_path
    except Exception:
        raise Exception("Cannot download latest Firefox driver")


def get_firefox_browser(driver_path):
    try:
        options = Options()
        options.add_argument("-headless")
        browser = webdriver.Firefox(
            service=FirefoxService(driver_path), options=options
        )
        return browser
    except Exception:
        raise Exception("Cannot create browser using driver: " + driver_path)


def get_bot_token():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        logging.error("BOT_TOKEN not provided by environment")
        sys.exit(0)
    return bot_token


def get_dopamine_id():
    dopamine_id = os.environ.get("DOPAMINE_ID")
    if not dopamine_id:
        logging.error("DOPAMINE_ID not provided by environment")
        sys.exit(0)
    return dopamine_id


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="¯\\_(ツ)_/¯")


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
    else:
        headers = get_headers(link)
        if not is_downloadable_video(headers):
            return "Cannot download!"
        if is_big(headers):
            return "Its so fucking big!"
    return None


async def send_converted_video(context, update, link):
    original = None
    converted = None
    try:
        original = download_file(link) or None
        if not original:
            raise Exception("Cannot download")
        converted = await convert2mp4(original) or None
        if not converted:
            raise Exception("Cannot convert")
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
        return error
    finally:
        remove_file(original)
        remove_file(converted)


def image2photo(image_link, caption=""):
    return InputMediaPhoto(media=image_link, caption=caption)


def images2album(images_links, link):
    if images_links:
        photos = [image2photo(images_links[0], caption="Full: " + link)]
        photos.extend(image2photo(image_link) for image_link in images_links[1:])
        return photos[:9]
    return []


async def send_post_images_as_album(context, update, link):
    images_links = get_post_pics(link)
    if images_links:
        await context.bot.send_media_group(
            chat_id=update.effective_chat.id,
            media=images2album(images_links, link),
            read_timeout=20,
            write_timeout=20,
            pool_timeout=20,
            disable_notification=True,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="No pictures inside the post!"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=link)


def _check_link(text: str) -> str:
    link = link_to_bot(text)
    error = check_link(link)
    if error:
        logging.error(error)
        raise Exception(error)
    return link


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    text = message.text
    if not is_bot_message(text):
        if not is_private_message(message):
            return
    try:
        link = _check_link(text)
        if is_joyreactor_post(link):
            await send_post_images_as_album(context, update, link)
        elif is_instagram_post(link):
            video_link = get_instagram_video(link, get_firefox_browser(driver))
            if not video_link:
                logging.error("Restricted or no videos inside the post")
                raise Exception("Restricted or no videos inside the post")
            await send_converted_video(context, update, video_link)
        elif is_tiktok_post(link):
            raise Exception("TikTok videos are not yet supported!")
            # video_link = get_tiktok_video(link, get_firefox_browser(driver))
            # if not video_link:
            #     logging.error("Restricted or no videos inside the post")
            #     raise Exception("Restricted or no videos inside the post")
            # await send_converted_video(context, update, video_link)
        else:
            await send_converted_video(context, update, link)
    except Exception as error:
        logging.error(error)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=str(error) + "\n" + link
        )
    finally:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            read_timeout=20,
            write_timeout=20,
            pool_timeout=20,
        )


async def sword_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=sword(update.effective_user.name),
        read_timeout=20,
        write_timeout=20,
        pool_timeout=20,
    )
    await context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
        read_timeout=20,
        write_timeout=20,
        pool_timeout=20,
    )


async def fortune_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=fortune(update.effective_user.name),
        read_timeout=20,
        write_timeout=20,
        pool_timeout=20,
    )
    await context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
        read_timeout=20,
        write_timeout=20,
        pool_timeout=20,
    )


if __name__ == "__main__":
    load_dotenv()
    driver = install_firefox_driver()
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
    logging.info("Bot start polling")
