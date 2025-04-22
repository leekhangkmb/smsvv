from keep_alive import keep_alive
keep_alive()

import telebot
import time
import json
import os
import subprocess
import tempfile
import random
import requests
from collections import defaultdict
from telebot import types

# Cấu hình bot
API_TOKEN = '7759219490:AAHK1vcQwlQCRmgLwQQZ1JaW5AGPxr1flr8'
bot = telebot.TeleBot(API_TOKEN)

# Cấu hình khác
admins = [6905385502]  # ID admin
GROUP_ID_KIN = -1002513165620  # ID nhóm thông báo
NHOM_CANTHAMGIA = ['@qwertghyjsdfghjertghjdfgh']  # Danh sách nhóm cần tham gia
blacklist = ["112", "113", "114", "115", "116", "117", "118", "119", "0", "1", "2", "3", "4"]
user_usage = defaultdict(list)
user_states = {}  # Lưu trạng thái cho lệnh /thongbao

# Danh sách emoji để thả reaction
emoji_list = ['👍', '❤️', '🔥', '🥰', '👏', '😁', '🎉', '🤩', '🙏', '👌', '🕊', '😍', '🐳', '💯', '⚡️', '🏆']

# File lưu trữ dữ liệu
invited_users_file = 'invitedusers.json'
user_data_file = 'userdata.json'
sdt_file = 'sdt.json'

# Hàm tải dữ liệu
def load_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            # Đảm bảo dữ liệu trong sdt.json có định dạng đúng
            if file_path == sdt_file:
                for user_id in data:
                    if not isinstance(data[user_id], list):
                        data[user_id] = []
            return data
    except FileNotFoundError:
        return {}

# Hàm lưu dữ liệu
def save_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

user_data = load_data(user_data_file)
invited_users = load_data(invited_users_file)
sdt_data = load_data(sdt_file)

# Hàm thả cảm xúc
def tha_camxuc(chat_id, message_id, emoji):
    url = f"https://api.telegram.org/bot{API_TOKEN}/setMessageReaction"
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reaction': json.dumps([{'type': 'emoji', 'emoji': emoji}])
    }
    response = requests.post(url, data=data)
    return response.json()

# Hàm mã hóa số điện thoại
def mask_phone_number(phone):
    if len(phone) >= 5:
        return f"{phone[:3]}*****{phone[-2:]}"
    return phone

# Hàm tạo hiệu ứng loading
def show_loading_animation(chat_id, message_id):
    stages = [
        "▁",
        "▁▂",
        "▁▂▃",
        "▁▂▃▅",
        "▁▂▃▅▆",
        "▁▂▃▅▆▇",
        "▁▂▃▅▆▇▉"
    ]
    for stage in stages:
        try:
            bot.edit_message_text(
                f"<b>⏳ Đang xử lý...\n{stage}</b>",
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='HTML'
            )
            time.sleep(0.3)  # Độ trễ để tạo hiệu ứng mượt
        except telebot.apihelper.ApiTelegramException:
            break

# Hàm kiểm tra tham gia nhóm
def check_subscription(user_id):
    for channel in NHOM_CANTHAMGIA:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except telebot.apihelper.ApiTelegramException as e:
            if "chat not found" in str(e).lower():
                print(f"Lỗi: Không tìm thấy nhóm/kênh {channel}")
                return False
            return False
    return True

