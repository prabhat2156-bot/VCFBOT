import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
from dotenv import load_dotenv

# =============== LOAD ENVIRONMENT VARIABLES ===============
load_dotenv()

# =============== TERMINAL COLORS ===============
GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

# =============== BOT CONFIGURATION ===============
# 👈 Environment Variables se load honge
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_1_ID = os.getenv('CHANNEL_1_ID')
CHANNEL_1_LINK = os.getenv('CHANNEL_1_LINK')
CHANNEL_2_ID = os.getenv('CHANNEL_2_ID')
CHANNEL_2_LINK = os.getenv('CHANNEL_2_LINK')
GROUP_ID = os.getenv('GROUP_ID')
PRIVATE_LOGS_ID = os.getenv('PRIVATE_LOGS_ID')  # New: Private group for logs
MAIN_BOT_USERNAME = os.getenv('MAIN_BOT_USERNAME')

DIVIDER = "✦ ━━━━━━━━━━━━━━━━━━━━ ✦"

bot = telebot.TeleBot(BOT_TOKEN)

# =============== DATABASE FOR VERIFIED USERS ===============
verified_users = set()
user_history = {}  # Store user join history

def is_user_verified(user_id):
    """Check if user is already verified"""
    return user_id in verified_users

def add_verified_user(user_id):
    """Add user to verified list"""
    verified_users.add(user_id)
    print(f"{GREEN}[DB] User {user_id} added to verified list{RESET}")

def remove_verified_user(user_id):
    """Remove user from verified list"""
    if user_id in verified_users:
        verified_users.remove(user_id)
        print(f"{RED}[DB] User {user_id} removed from verified list{RESET}")

def log_user_activity(user_id, action, details=""):
    """Log user activity to private group"""
    try:
        user = bot.get_chat(user_id)
        first_name = user.first_name
        username = user.username if user.username else "N/A"
        
        log_message = f"""
📊 *USER ACTIVITY LOG* 📊
{DIVIDER}
👤 *Name:* {first_name}
🆔 *ID:* {user_id}
🔗 *Username:* @{username}
📝 *Action:* {action}
📌 *Details:* {details}
🕒 *Time:* {time.strftime('%Y-%m-%d %H:%M:%S')}
{DIVIDER}
"""
        bot.send_message(PRIVATE_LOGS_ID, log_message, parse_mode="Markdown")
        print(f"{CYAN}[LOG] Activity logged for user {user_id}{RESET}")
    except Exception as e:
        print(f"{RED}[ERROR] Log Failed: {e}{RESET}")

# =============== TERMINAL COLORS ===============
def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{CYAN}{BOLD}{'='*50}{RESET}")
    print(f"{GREEN}{BOLD}    💀 CYBER MAINFRAME - VERIFICATION BOT 💀{RESET}")
    print(f"{RED}{BOLD}    🚨 FORCE JOIN GATEWAY ACTIVE 🚨{RESET}")
    print(f"{CYAN}{BOLD}{'='*50}{RESET}")
    print(f"{YELLOW}📡 Target Channel 1: {CHANNEL_1_ID}{RESET}")
    print(f"{YELLOW}📡 Target Channel 2: {CHANNEL_2_ID}{RESET}")
    print(f"{YELLOW}📡 Group ID: {GROUP_ID}{RESET}")
    print(f"{YELLOW}📡 Private Logs: {PRIVATE_LOGS_ID}{RESET}")
    print(f"{GREEN}✅ Bot is listening for incoming connections...{RESET}\n")

# =============== FORCE JOIN LOGIC ===============
def is_user_subscribed_both(user_id):
    """Check if user is in BOTH channels"""
    try:
        # Check Channel 1
        status1 = bot.get_chat_member(CHANNEL_1_ID, user_id).status
        if status1 not in ['member', 'administrator', 'creator']:
            return False
        
        # Check Channel 2
        status2 = bot.get_chat_member(CHANNEL_2_ID, user_id).status
        if status2 not in ['member', 'administrator', 'creator']:
            return False
            
        return True
    except Exception as e:
        print(f"{RED}[ERROR] API Check Failed: {e}{RESET}")
        return False

def force_join_markup():
    """Generate Hacker Theme Inline Buttons for 2 Channels"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🔒 JOIN NETWORK 1", url=CHANNEL_1_LINK))
    markup.add(InlineKeyboardButton("🔒 JOIN NETWORK 2", url=CHANNEL_2_LINK))
    markup.add(InlineKeyboardButton("⚡ VERIFY CONNECTION", callback_data="verify_access"))
    return markup

def verify_markup():
    """Generate Verify Button"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("⚡ VERIFY NOW", callback_data="verify_access"))
    return markup

