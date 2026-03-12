import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import bot as original_bot

bot = telebot.TeleBot(config.BOT_TOKEN)

# bot instance bot.py ko dena
original_bot.bot = bot


def is_joined(user_id):

    try:

        ch1 = bot.get_chat_member(config.CHANNEL_1, user_id).status
        ch2 = bot.get_chat_member(config.CHANNEL_2, user_id).status

        if ch1 in ['left','kicked'] or ch2 in ['left','kicked']:
            return False

        return True

    except:
        return False


def join_buttons():

    markup = InlineKeyboardMarkup()

    btn1 = InlineKeyboardButton("📢 JOIN CHANNEL 1", url=config.CHANNEL_1_LINK)
    btn2 = InlineKeyboardButton("📢 JOIN CHANNEL 2", url=config.CHANNEL_2_LINK)
    verify = InlineKeyboardButton("✅ VERIFY", callback_data="verify")

    markup.add(btn1)
    markup.add(btn2)
    markup.add(verify)

    return markup


@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    if not is_joined(user_id):

        bot.send_message(
            user_id,
            "⚠️ Bot use karne ke liye dono channels join karo",
            reply_markup=join_buttons()
        )

    else:

        bot.send_message(user_id, "✅ Access Granted")

        bot.send_message(
            config.OWNER_ID,
            f"🔔 New User Access\n\n{message.from_user.first_name}\n{user_id}"
        )

        # original bot start
        original_bot.start(message)


@bot.callback_query_handler(func=lambda call: call.data=="verify")
def verify(call):

    user_id = call.from_user.id

    if not is_joined(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Join both channels first",
            show_alert=True
        )

    else:

        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )

        bot.send_message(user_id, "✅ Verified")

        bot.send_message(
            config.OWNER_ID,
            f"🔔 User Verified\n\n{call.from_user.first_name}\n{user_id}"
        )

        original_bot.start(call.message)


@bot.message_handler(func=lambda message: True)
def all_messages(message):

    user_id = message.from_user.id

    if not is_joined(user_id):

        bot.send_message(user_id, "⚠️ Send /start and join channels")

    else:

        # message original bot ko
        original_bot.handle(message)


print("Force Join Gateway Running...")

bot.infinity_polling()
