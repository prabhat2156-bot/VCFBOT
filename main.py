import os
import threading
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import bot  # Tumhari bot.py file yahan se connect ho rahi hai

# ================= LOGGING SETUP =================
# Ye error aur status ko Render par turant print karega
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= ENV VARIABLES =================
TOKEN = os.getenv("BOT_TOKEN")

# Comma se split karke list banana
channel_ids_str = os.getenv("CHANNEL_IDS", "")
CHANNEL_IDS = [int(x.strip()) for x in channel_ids_str.split(",") if x.strip()]

channel_links_str = os.getenv("CHANNEL_LINKS", "")
CHANNEL_LINKS = [x.strip() for x in channel_links_str.split(",") if x.strip()]

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running 24/7 🚀"

# ================= CHECK JOIN =================
async def check_join(user_id, context):
    if not CHANNEL_IDS:
        logger.warning("⚠️ CHANNEL_IDS set nahi hain. Verification skip ho raha hai.")
        return True

    for ch in CHANNEL_IDS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            logger.info(f"User {user_id} in Channel {ch} status: {member.status}")
            
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logger.error(f"❌ Telegram API Error for channel {ch}: {e}")
            return False
            
    return True

# ================= BUTTONS =================
def join_buttons():
    buttons = [[InlineKeyboardButton("📢 Join Channel", url=link)] for link in CHANNEL_LINKS]
    buttons.append([InlineKeyboardButton("✅ Check", callback_data="verify")])
    return InlineKeyboardMarkup(buttons)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if await check_join(user_id, context):
        # Verification pass hote hi bot.py ka start chalega
        await bot.start(update, context)
    else:
        await update.message.reply_text(
            "⚠️ Welcome! Please join our required channels first to use this bot.",
            reply_markup=join_buttons()
        )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if await check_join(user_id, context):
        await query.answer("✅ Verification Successful!", show_alert=True)
        # Verify hone par main menu show hoga
        await query.message.reply_text(
            "🤖 **MAIN MENU**\nSelect an option to begin:", 
            reply_markup=bot.main_menu(), 
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ You must join all channels first!", show_alert=True)

# ================= RUN BOT =================
def run_bot():
    if not TOKEN:
        logger.error("❌ BOT_TOKEN environment variable set nahi hai!")
        return

    application = Application.builder().token(TOKEN).build()

    # 1. Force Join Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    
    # 2. VCF Bot (bot.py) Handlers (Ye ensure karta hai ki bot.py ka har feature chale)
    application.add_handler(CallbackQueryHandler(bot.buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_file))

    logger.info("🚀 Bot Started Successfully!")
    
    # drop_pending_updates=True purane atke hue messages ko ignore karega
    application.run_polling(drop_pending_updates=True)

# ================= FLASK =================
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
            