# Xử lý lệnh /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    referrer_id = None

    # Kiểm tra referrer_id nếu có
    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]

    # Lưu user_id vào user_data
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {'invited': 0}
        save_data(user_data_file, user_data)

    # Lưu referrer_id vào invited_users nếu có
    if referrer_id and str(user_id) not in invited_users:
        invited_users[str(user_id)] = referrer_id
        save_data(invited_users_file, invited_users)

    # Gửi thông báo và nút tham gia nhóm
    markup = types.InlineKeyboardMarkup()
    for channel in NHOM_CANTHAMGIA:
        markup.add(types.InlineKeyboardButton('👉 Tham Gia Nhóm 👈', url=f'https://t.me/{channel[1:]}'))
    markup.add(types.InlineKeyboardButton('✔️ Kiểm Tra ✔️', callback_data='check'))

    photo_url = 'https://i.imgur.com/anWzgzZ.jpeg'
    bot.send_photo(
        message.chat.id,
        photo=photo_url,
        caption=(
            "<b>👮🏻‍♂️ MỜI BẠN BÈ NHẬN CODE❗️❗️\n\n"
            "✅ CODE SỐ LƯỢNG CÓ HẠN, NHANH TAY LÊN! 💋\n\n"
            "⏳ CHỈ MẤT VÀI PHÚT ĐỂ NHẬN QUÀ CỰC CHẤT 😇\n\n"
            "🔰 XÉT DUYỆT NHANH CHÓNG TRONG 24H 👌\n\n</b>"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

# Xử lý callback kiểm tra
@bot.callback_query_handler(func=lambda call: call.data == 'check')
def check_channels(call):
    user_id = call.from_user.id

    # Xóa tin nhắn trước đó
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Lỗi khi xóa tin nhắn: {e}")

    if check_subscription(user_id):
        if str(user_id) not in user_data:
            user_data[str(user_id)] = {'invited': 0}
            save_data(user_data_file, user_data)

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton('🚀 Spam SMS'))
        markup.add(types.KeyboardButton('🎫 Nhóm bán STK bào game'), types.KeyboardButton('🌐 Proxy bào game'))
        markup.add(types.KeyboardButton('🏆 Danh sách spam'))

        bot.send_message(
            call.message.chat.id,
            "<b>🔴 CHÀO MỪNG BẠN QUAY LẠI! 🎉</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup()
        for channel in NHOM_CANTHAMGIA:
            markup.add(types.InlineKeyboardButton('👉 Tham Gia Nhóm 👈', url=f'https://t.me/{channel[1:]}'))
        markup.add(types.InlineKeyboardButton('✔️ Kiểm Tra ✔️', callback_data='check'))
        bot.send_message(
            call.message.chat.id,
            "<b>❌ VUI LÒNG THAM GIA ĐẦY ĐỦ CÁC NHÓM!</b>",
            parse_mode='HTML',
            reply_markup=markup
        )

# Xử lý lệnh /smskmb
@bot.message_handler(commands=['smskmb'])
def smskmb(message):
    user_id = message.from_user.id
    current_time = time.time()

    # Kiểm tra tham gia nhóm
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        for channel in NHOM_CANTHAMGIA:
            markup.add(types.InlineKeyboardButton('👉 Tham Gia Nhóm 👈', url=f'https://t.me/{channel[1:]}'))
        markup.add(types.InlineKeyboardButton('✔️ Kiểm Tra ✔️', callback_data='check'))
        bot.reply_to(
            message,
            "<b>❌ VUI LÒNG THAM GIA ĐẦY ĐỦ CÁC NHÓM!</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
        return

    # Kiểm tra admin (ngoại lệ giới hạn sử dụng)
    if user_id in admins:
        handle_smskmb(message)
        return

    # Kiểm tra giới hạn sử dụng cho người dùng thường
    user_usage[user_id] = [t for t in user_usage[user_id] if current_time - t < 300]
    if len(user_usage[user_id]) >= 2:
        bot.reply_to(message, "<blockquote><i>Đã vượt quá 2 lần trong 5 phút. Vui lòng thử lại sau!</i></blockquote>", parse_mode='HTML')
        return

    user_usage[user_id].append(current_time)
    handle_smskmb(message)

def handle_smskmb(message):
    params = message.text.split()[1:] if len(message.text.split()) > 1 else []
    if len(params) != 2:
        bot.reply_to(message, "🔰 <b>Cú pháp sử dụng:</b> <blockquote>👉🏻 /smskmb [số điện thoại] [số lần]\n\n💡 Ví dụ: <code>/smskmb 0942424242 5</code></blockquote>", parse_mode='HTML')
        return

    sdt, count = params
    if not count.isdigit():
        bot.reply_to(message, "<blockquote><i>Số lần không hợp lệ!</i></blockquote>", parse_mode='HTML')
        return

    count = int(count)
    if count > 5:
        bot.reply_to(message, "<blockquote><i>Tối đa 5 lần!</i></blockquote>", parse_mode='HTML')
        return

    if sdt in blacklist:
        bot.reply_to(message, f"<b>🚫 Số {sdt} bị chặn!</b>", parse_mode='HTML')
        return

    # Gửi tin nhắn tạm thời
    temp_message = bot.reply_to(message, "<b>⏳ Đang xử lý...</b>", parse_mode='HTML')

    # Hiển thị hiệu ứng loading
    show_loading_animation(message.chat.id, temp_message.message_id)

    # Lấy thông tin người dùng
    user_id = message.from_user.id
    try:
        user_info = bot.get_chat(user_id)
        user_full_name = user_info.first_name + (f" {user_info.last_name}" if user_info.last_name else "")
    except Exception as e:
        user_full_name = "Người dùng không xác định"

    # Mã hóa số điện thoại cho thông điệp người dùng
    masked_sdt = mask_phone_number(sdt)

    # Lưu số điện thoại và số lần vào sdt.json (cộng dồn)
    if str(user_id) not in sdt_data or not isinstance(sdt_data[str(user_id)], list):
        sdt_data[str(user_id)] = []
    sdt_data[str(user_id)].append({
        'phone': sdt,
        'count': count,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(sdt_file, sdt_data)

    # Thông điệp thành công
    success_message = f'''
<b>🚀 ĐÃ SPAM THÀNH CÔNG!</b>
<blockquote>
👮🏻‍♂️ Thực hiện: <a href='tg://user?id={user_id}'>{user_full_name}</a>
📞 Số: {masked_sdt}
🔄 Lặp: {count} lần
</blockquote>
'''

    script_filename = "api.py"
    try:
        if os.path.isfile(script_filename):
            with open(script_filename, 'r', encoding='utf-8') as file:
                script_content = file.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
                temp_file.write(script_content.encode('utf-8'))
                temp_file_path = temp_file.name

            subprocess.Popen(["python", temp_file_path, sdt, str(count)])
            try:
                bot.send_message(GROUP_ID_KIN, f'''
<b>🚀 ĐÃ SPAM THÀNH CÔNG!</b>
<blockquote>
👮🏻‍♂️ Thực hiện: <a href='tg://user?id={user_id}'>{user_full_name}</a>
🆔 {user_id}
📞 Số: {sdt}
🔄 Lặp: {count} lần
</blockquote>
''', parse_mode='HTML')
            except telebot.apihelper.ApiTelegramException as e:
                if "chat not found" in str(e).lower():
                    bot.edit_message_text(
                        "<b>❌ Lỗi: Không tìm thấy nhóm thông báo!</b>",
                        chat_id=message.chat.id,
                        message_id=temp_message.message_id,
                        parse_mode='HTML'
                    )
                    return
                raise e

            # Chỉnh sửa tin nhắn tạm thời
            bot.edit_message_text(
                success_message,
                chat_id=message.chat.id,
                message_id=temp_message.message_id,
                parse_mode='HTML'
            )

            # Thả reaction ngẫu nhiên
            random_emoji = random.choice(emoji_list)
            tha_camxuc(message.chat.id, message.message_id, random_emoji)
        else:
            bot.edit_message_text(
                "<b>❌ Tập tin api.py không tìm thấy!</b>",
                chat_id=message.chat.id,
                message_id=temp_message.message_id,
                parse_mode='HTML'
            )
    except Exception as e:
        bot.edit_message_text(
            f"<b>❌ Lỗi: {str(e)}</b>",
            chat_id=message.chat.id,
            message_id=temp_message.message_id,
            parse_mode='HTML'
        )

# Xử lý lệnh /thongbao
@bot.message_handler(commands=['thongbao'])
def thongbao_text(message):
    print(f"Received /thongbao from user_id: {message.from_user.id}")  # Debug log
    # Kiểm tra quyền admin
    if message.from_user.id not in admins:
        bot.reply_to(message, "<b>⛔ Bạn không có quyền thực hiện lệnh này.</b>", parse_mode='HTML')
        print(f"User {message.from_user.id} not in admins: {admins}")  # Debug log
        return

    # Lưu trạng thái ban đầu
    user_id = str(message.from_user.id)
    user_states[user_id] = {'step': 'choose_type', 'message_id': None}

    # Hỏi lựa chọn loại thông báo
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("KHÔNG ẢNH", callback_data="thongbao_no_photo"),
        types.InlineKeyboardButton("CÓ ẢNH", callback_data="thongbao_with_photo")
    )
    try:
        sent_message = bot.send_message(
            message.chat.id,
            "<b>📢 Bạn muốn gửi thông báo như thế nào?</b>\n"
            "👉🏻 CHỈ GỬI VĂN BẢN hay GỬI VĂN BẢN + ẢNH?",
            parse_mode='HTML',
            reply_markup=markup
        )
        user_states[user_id]['message_id'] = sent_message.message_id
        print(f"Sent choose_type message to {user_id}, message_id: {sent_message.message_id}")  # Debug log
    except Exception as e:
        bot.reply_to(message, f"<b>❌ Lỗi khi gửi tin nhắn: {str(e)}</b>", parse_mode='HTML')
        print(f"Error sending choose_type message: {str(e)}")  # Debug log

@bot.callback_query_handler(func=lambda call: call.data in ["thongbao_no_photo", "thongbao_with_photo"])
def handle_thongbao_type(call):
    user_id = str(call.from_user.id)
    print(f"Callback received: {call.data} from user_id: {user_id}")  # Debug log
    if user_id not in user_states or user_states[user_id]['step'] != 'choose_type':
        bot.answer_callback_query(call.id, "❌ Vui lòng sử dụng /thongbao để bắt đầu lại.")
        print(f"Invalid state for user {user_id}: {user_states.get(user_id)}")  # Debug log
        return

    if call.data == "thongbao_no_photo":
        user_states[user_id] = {
            'step': 'input_text',
            'photo_id': None,
            'message_id': call.message.message_id
        }
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="<b>📝 Vui lòng gửi văn bản thông báo cần gửi:</b>",
                parse_mode='HTML'
            )
            print(f"Updated to input_text for user {user_id}")  # Debug log
        except Exception as e:
            print(f"Error editing message: {str(e)}")  # Debug log
            bot.send_message(call.message.chat.id, "<b>📝 Vui lòng gửi văn bản thông báo cần gửi:</b>", parse_mode='HTML')
    else:  # thongbao_with_photo
        user_states[user_id] = {
            'step': 'input_photo',
            'photo_id': None,
            'message_id': call.message.message_id
        }
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="<b>🖼 Vui lòng gửi ảnh trước:</b>",
                parse_mode='HTML'
            )
            print(f"Updated to input_photo for user {user_id}")  # Debug log
        except Exception as e:
            print(f"Error editing message: {str(e)}")  # Debug log
            bot.send_message(call.message.chat.id, "<b>🖼 Vui lòng gửi ảnh trước:</b>", parse_mode='HTML')

    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text'], func=lambda message: str(message.from_user.id) in user_states and user_states[str(message.from_user.id)]['step'] == 'input_text')
def handle_text_input(message):
    user_id = str(message.from_user.id)
    print(f"Text input received from user_id: {user_id}")  # Debug log
    if user_id not in user_states or user_states[user_id]['step'] != 'input_text':
        print(f"Invalid text input state for user {user_id}: {user_states.get(user_id)}")  # Debug log
        return

    announcement = message.text
    user_states[user_id] = {
        'step': 'confirm',
        'photo_id': None,
        'text': announcement,
        'message_id': user_states[user_id]['message_id']
    }

    # Lấy full_name của admin
    try:
        admin_info = bot.get_chat(message.from_user.id)
        admin_full_name = admin_info.first_name + (" " + admin_info.last_name if admin_info.last_name else "")
    except Exception:
        admin_full_name = "Không xác định"

    # Tạo nội dung xác nhận
    full_announcement = (
        f"📝 <b>{announcement}</b>\n\n"
        f"🖋 <b>Tin nhắn được gửi bởi</b> <a href='tg://user?id={message.from_user.id}'>{admin_full_name}</a>"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("ĐỒNG Ý", callback_data="thongbao_confirm"),
        types.InlineKeyboardButton("HỦY", callback_data="thongbao_cancel")
    )
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=user_states[user_id]['message_id'],
            text=f"<b>📢 Xác nhận thông báo:</b>\n{full_announcement}",
            parse_mode='HTML',
            reply_markup=markup
        )
        print(f"Sent confirmation message for user {user_id}")  # Debug log
    except Exception as e:
        print(f"Error editing confirmation message: {str(e)}")  # Debug log
        sent_message = bot.send_message(
            message.chat.id,
            f"<b>📢 Xác nhận thông báo:</b>\n{full_announcement}",
            parse_mode='HTML',
            reply_markup=markup
        )
        user_states[user_id]['message_id'] = sent_message.message_id

@bot.message_handler(content_types=['photo'], func=lambda message: str(message.from_user.id) in user_states and user_states[str(message.from_user.id)]['step'] == 'input_photo')
def handle_photo_input(message):
    user_id = str(message.from_user.id)
    print(f"Photo input received from user_id: {user_id}")  # Debug log
    if user_id not in user_states or user_states[user_id]['step'] != 'input_photo':
        print(f"Invalid photo input state for user {user_id}: {user_states.get(user_id)}")  # Debug log
        return

    photo_id = message.photo[-1].file_id
    user_states[user_id] = {
        'step': 'input_text_with_photo',
        'photo_id': photo_id,
        'message_id': user_states[user_id]['message_id']
    }

    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=user_states[user_id]['message_id'],
            text="<b>📝 Ảnh đã nhận! Vui lòng gửi văn bản thông báo cần gửi:</b>",
            parse_mode='HTML'
        )
        print(f"Updated to input_text_with_photo for user {user_id}")  # Debug log
    except Exception as e:
        print(f"Error editing message: {str(e)}")  # Debug log
        bot.send_message(
            message.chat.id,
            "<b>📝 Ảnh đã nhận! Vui lòng gửi văn bản thông báo cần gửi:</b>",
            parse_mode='HTML'
        )

