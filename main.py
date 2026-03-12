import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

bot = telebot.TeleBot(config.BOT_TOKEN)

# ============ FORCE JOIN CHECK ============

def is_joined(user_id):
    try:
        ch1 = bot.get_chat_member(config.CHANNEL_1, user_id).status
        ch2 = bot.get_chat_member(config.CHANNEL_2, user_id).status

        if ch1 in ["left","kicked"] or ch2 in ["left","kicked"]:
            return False

        return True

    except:
        return False


def join_buttons():
    markup = InlineKeyboardMarkup()

    btn1 = InlineKeyboardButton("📢 Join Channel 1", url=config.CHANNEL_1_LINK)
    btn2 = InlineKeyboardButton("📢 Join Channel 2", url=config.CHANNEL_2_LINK)
    verify = InlineKeyboardButton("✅ Verify", callback_data="verify")

    markup.add(btn1)
    markup.add(btn2)
    markup.add(verify)

    return markup


# ============ START ============

@bot.message_handler(commands=['start'])
def start(message):

    if not is_joined(message.from_user.id):

        bot.send_message(
            message.chat.id,
            "⚠️ Welcome! Please join our required channels first to use this bot..",
            reply_markup=join_buttons()
        )

    else:

        bot.send_message(message.chat.id,"✅ Access Granted")

        bot.send_message(
            config.OWNER_ID,
            f"🔔 New User Access\n\n{message.from_user.first_name}\n{message.from_user.id}"
        )


# ============ VERIFY ============

@bot.callback_query_handler(func=lambda call: call.data=="verify")
def verify(call):

    if not is_joined(call.from_user.id):

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

        bot.send_message(call.message.chat.id,"✅ Verified")


# ============ LOAD ORIGINAL BOT ============

import bot as original_bot

original_bot.setup(bot)


print("Bot Running...")

bot.infinity_polling()
