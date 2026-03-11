import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import bot  # Tumhari bot.py file import ho rahi hai

# Ek hi main token use karo jo bot.py me bhi hai (Ya apna preferred token daalo)
TOKEN = "8572086597:AAGiQX9jC7q4Kj_lmqSojgVp0lNgDwy_u9Q" 

CHANNEL_IDS = [-1002576816263, -5169438728]
CHANNEL_LINKS = ["https://t.me/+e7SiGFxZCR0yOTc1", "https://t.me/+pJ4X6oBTDFkxMjdl"]

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running 24/7 🚀"

async def check_join(user_id, context):
    for ch in CHANNEL_IDS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_buttons():
    buttons = [[InlineKeyboardButton("📢 Join Channel", url=link)] for link in CHANNEL_LINKS]
    buttons.append([InlineKeyboardButton("✅ Check", callback_data="verify")])
    return InlineKeyboardMarkup(buttons)

async def start_with_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await check_join(user_id, context):
        # Agar user joined hai, toh seedha bot.py ka start function call karo
        await bot.start(update, context)
    else:
        await update.message.reply_text("⚠️ Join required channels first.", reply_markup=join_buttons())

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if await check_join(user_id, context):
        await query.answer("✅ Verification Successful!", show_alert=True)
        # Verify hone ke baad main menu dikhao
        await query.message.reply_text("🤖 **MAIN MENU**\nSelect an option to begin:", reply_markup=bot.main_menu(), parse_mode="Markdown")
    else:
        await query.answer("❌ You must join all channels first!", show_alert=True)

def run_bot():
    application = Application.builder().token(TOKEN).build()

    # Force join handlers
    application.add_handler(CommandHandler("start", start_with_force_join))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))

    # bot.py se saare handlers yahan add karo
    from telegram.ext import MessageHandler, filters
    application.add_handler(CallbackQueryHandler(bot.buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_file))

    application.run_polling()

def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
        