@bot.message_handler(content_types=['text'], func=lambda message: str(message.from_user.id) in user_states and user_states[str(message.from_user.id)]['step'] == 'input_text_with_photo')
def handle_text_with_photo_input(message):
    user_id = str(message.from_user.id)
    print(f"Text with photo input received from user_id: {user_id}")  # Debug log
    if user_id not in user_states or user_states[user_id]['step'] != 'input_text_with_photo':
        print(f"Invalid text_with_photo input state for user {user_id}: {user_states.get(user_id)}")  # Debug log
        return

    announcement = message.text
    user_states[user_id] = {
        'step': 'confirm',
        'photo_id': user_states[user_id]['photo_id'],
        'text': announcement,
        'message_id': user_states[user_id]['message_id']
    }

    # Lấy full_name của admin
    try:
        admin_info = bot.get_chat(message.from_user.id)
        admin_full_name = admin_info.first_name + (" " + admin_info.last_name if admin_info.last_name else "")
    except Exception:
        admin_full_name = "Không xác định"

    # Tạo nội dung xác nhận
    full_announcement = (
        f"📝 <b>{announcement}</b>\n\n"
        f"🖋 <b>Tin nhắn được gửi bởi</b> <a href='tg://user?id={message.from_user.id}'>{admin_full_name}</a>\n"
        "<i>[Kèm ảnh]</i>"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("ĐỒNG Ý", callback_data="thongbao_confirm"),
        types.InlineKeyboardButton("HỦY", callback_data="thongbao_cancel")
    )
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=user_states[user_id]['message_id'],
            text=f"<b>📢 Xác nhận thông báo:</b>\n{full_announcement}",
            parse_mode='HTML',
            reply_markup=markup
        )
        print(f"Sent confirmation with photo message for user {user_id}")  # Debug log
    except Exception as e:
        print(f"Error editing confirmation message: {str(e)}")  # Debug log
        sent_message = bot.send_message(
            message.chat.id,
            f"<b>📢 Xác nhận thông báo:</b>\n{full_announcement}",
            parse_mode='HTML',
            reply_markup=markup
        )
        user_states[user_id]['message_id'] = sent_message.message_id

