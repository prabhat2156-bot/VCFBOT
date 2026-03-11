import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import bot

TOKEN = "8247588556:AAE68EIloqjMtYn_KxbADulvGHZwWqkmA68"

# Private channel IDs
CHANNEL_IDS = [
    -1002576816263,
    -5169438728
]

# Invite links
CHANNEL_LINKS = [
    "https://t.me/+e7SiGFxZCR0yOTc1",
    "https://t.me/+pJ4X6oBTDFkxMjdl"
]

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running 24/7 🚀"


# ================= CHECK JOIN =================
async def check_join(user_id, context):

    for ch in CHANNEL_IDS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)

            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False

    return True


# ================= BUTTONS =================
def join_buttons():

    buttons = []

    for link in CHANNEL_LINKS:
        buttons.append(
            [InlineKeyboardButton("📢 Join Channel", url=link)]
        )

    buttons.append(
        [InlineKeyboardButton("✅ Check", callback_data="verify")]
    )

    return InlineKeyboardMarkup(buttons)


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if await check_join(user_id, context):

        await update.message.reply_text(
            "✅ Verified!\n\nYou can now use the bot."
        )

    else:

        await update.message.reply_text(
            "⚠️ Join required channels first.",
            reply_markup=join_buttons()
        )


# ================= VERIFY =================
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    if await check_join(user_id, context):

        await query.edit_message_text(
            "✅ Verification Successful!\nBot unlocked."
        )

    else:

        await query.answer(
            "❌ You must join all channels first!",
            show_alert=True
        )


# ================= BOT =================
def run_bot():

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))

    application.run_polling()


# ================= FLASK =================
def run_flask():
    app.run(host="0.0.0.0", port=10000)


# ================= MAIN =================
if __name__ == "__main__":

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_bot()
