import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- IMPORT EVERYTHING FROM YOUR BOT.PY ---
from bot import (
    start as original_start, 
    buttons as original_buttons, 
    handle_text, 
    handle_file, 
    BOT_TOKEN,
    app as original_app # Agar bot.py mein 'app' object hai toh
)

# --- CONFIGURATION ---
REQUIRED_CHANNELS = ["@madarachatgroup", "@Madarawswork"] # Yahan apne channel usernames likho

# --- RENDER FLASK SERVER ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is Online"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- FORCE JOIN CHECK ---
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

# --- NEW START HANDLER ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        btns = [[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch[1:]}")] for ch in REQUIRED_CHANNELS]
        btns.append([InlineKeyboardButton("Verify ✅", callback_data="verify_and_start")])
        return await update.message.reply_text(
            "❌ **Access Denied!**\n\nBot use karne ke liye pehle dono channels join karein.",
            reply_markup=InlineKeyboardMarkup(btns)
        )
    # Agar joined hai, toh seedha tumhare bot.py wala start function
    await original_start(update, context)

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if await is_subscribed(update, context):
        await query.answer("Success! ✅")
        await query.delete_message()
        # Seedha tumhare bot.py wala start call kar diya
        await original_start(update, context)
    else:
        await query.answer("❌ Pehle dono join karo bhenco!", show_alert=True)

# --- RUN EVERYTHING ---
if __name__ == "__main__":
    # Start Flask for Render
    Thread(target=run_server).start()
    
    # Start Bot
    # Note: Use the token and handlers exactly like your bot.py
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Custom Handlers for Force Join
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_and_start"))
    
    # Original Handlers from your bot.py
    app.add_handler(CallbackQueryHandler(original_buttons)) # Tumhare bot.py ke buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    print("Bot started with Force Join...")
    app.run_polling()