@bot.callback_query_handler(func=lambda call: call.data in ["thongbao_confirm", "thongbao_cancel"])
def handle_confirmation(call):
    user_id = str(call.from_user.id)
    print(f"Confirmation callback received: {call.data} from user_id: {user_id}")  # Debug log
    if user_id not in user_states or user_states[user_id]['step'] != 'confirm':
        bot.answer_callback_query(call.id, "❌ Vui lòng sử dụng /thongbao để bắt đầu lại.")
        print(f"Invalid confirmation state for user {user_id}: {user_states.get(user_id)}")  # Debug log
        return

    if call.data == "thongbao_cancel":
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=user_states[user_id]['message_id'],
                text="<b>❌ ĐÃ HỦY GỬI TIN NHẮN</b>",
                parse_mode='HTML'
            )
            print(f"Cancelled announcement for user {user_id}")  # Debug log
        except Exception as e:
            print(f"Error editing cancel message: {str(e)}")  # Debug log
            bot.send_message(call.message.chat.id, "<b>❌ ĐÃ HỦY GỬI TIN NHẮN</b>", parse_mode='HTML')
        del user_states[user_id]
        bot.answer_callback_query(call.id)
        return

    # Xử lý gửi thông báo (ĐỒNG Ý)
    announcement = user_states[user_id]['text']
    photo_id = user_states[user_id]['photo_id']
    success_count = 0
    failed_count = 0
    failed_users = []

    # Lấy full_name của admin
    try:
        admin_info = bot.get_chat(user_id)
        admin_full_name = admin_info.first_name + (" " + admin_info.last_name if admin_info.last_name else "")
    except Exception:
        admin_full_name = "Không xác định"

    # Tạo nội dung thông báo
    full_announcement = (
        f"📝 <b>{announcement}</b>\n\n"
        f"🖋 <b>Tin nhắn được gửi bởi</b> <a href='tg://user?id={user_id}'>{admin_full_name}</a>"
    )

    # Gửi thông báo đến tất cả người dùng
    for target_user_id in user_data.keys():
        try:
            if photo_id:
                bot.send_photo(
                    chat_id=target_user_id,
                    photo=photo_id,
                    caption=full_announcement,
                    parse_mode='HTML'
                )
            else:
                bot.send_message(
                    chat_id=target_user_id,
                    text=full_announcement,
                    parse_mode='HTML'
                )
            success_count += 1
            time.sleep(0.1)  # Tránh rate limit
            print(f"Sent announcement to user {target_user_id}")  # Debug log
        except Exception as e:
            print(f"Failed to send to user {target_user_id}: {str(e)}")  # Debug log
            failed_count += 1
            failed_users.append(target_user_id)

    # Tạo báo cáo kết quả
    result_message = (
        f"✅ <b>Gửi thành công:</b> {success_count}\n"
        f"🔴 <b>Gửi thất bại:</b> {failed_count}\n"
        f"🖋 <b>Tin nhắn được gửi bởi</b> <a href='tg://user?id={user_id}'>{admin_full_name}</a>"
    )
    if failed_users:
        result_message += "\n<b>Danh sách người dùng gửi thất bại:</b>\n"
        for target_user_id in failed_users:
            try:
                user_info = bot.get_chat(target_user_id)
                full_name = user_info.first_name + (" " + user_info.last_name if user_info.last_name else "")
            except Exception:
                full_name = "Không xác định"
            result_message += f"🆔 <code>{target_user_id}</code> - <a href='tg://user?id={target_user_id}'>{full_name}</a>\n"

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=user_states[user_id]['message_id'],
            text=result_message,
            parse_mode='HTML'
        )
        print(f"Sent result message to user {user_id}")  # Debug log
    except Exception as e:
        print(f"Error editing result message: {str(e)}")  # Debug log
        bot.send_message(call.message.chat.id, result_message, parse_mode='HTML')

    del user_states[user_id]
    bot.answer_callback_query(call.id)

