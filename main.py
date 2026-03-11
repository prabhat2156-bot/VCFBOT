import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

# =========================
# ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
GROUP = os.getenv("GROUP")

bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# CHECK JOIN FUNCTION
# =========================

def check_join(user_id):
    try:
        channel = bot.get_chat_member(CHANNEL, user_id)
        group = bot.get_chat_member(GROUP, user_id)

        if channel.status not in ["left", "kicked"] and group.status not in ["left", "kicked"]:
            return True
        else:
            return False

    except Exception as e:
        print(e)
        return False


# =========================
# START COMMAND
# =========================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    if check_join(user_id):

        bot.send_message(
            message.chat.id,
            "✅ Welcome!\n\nBot ready hai use karne ke liye."
        )

    else:

        markup = InlineKeyboardMarkup()

        join_channel = InlineKeyboardButton(
            "📢 Join Channel",
            url=f"https://t.me/{CHANNEL.replace('@','')}"
        )

        join_group = InlineKeyboardButton(
            "👥 Join Group",
            url=f"https://t.me/{GROUP.replace('@','')}"
        )

        verify = InlineKeyboardButton(
            "✅ Verify",
            callback_data="verify_join"
        )

        markup.add(join_channel)
        markup.add(join_group)
        markup.add(verify)

        bot.send_message(
            message.chat.id,
            "⚠️ Bot use karne ke liye pehle channel aur group join karo.",
            reply_markup=markup
        )


# =========================
# VERIFY BUTTON
# =========================

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify(call):

    user_id = call.from_user.id

    if check_join(user_id):

        bot.answer_callback_query(call.id, "✅ Verification Successful")

        bot.edit_message_text(
            "✅ Verified!\n\nAb bot use kar sakte ho.",
            call.message.chat.id,
            call.message.message_id
        )

    else:

        bot.answer_callback_query(
            call.id,
            "❌ Pehle join karo!",
            show_alert=True
        )


# =========================
# FLASK SERVER (RENDER)
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running Successfully"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = threading.Thread(target=run)
    server.start()


# =========================
# START BOT
# =========================

if __name__ == "__main__":
    keep_alive()
    print("Bot Started...")
    bot.infinity_polling()
