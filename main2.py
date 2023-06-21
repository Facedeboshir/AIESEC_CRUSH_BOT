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
                                  "/start - Начать диалог\n"
                                  "/help - Вывести список команд\n"
                                  "/random_name - Сгенерировать случайное имя\n"
                                  "/random_gif - Отправить случайный GIF")

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

# Unknown command handler
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Извините, я не понимаю эту команду.")

# Add command handlers to the updater
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('random_name', random_name))
updater.dispatcher.add_handler(CommandHandler('random_gif', random_gif))
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
        print('darkhan pidor')
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
    # Define the port number for the Flask server
    PORT = 5000

    server.run(debug=True, host='0.0.0.0', port=PORT)
    updater.stop()