# Biến toàn cục
full_name_cache = {}
cached_spam_list = None
cached_spam_timestamp = 0
CACHE_DURATION = 300  # Cache 5 phút
sdt_file = 'sdt.json'

# Hàm tải dữ liệu
def load_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            # Đảm bảo dữ liệu sdt.json là dict với user_id chứa list
            if file_path == sdt_file:
                if not isinstance(data, dict):
                    print(f"Error: {file_path} is not a valid dictionary")
                    return {}
                for user_id in data:
                    if not isinstance(data[user_id], list):
                        print(f"Warning: Converting {user_id} data to list in {file_path}")
                        data[user_id] = []
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {file_path}: {str(e)}")
        return {}

# Xử lý nút 🏆 Danh sách spam
@bot.message_handler(func=lambda message: message.text == '🏆 Danh sách spam')
def handle_spam_list(message):
    global cached_spam_list, cached_spam_timestamp
    
    # Kiểm tra quyền admin
    if message.from_user.id not in admins:
        bot.reply_to(message, "<b>⛔ Bạn không có quyền thực hiện lệnh này.</b>", parse_mode='HTML')
        return
    
    # Kiểm tra cache
    current_time = time.time()
    if cached_spam_list is None or current_time - cached_spam_timestamp > CACHE_DURATION:
        # Đọc dữ liệu từ sdt.json
        sdt_data = load_data(sdt_file)
        print(f"Loaded sdt.json: {len(sdt_data)} users")  # Debug log
        
        # Tạo danh sách spam
        spam_list = []
        for user_id, records in sdt_data.items():
            print(f"Processing user {user_id}: {len(records)} records")  # Debug log
            for record in records:
                try:
                    spam_list.append({
                        'user_id': user_id,
                        'phone': record['phone'],
                        'count': record['count'],
                        'timestamp': record['timestamp']
                    })
                except KeyError as e:
                    print(f"Error in record for user {user_id}: Missing key {str(e)}")
        
        # Sắp xếp theo timestamp (mới nhất trước)
        spam_list.sort(key=lambda x: x['timestamp'], reverse=True)
        print(f"Total spam records: {len(spam_list)}")  # Debug log
        
        # Lưu vào cache
        cached_spam_list = spam_list
        cached_spam_timestamp = current_time
    else:
        spam_list = cached_spam_list
        print(f"Using cached spam list: {len(spam_list)} records")  # Debug log
    
    # Nếu không có dữ liệu
    if not spam_list:
        bot.send_message(
            message.chat.id,
            "🏆 <b>Danh sách spam 🏆</b>\n\nHiện tại chưa có dữ liệu.",
            parse_mode='HTML'
        )
        return
    
    # Gửi trang đầu tiên
    send_spam_list_page(message.chat.id, spam_list, 1)

