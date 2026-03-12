import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import os
import bot  # 👈 tumhara main bot file

# =============== TERMINAL COLORS ===============
GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

# =============== BOT CONFIG ===============

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = "@Madarawswork"
CHANNEL_LINK = "https://t.me/Madarawswork"

CHANNEL2_ID = "@madarachatgroup"
CHANNEL2_LINK = "https://t.me/madarachatgroup"

OWNER_ID = 8395315423  # 👈 owner telegram id

DIVIDER = "✦ ━━━━━━━━━━━━━━━━━━━━ ✦"

bot = telebot.TeleBot(BOT_TOKEN)

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{CYAN}{BOLD}{'='*50}{RESET}")
    print(f"{GREEN}{BOLD}    💀 CYBER MAINFRAME INITIATED 💀{RESET}")
    print(f"{RED}{BOLD}    🚨 FORCE JOIN GATEWAY ACTIVE 🚨{RESET}")
    print(f"{CYAN}{BOLD}{'='*50}{RESET}")
    print(f"{YELLOW}📡 Target Channels: {CHANNEL_ID} , {CHANNEL2_ID}{RESET}")
    print(f"{GREEN}✅ Bot is listening for incoming connections...{RESET}\n")

# =============== FORCE JOIN LOGIC ===============
def is_user_subscribed(user_id):
    try:
        ch1 = bot.get_chat_member(CHANNEL_ID, user_id).status
        ch2 = bot.get_chat_member(CHANNEL2_ID, user_id).status

        if ch1 in ['left','kicked'] or ch2 in ['left','kicked']:
            return False
        return True

    except Exception as e:
        print(f"{RED}[ERROR] API Check Failed: {e}{RESET}")
        return False


def force_join_markup():
    markup = InlineKeyboardMarkup(row_width=1)

    markup.add(InlineKeyboardButton("💀 JOIN CHANNEL 1", url=CHANNEL_LINK))
    markup.add(InlineKeyboardButton("💀 JOIN CHANNEL 2", url=CHANNEL2_LINK))
    markup.add(InlineKeyboardButton("⚡ VERIFY CONNECTION", callback_data="verify_access"))

    return markup


# =============== MESSAGE HANDLERS ===============
@bot.message_handler(commands=['start'])
def start_command(message):

    user_id = message.from_user.id
    first_name = message.from_user.first_name

    print(f"{CYAN}[LOG] Connection attempt by ID: {user_id}{RESET}")

    if not is_user_subscribed(user_id):

        text = f"""
🚨 *SYSTEM BREACH DETECTED* 🚨
{DIVIDER}
❌ *ACCESS DENIED!* 

🛡️ Join both encrypted networks to bypass firewall.
{DIVIDER}
"""

        bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=force_join_markup())
        print(f"{RED}[BLOCKED] Access Denied for ID: {user_id}{RESET}")

    else:

        text = f"""
✅ *ACCESS GRANTED* ✅
{DIVIDER}
Welcome to the Mainframe, `{first_name}`.

📡 Status: Connected
🛡️ Security: Encrypted
⚡ Privilege: Admin Level 1

`Waiting for command execution...`
{DIVIDER}
"""

        bot.send_message(user_id, text, parse_mode="Markdown")

        # 👇 OWNER NOTIFICATION
        bot.send_message(
            OWNER_ID,
            f"🔔 New User Got Access\n\n👤 Name: {first_name}\n🆔 ID: {user_id}"
        )

        print(f"{GREEN}[GRANTED] Access Approved for ID: {user_id}{RESET}")


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):

    user_id = message.from_user.id

    if not is_user_subscribed(user_id):

        bot.reply_to(message, "⚠️ ERROR: Send /start and join channels first")
        bot.delete_message(message.chat.id, message.message_id)

    else:
        bot.reply_to(message, f"💻 Command Received: {message.text}")


# =============== CALLBACK HANDLER ===============
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    user_id = call.from_user.id

    if call.data == "verify_access":

        if not is_user_subscribed(user_id):

            bot.answer_callback_query(
                call.id,
                "❌ Join both channels first!",
                show_alert=True
            )

        else:

            bot.delete_message(call.message.chat.id, call.message.message_id)

            text = f"""
✅ *FIREWALL BYPASSED* ✅
{DIVIDER}
Welcome `{call.from_user.first_name}`

Access Granted.
{DIVIDER}
"""

            bot.send_message(user_id, text, parse_mode="Markdown")

            # 👇 OWNER MESSAGE
            bot.send_message(
                OWNER_ID,
                f"🔔 User Verified\n\n👤 {call.from_user.first_name}\n🆔 {user_id}"
            )


# =============== START BOT ===============
if __name__ == "__main__":

    print_banner()

    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)

    except Exception as e:
        print(f"{RED}CRITICAL ERROR: {e}{RESET}")
