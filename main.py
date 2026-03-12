import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
import bot # Aapka original bot.py

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_CHANNELS = ["@Madarawswork", "@madarachatgroup"] # Apne channel usernames yahan dalo

# --- RENDER SERVER ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is Online"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- STRICT JOIN CHECK ---
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

async def send_join_msg(update: Update):
    btns = [[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch[1:]}")] for ch in REQUIRED_CHANNELS]
    btns.append([InlineKeyboardButton("Verify ✅", callback_data="verify_subs")])
    text = "❌ **Access Denied!**\n\nYou have left the channel. To join again, please join and verify."
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns))

# --- MIDDLEWARE FOR ALL CALLBACKS (Buttons Fix) ---
async def global_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # 1. Agar Verify button hai toh uska logic alag chalega
    if query.data == "verify_subs":
        if await is_subscribed(update, context):
            await query.answer("Verified! ✅")
            await query.edit_message_text("✅ Verification successful! Now press /start once to use the bot.")
        else:
            await query.answer("❌ Please join both Channel!", show_alert=True)
        return

    # 2. Baki saare buttons ke liye check
    if not await is_subscribed(update, context):
        await query.answer("❌ Access Revoked! Join first.", show_alert=True)
        return await send_join_msg(update)

    # 3. Agar joined hai toh bot.py ke buttons chalenge
    await bot.buttons(update, context)

# --- MIDDLEWARE FOR MESSAGES & FILES ---
async def global_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return await send_join_msg(update)
    
    # Joined hai toh bot.py ke functions
    if update.message.document:
        await bot.handle_file(update, context)
    else:
        await bot.handle_text(update, context)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return await send_join_msg(update)
    await bot.start(update, context)

# --- RUN ---
if __name__ == "__main__":
    Thread(target=run_server).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Start Command
    app.add_handler(CommandHandler("start", start_handler))
    
    # All Button Clicks (Fixed Inline Button Issue)
    app.add_handler(CallbackQueryHandler(global_callback_handler))
    
    # All Files and Texts
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, global_message_handler))
    
    print("Bot is 100% Fixed and Running...")
    app.run_polling()
                           
