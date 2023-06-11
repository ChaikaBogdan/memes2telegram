#!/usr/bin/env python3

import logging
import sys
import os
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from converter import convert2mp4
from scraper import is_big, is_link, is_joyreactor_post, is_bot_message, link_to_bot, get_headers,\
    get_post_pics, remove_file, download_file, is_downloadable_video
from randomizer import sword

from dotenv import load_dotenv

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.CRITICAL)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="¯\\_(ツ)_/¯")


def get_bot_token():
    bot_token = os.environ.get('BOT_TOKEN', None)
    if not bot_token:
        logging.error('BOT_TOKEN not provided by environment!')
        sys.exit(0)
    return bot_token


def get_dopamine_id():
    dopamine_id = os.environ.get('DOPAMINE_ID', None)
    if not dopamine_id:
        logging.error('DOPAMINE_ID not provided by environment!')
        sys.exit(0)
    return dopamine_id


def check_link(link):
    if not link:
        return "Empty message (╯°□°）╯︵ ┻━┻"
    if not is_link(link):
        return "Not a link (╯°□°）╯︵ ┻━┻"
    if not is_joyreactor_post(link):
        headers = get_headers(link)
        if not is_downloadable_video(headers):
            return "Cannot download it ლ(ಠ益ಠლ)"
        if is_big(headers):
            return "It's so fucking big ( ͡° ͜ʖ ͡°)"
    return None


async def send_converted_video(context, update, link):
    try:
        original = download_file(link)
        converted = await convert2mp4(original)
        with open(converted, 'rb') as video:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video,
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                pool_timeout=120,
                disable_notification=True)
    except Exception as e:
        return
    finally:
        remove_file(original)
        remove_file(converted)
       
        


def image2photo(image_link, caption=''):
    return InputMediaPhoto(media=image_link, caption=caption)


async def send_post_images_as_album(context, update, link):
    images_links = get_post_pics(link)
    if images_links:
        photos = list(map(image2photo, images_links[1:]))
        photos.insert(0, image2photo(images_links[0], caption="Full: " + link))
        photos = [i for i in photos if i]
        album = photos[:9]
        await context.bot.send_media_group(
            chat_id=update.effective_chat.id,
            media=album,
            read_timeout=20,
            write_timeout=20,
            pool_timeout=20,
            disable_notification=True)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='No pictures inside the post ლ(ಠ益ಠლ)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=link)


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not is_bot_message(update.message.text):
        return
    link = link_to_bot(update.message.text)
    error = check_link(link)
    if error:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error)
        return
    try:
        if is_joyreactor_post(link):
            await send_post_images_as_album(context, update, link)
        else:
            await send_converted_video(context, update, link)
    except Exception as exception:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(exception))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=link)
    finally:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            read_timeout=20,
            write_timeout=20,
            pool_timeout=20,)


async def sword_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=sword(
            update.effective_user.name),
            read_timeout=20,
            write_timeout=20,
            pool_timeout=20,)
    await context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
        read_timeout=20,
        write_timeout=20,
        pool_timeout=20,)

if __name__ == "__main__":
    load_dotenv()
    application = ApplicationBuilder().token(get_bot_token()).build()
    converter_handler = MessageHandler(filters.TEXT & ~(filters.COMMAND), process)
    sword_handler = CommandHandler('sword', sword_size)
    application.add_handler(sword_handler)
    application.add_handler(converter_handler)
    application.run_polling(poll_interval=5, bootstrap_retries = 3, timeout=30, read_timeout=30, write_timeout=30,connect_timeout=30, pool_timeout=30, drop_pending_updates=True)    
    logging.info('Bot start polling...')
   