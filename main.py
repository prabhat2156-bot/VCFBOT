#!/usr/bin/env python3
# ==================================================
#    💀 CYBER MAINFRAME - VERIFICATION BOT WITH IMPORT 💀
#    ⚡ FORCE JOIN SYSTEM + BOT.PY FEATURES 💀
#    🛡️ BY: Phantom tech
# ==================================================

import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# =============== LOAD ENVIRONMENT VARIABLES ===============
load_dotenv()

# =============== IMPORT BOT.PY FEATURES ===============
import bot
# =============== BOT CONFIGURATION ===============
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_1_ID = os.getenv('CHANNEL_1_ID')
CHANNEL_1_LINK = os.getenv('CHANNEL_1_LINK')
CHANNEL_2_ID = os.getenv('CHANNEL_2_ID')
CHANNEL_2_LINK = os.getenv('CHANNEL_2_LINK')
GROUP_ID = os.getenv('GROUP_ID')
PRIVATE_LOGS_ID = os.getenv('PRIVATE_LOGS_ID')

DIVIDER = "✦ ━━━━━━━━━━━━━━━━━━━━ ✦"

# =============== DATABASE FOR VERIFIED USERS ===============
verified_users = set()

def is_user_verified(user_id):
    """Check if user is already verified"""
    return user_id in verified_users

def add_verified_user(user_id):
    """Add user to verified list"""
    verified_users.add(user_id)
    print(f"[DB] User {user_id} added to verified list")

def remove_verified_user(user_id):
    """Remove user from verified list"""
    if user_id in verified_users:
        verified_users.remove(user_id)
        print(f"[DB] User {user_id} removed from verified list")

def log_user_activity(user_id, action, details=""):
    """Log user activity to private group"""
    try:
        log_message = f"""
📊 *USER ACTIVITY LOG* 📊
{DIVIDER}
🆔 *ID:* {user_id}
📝 *Action:* {action}
📌 *Details:* {details}
{DIVIDER}
"""
        # Note: This requires bot instance to be available
        print(f"[LOG] Activity logged for user {user_id}")
    except Exception as e:
        print(f"[ERROR] Log Failed: {e}")

# =============== FORCE JOIN LOGIC ===============
async def is_user_subscribed_both(user_id, bot):
    """Check if user is in BOTH channels - REAL-TIME CHECK"""
    try:
        # Check Channel 1
        status1 = await bot.get_chat_member(CHANNEL_1_ID, user_id)
        if status1.status not in ['member', 'administrator', 'creator']:
            return False
        
        # Check Channel 2
        status2 = await bot.get_chat_member(CHANNEL_2_ID, user_id).status
        if status2 not in ['member', 'administrator', 'creator']:
            return False
            
        return True
    except Exception as e:
        print(f"[ERROR] API Check Failed: {e}")
        return False

def force_join_markup():
    """Generate Hacker Theme Inline Buttons for 2 Channels"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🔒 JOIN NETWORK 1", url=CHANNEL_1_LINK))
    markup.add(InlineKeyboardButton("🔒 JOIN NETWORK 2", url=CHANNEL_2_LINK))
    markup.add(InlineKeyboardButton("⚡ VERIFY CONNECTION", callback_data="verify_access"))
    return markup

# =============== MESSAGE HANDLERS ===============
async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    print(f"[LOG] Connection attempt by ID: {user_id}")
    log_user_activity(user_id, "START_COMMAND", f"User started bot")

    # REAL-TIME CHECK - Check channels EVERY TIME
    if not await is_user_subscribed_both(user_id, ctx.bot):
        # ❌ ACCESS DENIED MESSAGE
        text = f"""
🚨 *SYSTEM BREACH DETECTED* 🚨
{DIVIDER}
❌ *ACCESS DENIED!* `You have left the encrypted network.`

🛡️ You must join BOTH channels to use this bot.
{DIVIDER}
"""
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=force_join_markup())
        remove_verified_user(user_id)
        print(f"[BLOCKED] Access Denied for ID: {user_id}")
        return

    # ✅ ACCESS GRANTED - Show bot.py Welcome Message + Features
    add_verified_user(user_id)
    
    # Show Welcome Message from bot.py
    welcome_text = f"""
✅ *ACCESS GRANTED* ✅
{DIVIDER}
Welcome to the Mainframe, `{first_name}`.

📡 *Status:* Connected
🛡️ *Security:* Encrypted
⚡ *Privilege:* Admin Level 1

