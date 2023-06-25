import os
import random
import telegram
import logging
from flask import Flask, request
from telegram import Bot, Update, ChatAction, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_markdown
import psycopg2
from psycopg2.extras import execute_values
from config import *
from botdatabase import BotDatabase
server = Flask(__name__)


updater = Updater(BOT_TOKEN)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Gifs directory path
GIFS_DIR = 'gifs'

# List of names
names = ['Guldana Kurmangali', 'Zarina Mustafina', 'Dina Kalibekova', 'Tamiris Imankulova', 'Askan Kurmyshev', 'Ali Tussupov',
         'Daulet Kanatuly', 'Aktan Seraliev', 'Saltanat Kamalova', 'Alima Sairan', 'Aray Serikkali', 'Sabina Khabdullina',
         'Zhaina Toleutay', 'Sagiyeva Dilnaz', 'Arulan Bauyrzhanov', 'Malika Sissenova', 'Madina Maulitova',
         'Kamila Moldabayeva', 'Assimgul Zhetpisbayeva', 'Zhangir Ospanov', 'Nurdaulet Assylgali', 'Aruzhan Kaimbekova',
         'Aida Orazkhunova', 'Aliya Rashitova', 'Dina Khamitova', 'Alua Valitova', 'Alibek Aitzhan', 'Shakhanazar Shayakhmet',
         'Anelya Amanzholova', 'Merey Marat', 'Nazerke Nsanbayeva', 'Dilnaz Kanafina', 'Madi Suleimenov', 'Dilnaz Akylzhan',
         'Arailym Yeskendirova', 'Nargiz Zhakupova', 'Aldiyar Shakayev', 'Altynay Yelenbayeva', 'Darkhan Mustafin',
         'Tolganay Aityn', 'Arafat Matkarimov', 'Aiida Karsybay', 'Yesbossyn Aiym', 'Islam Shintemirov',
         'Alina Sagymbayeva', 'Kamila Balkibekova', 'Aknyssan Itegul', 'Aruzhan Yendybayeva', 'Luiza Aitkozha',
         'Nurzhan Kadyrkhan', 'Yerkezhan Ryskanova', 'Aibek Alimkhan', 'Nagyn Seitkhan', 'Nursultan Seitmyrza',
         'Aida Toxambayeva', 'Rozalina Alkeyeva', 'Altair Abdrakhman', 'Aruzhan Adebiyetova', 'Assem Khazadiyaz',
         'Aibat Mukametkali', 'Kaisar Daukenov']
# Configure logging
logging.basicConfig(filename='logs.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Start command handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Привет, я твой любимый бот! \nС помощью /help ты можешь ознакомиться с.списком доступных команд.")

def compatibility(update, context):
    args = context.args
    if len(args) > 0:
        name = ' '.join(args)
        random_num = random.randint(1, 100)
        message = f"Ваша совместимость с <a href='tg://user?id={update.effective_user.id}'>{name}</a>: {random_num}%"

        if random_num > 80:
            message += "\nТебе пора звать его на брекфаст!"
        elif random_num > 50:
            message += "\nУ тебя есть шансы."
        elif random_num > 30:
            message += "\nНе отчаивайся, дорогуша."

        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Тег написан неправильно, пример /comp @username.")


# In command handler
def in_command(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    logging.info('/in called, chat_id=%s user_id=%s', chat_id, user.id)
    user_name = user.username or user.first_name or 'anonymous'
    BotDatabase.add_user(user.id, user_name)
    BotDatabase.add_user_to_chat(chat_id, user.id)
    message = f'Thanks for opting in {user_name}'
    context.bot.send_message(chat_id=chat_id, text=message)
    

# Help command handler
def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Я могу выполнить следующие команды:\n\n"
                                  "/start - Description\n"
                                  "/crush - who is your heartthrob\n"
                                  "/in - receive mentions\n"
                                  "/all - mention all members\n"
                                  "/daymood - explore your daily mood\n"
                                  "/help - get the command list\n"
                                  "/comp @name - Check your compatibility")

# Random name command handler
def random_name(update, context):
    name = random.choice(names)
    context.bot.send_message(chat_id=update.effective_chat.id, text=name)

# Random GIF command handler
def random_gif(update, context):
    gif_files = os.listdir(GIFS_DIR)
    gif_file = random.choice(gif_files)
    gif_path = os.path.join(GIFS_DIR, gif_file)
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    context.bot.send_animation(chat_id=update.effective_chat.id, animation=open(gif_path, 'rb'))



# Out command handler
def out_command(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_name = user.username or user.first_name or 'anonymous'
    BotDatabase.delete_user_from_chat(chat_id, user.id)
    message = f'You\'ve been opted out {user_name}'
    context.bot.send_message(chat_id=chat_id, text=message)

# All command handler
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

from telegram import ChatPermissions

def all_command(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Check if the user is an admin in the group
    if context.bot.get_chat_member(chat_id, user.id).status not in ['creator', 'administrator']:
        context.bot.send_message(chat_id=chat_id, text="Only group admins can use this command.")
        return

    user_list = BotDatabase.get_users_from_chat(chat_id)
    logging.info('/all called, chat_id=%s user_count=%s', chat_id, len(user_list))
    if not user_list:
        message = 'There are no users. To opt in, type /in command.'
        context.bot.send_message(chat_id=chat_id, text=message)
    else:
        mentions = [mention_markdown(user_id, user_name, version=2) for user_id, user_name in user_list]
        for chunk in chunks(mentions, 4):
            message = ' '.join(chunk)
            context.bot.send_message(
                chat_id=chat_id, text=message, parse_mode=telegram.ParseMode.MARKDOWN_V2)

# Unknown command handler
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Извините, я не понимаю эту команду.")

# Add command handlers to the updater
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('crush', random_name))
updater.dispatcher.add_handler(CommandHandler('daymood', random_gif))
updater.dispatcher.add_handler(CommandHandler('in',in_command))
updater.dispatcher.add_handler(CommandHandler('out',out_command))
updater.dispatcher.add_handler(CommandHandler('all',all_command ))
comp_handler = CommandHandler('comp', compatibility, pass_args=True)
updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))

# Run the bot
updater.start_polling()


if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    updater.stop()