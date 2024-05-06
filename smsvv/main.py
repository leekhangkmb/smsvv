from keep_alive import keep_alive
keep_alive()

import telebot
import datetime
import time
import os
import subprocess
import psutil
import sqlite3
import hashlib
import requests
import datetime
import sys

bot_token = '6624218714:AAETKqRPxrtOTeq2JZalgEMiOamdXVjeENk'
bot = telebot.TeleBot(bot_token)

allowed_users = []
processes = []
ADMIN_ID = 5047988352
GROUP_ID = '-1001929593081'  # Thay YOUR_GROUP_ID bằng ID thực của nhóm

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()
cooldown_dict = {}
# Create the users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiration_time TEXT
    )
''')
connection.commit()


def TimeStamp():
  now = str(datetime.date.today())
  return now


def load_users_from_database():
  cursor.execute('SELECT user_id, expiration_time FROM users')
  rows = cursor.fetchall()
  for row in rows:
    user_id = row[0]
    expiration_time = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
    if expiration_time > datetime.datetime.now():
      allowed_users.append(user_id)


def save_user_to_database(connection, user_id, expiration_time):
  cursor = connection.cursor()
  cursor.execute(
      '''
        INSERT OR REPLACE INTO users (user_id, expiration_time)
        VALUES (?, ?)
    ''', (user_id, expiration_time.strftime('%Y-%m-%d %H:%M:%S')))
  connection.commit()


def add_user(message):
  if len(message.text.split()) == 1:
    bot.reply_to(message, 'VUI LÒNG NHẬP ID NGƯỜI DÙNG ')
    return

  user_id = int(message.text.split()[1])
  allowed_users.append(user_id)
  expiration_time = datetime.datetime.now() + datetime.timedelta(days=30)
  connection = sqlite3.connect('user_data.db')
  save_user_to_database(connection, user_id, expiration_time)
  connection.close()

  bot.reply_to(
      message,
      f'💎NGƯỜI DÙNG CÓ ID {user_id} ĐÃ ĐƯỢC THÊM VÀO DANH SÁCH ĐƯỢC PHÉP SỬ DỤNG LỆNH /spam.💎'
  )


load_users_from_database()


import re
import os
import subprocess

@bot.message_handler(commands=['spam'])
def attack_command(message):
    user_id = message.from_user.id

    if len(message.text.split()) != 3:
        bot.reply_to(message, 'Sử dụng lệnh theo định dạng: /spam {số điện thoại} {số lần}')
        return

    phone_number = message.text.split()[1]
    lap = message.text.split()[2]

    if not re.search("^(0?)(3[2-9]|5[6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])[0-9]{7}$", phone_number):
        bot.reply_to(message, 'SỐ ĐIỆN THOẠI KHÔNG HỢP LỆ !')
        return

    blocked_numbers = ['113', '114', '115', '198', '911', '0376349783']
    if phone_number in blocked_numbers:
        bot.reply_to(message, 'Bạn không được spam số này.')
        return

    cooldown_dict[user_id] = time.time()

    username = message.from_user.username

    bot.reply_to(
        message,
        f'💎Spam Thành Công!!!💎\n┏━━━━━━━━━━━━━━┓\n┣➤ Attack By: @{username} \n┣➤ Số Tấn Công: {phone_number} \n┣➤ Group: t.me/+1CsguhMAhl8yMGRl \n┗━━━━━━━━━━━━━━➤'
    )

    # Chạy file newsms.py sử dụng subprocess
    file_path = os.path.join(os.getcwd(), "newsms.py")
    process = subprocess.Popen(["python", file_path, phone_number, lap])
    processes.append(process)

    # Gửi thông báo vào nhóm
    bot.send_message(
        GROUP_ID,
        f'🔰👮Người dùng @{message.from_user.username} đã thực hiện lệnh /spam \n🔰Số điện thoại {phone_number} \n❌Lặp lại {lap} lần.'
    )



@bot.message_handler(commands=['how'])
def how_to(message):
  how_to_text = '''
Hướng dẫn sử dụng:
- Sử dụng lệnh /spam {số điện thoại} {số lần} để gửi tin nhắn SMS.
'''
  bot.reply_to(message, how_to_text)


@bot.message_handler(commands=['help'])
def help(message):
  help_text = '''
Danh sách lệnh:
- /spam {số điện thoại} {số lần} : Gửi tin nhắn SMS.
- /stop : Tạm dừng spam
- /how : Hướng dẫn sử dụng.
- /help : Danh sách lệnh.
'''
  bot.reply_to(message, help_text)


@bot.message_handler(commands=['status'])
def status(message):
  process_count = len(processes)
  bot.reply_to(message, f'Số quy trình đang chạy: {process_count}.')


@bot.message_handler(commands=['restart'])
def restart(message):
  bot.reply_to(message, 'Bot sẽ được khởi động lại trong giây lát...')
  time.sleep(2)
  python = sys.executable
  os.execl(python, python, *sys.argv)


@bot.message_handler(commands=['stop'])
def stop(message):
  bot.reply_to(message, 'Tạm dừng gửi tin nhắn...')
  for process in processes:
    process.kill()
  bot.reply_to(message, 'Đã dừng gửi tin nhắn tạm thời.')


@bot.message_handler(func=lambda message: True)
def echo_all(message):
  bot.reply_to(
      message,
      '💎Lệnh không hợp lệ. Vui lòng sử dụng lệnh /help để xem danh sách lệnh.💎'
  )


bot.polling()
