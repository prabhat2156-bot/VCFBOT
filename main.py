import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNELS = ["@madarachatgroup", "@Madarawswork"] # Yahan apne channel ka username dalein

# --- FLASK SERVER FOR RENDER ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is Running 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# --- FORCE JOIN CHECK FUNCTION ---
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False # Bot admin nahi hai ya channel galat hai
    return True

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_subscribed(update, context):
        # Join buttons dikhayega
        buttons = [[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch[1:]}")] for ch in CHANNELS]
        buttons.append([InlineKeyboardButton("Check Membership ✅", callback_data="verify_subs")])
        
        await update.message.reply_text(
            "❌ **Access Denied!**\n\nBot use karne ke liye aapko hamare channels join karne honge.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await update.message.reply_text(
        "👋 **Welcome!**\nAb aap bot use kar sakte hain. File bhejiye start karne ke liye.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Settings ⚙️", callback_data="settings")]])
    )

# --- CALLBACK FOR CHECK MEMBERSHIP ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "verify_subs":
        if await is_subscribed(update, context):
            await query.answer("Verification Successful! ✅")
            await query.edit_message_text("✅ Thank you for joining! Ab /start dabayein.")
        else:
            await query.answer("❌ Abhi tak aapne saare channels join nahi kiye!", show_alert=True)

# --- MAIN RUNNER ---
if __name__ == "__main__":
    # Render ke liye Flask start karein
    Thread(target=run_flask).start()
    
    # Bot start karein
    print("Bot Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Yahan aap apne baaki purane bot.py ke handlers add kar sakte hain
    # app.add_handler(MessageHandler(filters.Document.ALL, handle_file)) 
    
    app.run_polling()
