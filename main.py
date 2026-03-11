import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

# ==========================
# ENV VARIABLES
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
GROUP = os.getenv("GROUP")

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================
# CHECK USER JOINED
# ==========================

def is_joined(user_id):
    try:
        ch = bot.get_chat_member(CHANNEL, user_id)
        gp = bot.get_chat_member(GROUP, user_id)

        if ch.status in ["member", "administrator", "creator"] and gp.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except:
        return False


# ==========================
# START COMMAND
# ==========================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    if is_joined(user_id):

        bot.send_message(
            message.chat.id,
            "✅ Welcome! Bot use kar sakte ho."
        )

    else:

        markup = InlineKeyboardMarkup()

        btn1 = InlineKeyboardButton(
            "📢 Join Channel",
            url=f"https://t.me/{CHANNEL.replace('@','')}"
        )

        btn2 = InlineKeyboardButton(
            "👥 Join Group",
            url=f"https://t.me/{GROUP.replace('@','')}"
        )

        btn3 = InlineKeyboardButton(
            "✅ Verify",
            callback_data="verify"
        )

        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)

        bot.send_message(
            message.chat.id,
            "⚠️ Bot use karne ke liye pehle Channel aur Group join karo.",
            reply_markup=markup
        )


# ==========================
# VERIFY BUTTON
# ==========================

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):

    user_id = call.from_user.id

    if is_joined(user_id):

        bot.answer_callback_query(call.id, "✅ Verified")

        bot.edit_message_text(
            "✅ Verification Successful!\n\nAb bot use kar sakte ho.",
            call.message.chat.id,
            call.message.message_id
        )

    else:

        bot.answer_callback_query(
            call.id,
            "❌ Pehle join karo!",
            show_alert=True
        )


# ==========================
# FLASK SERVER (RENDER 24/7)
# ==========================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    thread = threading.Thread(target=run)
    thread.start()


# ==========================
# START BOT
# ==========================

keep_alive()
print("Bot Started...")

bot.infinity_polling()
