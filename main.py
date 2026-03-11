import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import bot

TOKEN = "YOUR_BOT_TOKEN"

CHANNELS = [
    "channelusername1",
    "channelusername2"
]

app = Flask(__name__)

@app.route('/')
def home():
    return "Madara Bot Running 🚀"


# ================= FORCE JOIN CHECK =================
async def check_user(user_id, context):

    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(f"@{ch}", user_id)

            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False

    return True


# ================= BUTTONS =================
def join_buttons():

    buttons = []

    for ch in CHANNELS:
        buttons.append(
            [InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{ch}")]
        )

    buttons.append(
        [InlineKeyboardButton("✅ Check", callback_data="verify")]
    )

    return InlineKeyboardMarkup(buttons)


# ================= START COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if await check_user(user_id, context):

        await update.message.reply_text(
            "✅ Access Granted\n\nYou can now use the bot."
        )

    else:

        await update.message.reply_text(
            "⚠️ Please join the required channels first.",
            reply_markup=join_buttons()
        )


# ================= VERIFY BUTTON =================
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    if await check_user(user_id, context):

        await query.edit_message_text(
            "✅ Verified Successfully!\n\nBot unlocked."
        )

    else:

        await query.answer(
            "❌ Join all channels first!",
            show_alert=True
        )


# ================= BOT RUNNER =================
def run_bot():

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))

    application.run_polling()


# ================= FLASK SERVER =================
def run_flask():
    app.run(host="0.0.0.0", port=10000)


# ================= MAIN =================
if __name__ == "__main__":

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_bot()
