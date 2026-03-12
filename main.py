import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

# --- 1. IMPORT YOUR ORIGINAL BOT LOGIC ---
# Maan lete hain tumhare bot.py mein ye saare functions hain
import bot 

# --- 2. CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Apne 2 channels ke username yahan dalo
REQUIRED_CHANNELS = ["@Channel1", "@Channel2"] 

# --- 3. RENDER SERVER (24/7) ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is Online"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- 4. FORCE JOIN CHECK ---
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

# --- 5. SMART START HANDLER ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user has joined
    if not await is_subscribed(update, context):
        btns = [[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch[1:]}")] for ch in REQUIRED_CHANNELS]
        btns.append([InlineKeyboardButton("Verify & Start ✅", callback_data="verify_subs")])
        return await update.message.reply_text(
            "❌ **Access Denied!**\n\nBot use karne ke liye pehle dono channels join karein.",
            reply_markup=InlineKeyboardMarkup(btns)
        )
    
    # AGAR JOINED HAI -> Seedha tumhare bot.py wala start function
    await bot.start(update, context)

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if await is_subscribed(update, context):
        await query.answer("Verified! ✅")
        await query.delete_message()
        # Seedha tumhare bot.py wala start function call hoga
        await bot.start(update, context)
    else:
        await query.answer("❌ Pehle dono join karo!", show_alert=True)

# --- 6. RUNNING THE APPLICATION ---
if __name__ == "__main__":
    # Start Flask in background
    Thread(target=run_server).start()
    
    # Initialize Bot using your token
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Custom Force Join Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_subs"))
    
    # Register all other handlers from your original bot.py
    app.add_handler(CallbackQueryHandler(bot.buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, bot.handle_file))
    
    print("Bot is running with Force Join & Render Support...")
    app.run_polling()
        
