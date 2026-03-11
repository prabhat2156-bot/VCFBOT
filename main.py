#!/usr/bin/env python3

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from flask import Flask
import threading

# ================= ENV VARIABLES =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")

bot = telebot.TeleBot(BOT_TOKEN)

# ================= FLASK SERVER =================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ================= FORCE JOIN CHECK =================

def is_user_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        if status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        print("Check Error:", e)
        return False

# ================= BUTTON MARKUP =================

def force_join_markup():
    markup = InlineKeyboardMarkup(row_width=1)

    join_btn = InlineKeyboardButton(
        "📢 JOIN CHANNEL",
        url=CHANNEL_LINK
    )

    verify_btn = InlineKeyboardButton(
        "✅ VERIFY",
        callback_data="verify_access"
    )

    markup.add(join_btn)
    markup.add(verify_btn)

    return markup

# ================= START COMMAND =================

@bot.message_handler(commands=['start'])
def start_command(message):

    user_id = message.from_user.id

    if not is_user_subscribed(user_id):

        text = """
🚨 ACCESS DENIED 🚨

Bot use karne ke liye pehle channel join karo.
"""

        bot.send_message(
            user_id,
            text,
            reply_markup=force_join_markup()
        )

    else:

        bot.send_message(
            user_id,
            "✅ ACCESS GRANTED\n\nBot ready hai."
        )

# ================= VERIFY BUTTON =================

@bot.callback_query_handler(func=lambda call: call.data == "verify_access")
def verify(call):

    user_id = call.from_user.id

    if not is_user_subscribed(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Pehle channel join karo!",
            show_alert=True
        )

    else:

        bot.answer_callback_query(call.id, "✅ Verified")

        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )

        bot.send_message(
            user_id,
            "✅ Verification Successful\n\nAb bot use kar sakte ho."
        )

# ================= BLOCK OTHER MESSAGES =================

@bot.message_handler(func=lambda message: True)
def block_messages(message):

    user_id = message.from_user.id

    if not is_user_subscribed(user_id):

        bot.delete_message(
            message.chat.id,
            message.message_id
        )

        bot.send_message(
            user_id,
            "⚠️ Pehle /start karo aur channel join karo."
        )

# ================= START BOT =================

if __name__ == "__main__":

    keep_alive()

    print("Bot Started...")

    bot.infinity_polling()
