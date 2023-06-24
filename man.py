import os
import random
import telegram
import logging
from flask import Flask, request
from telegram import Bot, Update, ChatAction, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_markdown
import psycopg2
from config import *

server = Flask(__name__)
db_connection = psycopg2.connect(DB_URI)
db_object = db_connection.cursor()


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

# Configure logging
logging.basicConfig(filename='logs.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Start command handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Привет, я твой любимый бот! \nС помощью /help ты можешь ознакомиться с.списком доступных команд.")

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

# Create the necessary tables in the database if they don't exist
db_connection.commit()

class BotDatabase:
    def __init__(self, filename):
        self.conn = psycopg2.connect(DB_URI)

        self._add_users_table()
        self._add_chats_table()
        
    def add_user(self, user_id, username):
        with self.conn.cursor() as cursor:
            query = '''INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) do UPDATE SET username = %s'''
            cursor.execute(query, (user_id, username, username))
            self.conn.commit()

    def get_all_users(self):
        with self.conn.cursor() as cursor:
            query = '''SELECT user_id, username FROM users'''
            cursor.execute(query)
            return cursor.fetchall()

    def get_users_from_chat(self, group_id):
        with self.conn.cursor() as cursor:
            query = '''SELECT c.user_id, u.username 
                        FROM chats c 
                        JOIN users u on c.user_id = u.user_id 
                        WHERE c.chat_id=%s'''
            cursor.execute(query, (group_id,))
            return cursor.fetchall()

    def add_user_to_chat(self, chat_id, user_id):
        with self.conn.cursor() as cursor:
            query = '''INSERT INTO chats (chat_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING'''
            cursor.execute(query, (chat_id, user_id))
            self.conn.commit()

    def delete_user_from_chat(self, chat_id, user_id):
        with self.conn.cursor() as cursor:
            query = '''DELETE from chats WHERE chat_id = %s AND user_id = %s'''
            cursor.execute(query, (chat_id, user_id))
            self.conn.commit()

    def update_user_username(self, user_id, new_username):
        with self.conn.cursor() as cursor:
            sql_update_query = '''UPDATE users SET username = %s WHERE user_id = %s'''
            cursor.execute(sql_update_query, (new_username, user_id))
            self.conn.commit()

    def count_users(self):
        with self.conn.cursor() as cursor:
            query = '''SELECT COUNT(user_id) FROM users'''
            cursor.execute(query)
            return cursor.fetchone()

    def count_chats(self):
        with self.conn.cursor() as cursor:
            query = '''SELECT COUNT(DISTINCT chat_id) FROM chats'''
            cursor.execute(query)
            return cursor.fetchone()

    def count_groups(self):
        with self.conn.cursor() as cursor:
            query = '''SELECT COUNT(DISTINCT chat_id) FROM chats WHERE chat_id <> user_id'''
            cursor.execute(query)
            return cursor.fetchone()

    def _add_users_table(self):
        with self.conn.cursor() as cursor:
            query = '''CREATE TABLE IF NOT EXISTS 
                                        users (user_id BIGINT, username VARCHAR(64), PRIMARY KEY (user_id))'''
            cursor.execute(query)
            self.conn.commit()

    def _add_chats_table(self):
        with self.conn.cursor() as cursor:
            query = '''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id BIGINT, 
                    user_id BIGINT, 
                    PRIMARY KEY (chat_id, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE )'''
            cursor.execute(query)
            self.conn.commit()

    def close(self):
        self.conn.close()


# Close the database connection
db_connection.close()
if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    updater.stop()