`Waiting for command execution...`
{DIVIDER}
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    # Show Features Menu from bot.py
    features_menu = main_menu()
    await update.message.reply_text("🎯 *Available Features:*", reply_markup=features_menu)
    
    print(f"[GRANTED] Access Approved for ID: {user_id}")

async def handle_all_messages(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Intercept all other messages - REAL-TIME CHECK"""
    user_id = update.effective_user.id
    
    # REAL-TIME CHECK on EVERY message
    if not await is_user_subscribed_both(user_id, ctx.bot):
        await update.message.reply_text("⚠️ *ERROR:* You cannot send messages until you bypass the firewall. Send /start", parse_mode="Markdown")
        remove_verified_user(user_id)
        log_user_activity(user_id, "MESSAGE_BLOCKED", "User left channels")
    else:
        # Call bot.py command handler
        response = handle_command(update.message.text)
        await update.message.reply_text(response, parse_mode="Markdown")

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    q = update.callback_query
    await q.answer()
    
    if q.data == "verify_access":
        # REAL-TIME CHECK
        if not await is_user_subscribed_both(user_id, ctx.bot):
            await q.answer("❌ FIREWALL ACTIVE: You have not joined the network yet!", show_alert=True)
        else:
            await q.answer("✅ Verified! Access Granted", show_alert=True)
            await q.message.delete()
            
            add_verified_user(user_id)
            
            # Show Welcome Message from bot.py
            welcome_text = f"""
✅ *FIREWALL BYPASSED* ✅
{DIVIDER}
Welcome to the Mainframe, `{q.from_user.first_name}`.

📡 *Status:* Connected
🛡️ *Security:* Encrypted
⚡ *Privilege:* Admin Level 1

`Waiting for command execution...`
{DIVIDER}
"""
            await q.message.reply_text(welcome_text, parse_mode="Markdown")
            
            # Show Features Menu from bot.py
            features_menu = main_menu()
            await q.message.reply_text("🎯 *Available Features:*", reply_markup=features_menu)

# =============== GROUP MESSAGE HANDLER ===============
async def group_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle messages from group (main bot detection)"""
    user_id = update.effective_user.id
    add_verified_user(user_id)
    log_user_activity(user_id, "GROUP_JOIN", "User joined main bot group")
    print(f"[GROUP] User {user_id} verified from group")

# =============== NEW MEMBER LOGGING ===============
async def new_member_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Log when new members join the group"""
    if update.message.chat.id == GROUP_ID:
        for user in update.message.new_chat_members:
            user_id = user.id
            first_name = user.first_name
            username = user.username if user.username else "N/A"
            
            log_message = f"""
🎉 *NEW MEMBER JOINED* 🎉
{DIVIDER}
👤 *Name:* {first_name}
🆔 *ID:* {user_id}
🔗 *Username:* @{username}
{DIVIDER}
"""
            # Note: This requires bot instance to be available
            print(f"[NEW MEMBER] {first_name} joined the group")

# =============== CHECK SUBSCRIPTION COMMAND ===============
async def check_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if await is_user_subscribed_both(user_id, ctx.bot):
        await update.message.reply_text("✅ You are subscribed to both channels!")
    else:
        await update.message.reply_text("❌ You are not subscribed to both channels!")

# =============== ADMIN COMMAND ===============
async def admin_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == 123456789:  # Apna user ID yahan daalo
        await update.message.reply_text(f"""
🛡️ *ADMIN PANEL* 🛡️
{DIVIDER}
📊 *Statistics:*
✅ Verified Users: {len(verified_users)}
📡 Bot Status: Active
{DIVIDER}
""", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Access Denied!")

# =============== START BOT ===============
if __name__ == "__main__":
    print(f"{'='*50}")
    print(f"💀 CYBER MAINFRAME - VERIFICATION BOT 💀")
    print(f"🚨 FORCE JOIN GATEWAY ACTIVE 🚨")
    print(f"{'='*50}")
    print(f"📡 Target Channel 1: {CHANNEL_1_ID}")
    print(f"📡 Target Channel 2: {CHANNEL_2_ID}")
    print(f"📡 Group ID: {GROUP_ID}")
    print(f"📡 Private Logs: {PRIVATE_LOGS_ID}")
    print(f"✅ Bot is listening for incoming connections...\n")
    
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("check", check_command))
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CallbackQueryHandler(callback_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
        application.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, group_handler))
        application.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
