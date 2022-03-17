#!/usr/bin/env python3

from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext
from telegram import Update
from telegram.files.inputmedia import InputMediaPhoto
import logging
from converter import *
from scraper import *
from randomizer import sword


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="¯\_(ツ)_/¯")


def get_bot_token():
    bot_token = os.environ.get('BOT_TOKEN', None)
    if not bot_token:
        logging.log(50, 'BOT_TOKEN not provided by Heroku!')
        exit(0)
    return bot_token


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


def send_converted_video(context, update, link):
    # original = in_memory_download_file(link)
    # converted = in_memory_convert2mp4(original)
    # if converted:
    #     context.bot.send_video(chat_id=update.effective_chat.id, video=converted, supports_streaming=True,
    #                            disable_notification=True)
    # else:
    #     context.bot.send_message(chat_id=update.effective_chat.id, text='Video conversion fail ლ(ಠ益ಠლ)')

    original = download_file(link)
    converted = convert2mp4(original)
    context.bot.send_video(chat_id=update.effective_chat.id, video=open(converted, 'rb'), supports_streaming=True,
                           disable_notification=True)
    remove_file(original)
    remove_file(converted)


def image2photo(image_link, caption=''):
    return InputMediaPhoto(media=image_link, caption=caption)


def send_post_images_as_album(context, update, link):
    images_links = get_post_pics(link)
    if images_links:
        photos = list(map(image2photo, images_links[1:]))
        photos.insert(0, image2photo(images_links[0], caption="Full: " + link))
        photos = [i for i in photos if i]
        album = photos[:9]
        context.bot.send_media_group(chat_id=update.effective_chat.id, media=album,
                                     disable_notification=True)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='No pictures inside the post ლ(ಠ益ಠლ)')


def process(update: Update, context: CallbackContext):
    if not update.message:
        return
    if not is_bot_message(update.message.text):
        return
    link = link_to_bot(update.message.text)
    error = check_link(link)
    if error:
        context.bot.send_message(chat_id=update.effective_chat.id, text=error)
        return
    try:
        if is_joyreactor_post(link):
            send_post_images_as_album(context, update, link)
        else:
            send_converted_video(context, update, link)
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    finally:
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)


def sword_size(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=sword(update.effective_user.name))
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    updater = Updater(token=get_bot_token(), use_context=True)
    dispatcher = updater.dispatcher
    converter_handler = MessageHandler(Filters.text & (~Filters.command), process)
    sword_handler = CommandHandler('sword', sword_size)
    dispatcher.add_handler(sword_handler)
    dispatcher.add_handler(converter_handler)
    logging.log(20, 'Bot start polling...')
    updater.start_polling()
