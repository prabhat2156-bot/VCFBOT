import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import bot  # Tumhari bot.py file link ho rahi hai

# ================= ENV VARIABLES SETUP =================
TOKEN = os.getenv("BOT_TOKEN")

channel_ids_str = os.getenv("CHANNEL_IDS", "")
CHANNEL_IDS = [int(x.strip()) for x in channel_ids_str.split(",")] if channel_ids_str else []

channel_links_str = os.getenv("CHANNEL_LINKS", "")
CHANNEL_LINKS = [x.strip() for x in channel_links_str.split(",")] if channel_links_str else []

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running 24/7 🚀"

# ================= CHECK JOIN =================
async def check_join(user_id, context):
    if not CHANNEL_IDS:
        return True

    for ch in CHANNEL_IDS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"Error checking channel {ch}: {e}")
            return False
    return True

# ================= BUTTONS =================
def join_buttons():
    buttons = [[InlineKeyboardButton("📢 Join Channel", url=link)] for link in CHANNEL_LINKS]
    buttons.append([InlineKeyboardButton("✅ Check", callback_data="verify")])
    return InlineKeyboardMarkup(buttons)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if await check_join(user_id, context):
        # Agar user joined hai, toh seedha bot.py ka menu dikhao
        await bot.start(update, context)
    else:
        await update.message.reply_text(
            "⚠️ Welcome! Please join our required channels first to use this bot.",
            reply_markup=join_buttons()
        )

# ================= VERIFY =================
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if await check_join(user_id, context):
        await query.answer("✅ Verification Successful!", show_alert=True)
        # Verify hone ke baad seedha VCF bot ka menu khulega
        await query.message.reply_text(
            "🤖 **MAIN MENU**\nSelect an option to begin:", 
            reply_markup=bot.main_menu(), 
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ You must join all channels first!", show_alert=True)

# ================= BOT =================
def run_bot():
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable set nahi hai! Render par set karo.")
        return

    application = Application.builder().token(TOKEN).build()

    # 1. Force Join Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    
    # 2. VCF Bot (bot.py) Handlers
    application.add_handler(CallbackQueryHandler(bot.buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_file))

    print("🚀 Bot Started Successfully!")
    application.run_polling()

# ================= FLASK =================
def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ================= MAIN =================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
                                                  