# =============== MESSAGE HANDLERS ===============
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    print(f"{CYAN}[LOG] Connection attempt by ID: {user_id}{RESET}")
    log_user_activity(user_id, "START_COMMAND", f"User started bot")

    # Check if already verified
    if is_user_verified(user_id):
        bot.send_message(user_id, f"""
✅ *VERIFIED USER* ✅
{DIVIDER}
Welcome back, `{first_name}`.

📡 *Status:* Verified
🛡️ *Security:* Active
⚡ *Privilege:* Full Access

`You can now use the main bot features.`
{DIVIDER}
""", parse_mode="Markdown")
        return

    # Check channel subscription
    if not is_user_subscribed_both(user_id):
        # ❌ ACCESS DENIED MESSAGE
        text = f"""
🚨 *SYSTEM BREACH DETECTED* 🚨
{DIVIDER}
❌ *ACCESS DENIED!* `Unidentified user attempting to access the mainframe. Protocol 404 engaged.`

🛡️ You must join BOTH encrypted networks to bypass this firewall.
{DIVIDER}
"""
        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=force_join_markup())
        print(f"{RED}[BLOCKED] Access Denied for ID: {user_id}{RESET}")
    else:
        # ✅ ACCESS GRANTED - Forward to main bot
        text = f"""
✅ *ACCESS GRANTED* ✅
{DIVIDER}
Welcome to the Mainframe, `{first_name}`.

📡 *Status:* Connected
🛡️ *Security:* Encrypted
⚡ *Privilege:* Admin Level 1

`Waiting for command execution...`
{DIVIDER}
"""
        bot.send_message(user_id, text, parse_mode="Markdown")
        add_verified_user(user_id)
        
        # Forward to group where main bot is
        try:
            bot.forward_message(GROUP_ID, message.chat.id, message.message_id)
            print(f"{GREEN}[FORWARD] User {user_id} forwarded to group{RESET}")
        except Exception as e:
            print(f"{RED}[ERROR] Forward Failed: {e}{RESET}")
        
        print(f"{GREEN}[GRANTED] Access Approved for ID: {user_id}{RESET}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Intercept all other messages if not joined"""
    user_id = message.from_user.id
    
    if not is_user_subscribed_both(user_id):
        bot.reply_to(message, "⚠️ *ERROR:* You cannot send messages until you bypass the firewall. Send /start", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"💻 *Command Received:* `{message.text}`\n_Executing..._", parse_mode="Markdown")

# =============== CALLBACK HANDLER ===============
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "verify_access":
        if not is_user_subscribed_both(user_id):
            bot.answer_callback_query(call.id, "❌ FIREWALL ACTIVE: You have not joined the network yet!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "✅ Verified! Access Granted", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            
            text = f"""
✅ *FIREWALL BYPASSED* ✅
{DIVIDER}
Welcome to the Mainframe, `{call.from_user.first_name}`.

📡 *Status:* Connected
🛡️ *Security:* Encrypted
⚡ *Privilege:* Admin Level 1

`Waiting for command execution...`
{DIVIDER}
"""
            bot.send_message(user_id, text, parse_mode="Markdown")
            add_verified_user(user_id)
            
            # Forward to group
            try:
                bot.forward_message(GROUP_ID, call.message.chat.id, call.message.message_id)
                print(f"{GREEN}[FORWARD] User {user_id} forwarded to group{RESET}")
            except Exception as e:
                print(f"{RED}[ERROR] Forward Failed: {e}{RESET}")

# =============== GROUP MESSAGE HANDLER ===============
@bot.message_handler(func=lambda message: message.chat.id == GROUP_ID)
def group_handler(message):
    """Handle messages from group (main bot detection)"""
    user_id = message.from_user.id
    add_verified_user(user_id)
    log_user_activity(user_id, "GROUP_JOIN", "User joined main bot group")
    print(f"{GREEN}[GROUP] User {user_id} verified from group{RESET}")

# =============== NEW MEMBER LOGGING ===============
@bot.message_handler(content_types=['new_chat_members'])
def new_member_handler(message):
    """Log when new members join the group"""
    if message.chat.id == GROUP_ID:
        for user in message.new_chat_members:
            user_id = user.id
            first_name = user.first_name
            username = user.username if user.username else "N/A"
            
            log_message = f"""
🎉 *NEW MEMBER JOINED* 🎉
{DIVIDER}
👤 *Name:* {first_name}
🆔 *ID:* {user_id}
🔗 *Username:* @{username}
📅 *Joined:* {time.strftime('%Y-%m-%d %H:%M:%S')}
{DIVIDER}
"""
            bot.send_message(PRIVATE_LOGS_ID, log_message, parse_mode="Markdown")
            print(f"{GREEN}[NEW MEMBER] {first_name} joined the group{RESET}")

# =============== CHECK SUBSCRIPTION COMMAND ===============
@bot.message_handler(commands=['check'])
def check_command(message):
    user_id = message.from_user.id
    
    if is_user_subscribed_both(user_id):
        bot.send_message(user_id, "✅ You are subscribed to both channels!")
    else:
        bot.send_message(user_id, "❌ You are not subscribed to both channels!")

# =============== ADMIN COMMAND ===============
@bot.message_handler(commands=['admin'])
def admin_command(message):
    # Check if user is admin (you can add admin list)
    if message.from_user.id == 123456789:  # Apna user ID yahan daalo
        bot.send_message(message.from_user.id, f"""
🛡️ *ADMIN PANEL* 🛡️
{DIVIDER}
📊 *Statistics:*
✅ Verified Users: {len(verified_users)}
📡 Bot Status: Active
{DIVIDER}
""", parse_mode="Markdown")
    else:
        bot.send_message(message.from_user.id, "❌ Access Denied!")

# =============== START BOT ===============
if __name__ == "__main__":
    print_banner()
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"{RED}CRITICAL ERROR: {e}{RESET}")