def send_spam_list_page(chat_id, spam_list, page, message_id=None):
    # Phân trang: mỗi trang 10 mục
    page_size = 10
    total_records = len(spam_list)
    total_pages = (total_records + page_size - 1) // page_size
    
    # Đảm bảo trang hợp lệ
    page = max(1, min(page, total_pages))
    
    # Lấy danh sách cho trang hiện tại
    start_index = (page - 1) * page_size
    end_index = min(start_index + page_size, total_records)
    page_records = spam_list[start_index:end_index]
    
    # Tạo thông điệp danh sách
    caption = f"🏆 <b>Danh sách spam 🏆</b>\n" \
              f"─────\n" \
              f"<b>Tổng bản ghi:</b> {total_records}\n" \
              f"<b>Hiển thị {start_index + 1}-{end_index} (Trang {page}/{total_pages}):</b>\n\n"
    
    for i, record in enumerate(page_records, start=start_index + 1):
        user_id = record['user_id']
        # Kiểm tra cache tên
        if user_id not in full_name_cache:
            try:
                user_info = bot.get_chat(user_id)
                full_name_cache[user_id] = f"{user_info.first_name} {user_info.last_name or ''}".strip() or "Không xác định"
            except Exception:
                full_name_cache[user_id] = "Không xác định"
        full_name = full_name_cache[user_id]
        
        # Mã hóa số điện thoại
        masked_phone = mask_phone_number(record['phone'])
        
        # Thêm thông tin vào danh sách, bọc trong <blockquote>
        caption += f"<blockquote>➤ {i}. <a href='tg://user?id={user_id}'>{full_name}</a> <code>{user_id}</code>\n" \
                   f"📞 Số: {masked_phone}\n" \
                   f"🔄 Lần: {record['count']}\n" \
                   f"⏰ Thời gian: {record['timestamp']}</blockquote>\n\n"
    
    # Tạo nút điều hướng
    markup = types.InlineKeyboardMarkup()
    buttons = []
    if page > 1:
        buttons.append(types.InlineKeyboardButton("◀️ Trang trước", callback_data=f"spam_page_{page-1}"))
    if page < total_pages:
        buttons.append(types.InlineKeyboardButton("Trang sau ▶️", callback_data=f"spam_page_{page+1}"))
    if buttons:
        markup.add(*buttons)  # Thêm các nút trên cùng một hàng
    
    try:
        # Nếu có message_id, chỉnh sửa tin nhắn
        if message_id:
            bot.edit_message_text(
                text=caption,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            # Gửi tin nhắn mới
            sent_message = bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode='HTML',
                reply_markup=markup
            )
            return sent_message.message_id
    except Exception as e:
        print(f"Error editing message {message_id}: {str(e)}")
        sent_message = bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode='HTML',
            reply_markup=markup
        )
        return sent_message.message_id
    
# Xử lý callback phân trang
@bot.callback_query_handler(func=lambda call: call.data.startswith('spam_page_'))
def handle_spam_page_callback(call):
    page = int(call.data.split('_')[-1])
    spam_list = cached_spam_list  # Sử dụng cache
    
    if not spam_list:
        bot.answer_callback_query(call.id, "Danh sách spam hiện tại trống.")
        return
    
    message_id = send_spam_list_page(call.message.chat.id, spam_list, page, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == '🚀 Spam SMS')
def handle_game_promotion(message):
    caption = (
        "🔰 <b>Vui lòng sử dụng</b>\n\n"
        "👉🏻 <b>/smskmb [SĐT] [SỐ LẦN]</b>\n\n"
        "✅ <b>Ví dụ:</b> <code>/smskmb 0942424242 1</code>"
    )
    
    bot.send_message(
        message.chat.id,
        text=caption,
        parse_mode='HTML'
    )

# Chạy bot
bot.polling()
