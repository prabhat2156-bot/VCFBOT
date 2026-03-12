#!/usr/bin/env python3
# ==================================================
#    💀 CYBER MAINFRAME - VCF MANAGER WITH VERIFICATION 💀
#    ⚡ ALL IN ONE FILE - VERIFICATION + FEATURES 💀
# ==================================================

import os
import re
import asyncio
import pandas as pd
import phonenumbers
from phonenumbers import geocoder, carrier
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

# =============== LOAD ENVIRONMENT VARIABLES ===============
load_dotenv()

# 🔑 Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================= CHANNEL CONFIG =================
CHANNEL_1_ID = os.getenv("CHANNEL_1_ID")
CHANNEL_1_LINK = os.getenv("CHANNEL_1_LINK")
CHANNEL_2_ID = os.getenv("CHANNEL_2_ID")
CHANNEL_2_LINK = os.getenv("CHANNEL_2_LINK")

# ================= SETTINGS =================
DEFAULT_SETTINGS = {
    "file_name": "Contacts",
    "contact_name": "Contact",
    "limit": 100,
    "contact_start": 1,
    "vcf_start": 1,
    "country_code": "",
    "group_number": None,
}

users_data = {}

def get_ud(uid):
    if uid not in users_data:
        users_data[uid] = {
            "mode": None, "step": None, "files": [],
            "merge_choice": None, "format": None, "action": None,
            "edit_nums": [], "custom_name": "Output", "split_limit": 100,
            "quick_data": [], "upload_msg": None, "settings": DEFAULT_SETTINGS.copy()
        }
    return users_data[uid]

def clear_ud(uid):
    if uid in users_data:
        for f in users_data[uid].get("files", []):
            if os.path.exists(f):
                try: os.remove(f)
                except: pass
        users_data[uid]["files"] = []
        users_data[uid]["mode"] = None
        users_data[uid]["step"] = None
        users_data[uid]["merge_choice"] = None
        users_data[uid]["upload_msg"] = None

# ================= VERIFICATION CHECK =================
async def check_channel_membership(bot, user_id):
    """Check if user is in BOTH channels"""
    try:
        status1 = await bot.get_chat_member(CHANNEL_1_ID, user_id)
        status2 = await bot.get_chat_member(CHANNEL_2_ID, user_id)
        
        if status1.status not in ['member', 'administrator', 'creator']:
            return False
        if status2.status not in ['member', 'administrator', 'creator']:
            return False
        return True
    except Exception as e:
        print(f"[ERROR] Channel check failed: {e}")
        return False

def force_join_markup():
    """Generate Join Buttons"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🔒 JOIN NETWORK 1", url=CHANNEL_1_LINK))
    markup.add(InlineKeyboardButton("🔒 JOIN NETWORK 2", url=CHANNEL_2_LINK))
    markup.add(InlineKeyboardButton("⚡ VERIFY CONNECTION", callback_data="verify_access"))
    return markup

# ================= HELPERS =================
def get_file_format(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt": return "txt"
    if ext == ".csv": return "csv"
    if ext in [".xlsx", ".xls"]: return "xlsx"
    return "vcf"

def extract_all_numbers(path):
    ext = os.path.splitext(path)[1].lower()
    nums = []
    try:
        if ext == ".vcf":
            with open(path, "r", errors="ignore") as f:
                for line in f:
                    if line.startswith("TEL"):
                        n = re.sub(r"[^\d+]", "", line)
                        if len(n) >= 7: nums.append(n)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(path, dtype=str)
            text_data = " ".join(df.values.flatten().astype(str))
            nums = re.findall(r"\+?\d{7,}", text_data)
        elif ext == ".csv":
            df = pd.read_csv(path, dtype=str)
            text_data = " ".join(df.values.flatten().astype(str))
            nums = re.findall(r"\+?\d{7,}", text_data)
        else:
            with open(path, "r", errors="ignore") as f:
                nums = re.findall(r"\+?\d{7,}", f.read())
    except Exception as e:
        print(f"Error extracting: {e}")
        return []
    return list(dict.fromkeys(nums))

def detect_primary_country(numbers):
    countries = {}
    for n in numbers[:50]:
        try:
            parse_num = "+" + n if not n.startswith("+") else n
            pn = phonenumbers.parse(parse_num, None)
            region = geocoder.description_for_number(pn, "en")
            if region: countries[region] = countries.get(region, 0) + 1
        except: continue
    if countries: return max(countries, key=countries.get)
    return "Unknown"

def generate_analysis_report(file_name, numbers):
    total = len(numbers)
    unique_set = set(numbers)
    unique_count = len(unique_set)
    duplicates = total - unique_count

    country_stats = {}
    invalid_count = 0
    for n in unique_set:
        try:
            parse_num = "+" + n if not n.startswith("+") else n
            pn = phonenumbers.parse(parse_num, None)
            if phonenumbers.is_valid_number(pn):
                region = geocoder.description_for_number(pn, "en") or "Unknown"
                country_stats[region] = country_stats.get(region, 0) + 1
            else: invalid_count += 1
        except: invalid_count += 1

    country_text = "\n".join([f"  └ {c}: {count}" for c, count in country_stats.items()])
    if not country_text: country_text = "  └ None detected"

    report = (
        f"📊 **FILE ANALYSIS REPORT**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 **File:** `{file_name}`\n\n"
        f"📌 **Statistics:**\n"
        f"  ├ 🔢 Total Numbers: `{total}`\n"
        f"  ├ ✅ Unique: `{unique_count}`\n"
        f"  └ ♻️ Duplicates: `{duplicates}`\n\n"
        f"🌍 **Country Breakdown:**\n"
        f"{country_text}\n\n"
        f"⚠️ **Issues:**\n"
        f"  └ ❌ Invalid/Junk: `{invalid_count}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    return report

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def make_vcf(numbers, cfg, index=0, custom_limit=None, custom_fname=None):
    limit = custom_limit if custom_limit else cfg["limit"]
    start = cfg["contact_start"] + index * limit
    out = ""
    for i, n in enumerate(numbers, start=start):
        name = f"{cfg['contact_name']}{str(i).zfill(3)}"
        if cfg.get("group_number"): name += f" ({cfg['group_number']})"
        clean_n = n.replace("+", "")
        prefix = cfg["country_code"] if cfg["country_code"] else "+"
        final_num = f"{prefix}{clean_n}"
        out += f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL;TYPE=CELL:{final_num}\nEND:VCARD\n"

    fname = custom_fname if custom_fname else f"{cfg['file_name']}{cfg['vcf_start'] + index}.vcf"
    with open(fname, "w", encoding="utf-8") as f: f.write(out)
    return fname

def save_format(numbers, target_fmt, out_file, cfg):
    if target_fmt == "vcf":
        return make_vcf(numbers, cfg, custom_limit=len(numbers), custom_fname=out_file)
    elif target_fmt == "txt":
        with open(out_file, "w") as f: f.write("\n".join(["+" + n.replace("+","") for n in numbers]))
    elif target_fmt == "csv":
        pd.DataFrame(["+" + n.replace("+","") for n in numbers], columns=["Mobile Number"]).to_csv(out_file, index=False)
    elif target_fmt == "xlsx":
        pd.DataFrame(["+" + n.replace("+","") for n in numbers], columns=["Mobile Number"]).to_excel(out_file, index=False)
    return out_file

# ================= UI & MENUS =================
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📂 FILE ANALYSIS", callback_data="analysis"),
            InlineKeyboardButton("🔄 FILE CONVERTER", callback_data="converter")
        ],
        [
            InlineKeyboardButton("⚡ QUICK VCF", callback_data="quick_vcf"),
            InlineKeyboardButton("📇 VCF GENERATOR", callback_data="gen")
        ],
        [
            InlineKeyboardButton("✂️ SPLIT VCF", callback_data="split_vcf"),
            InlineKeyboardButton("🧩 MERGE FILES", callback_data="merge")
        ],
        [
            InlineKeyboardButton("🛠️ FILE EDITOR", callback_data="vcf_editor"),
            InlineKeyboardButton("📝 NAME MAKER", callback_data="name_gen")
        ],
        [
            InlineKeyboardButton("✏️ RENAME FILE", callback_data="rename_files"),
            InlineKeyboardButton("✏️ RENAME CONTACT", callback_data="rename_contacts")
        ],
        [
            InlineKeyboardButton("⚙️ SETTINGS", callback_data="mysettings"),
            InlineKeyboardButton("🗑 RESET", callback_data="reset")
        ]
    ])

def cancel_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]])

def done_upload_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ DONE UPLOADING", callback_data="done_uploading")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]
    ])

def merge_single_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧩 MERGE ALL", callback_data="choice_merge")],
        [InlineKeyboardButton("📄 KEEP SINGLE", callback_data="choice_single")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]
    ])

def convert_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 TO TXT", callback_data="cv_txt"), InlineKeyboardButton("📇 TO VCF", callback_data="cv_vcf")],
        [InlineKeyboardButton("📊 TO CSV", callback_data="cv_csv"), InlineKeyboardButton("📑 TO XLSX", callback_data="cv_xlsx")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]
    ])

def editor_action_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ADD", callback_data="edit_add"), InlineKeyboardButton("❌ REMOVE", callback_data="edit_remove")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]
    ])

async def show_summary(msg, cfg):
    c_disp = cfg['country_code'] if cfg['country_code'] else "🤖 Auto-Detect"
    g_disp = cfg['group_number'] if cfg['group_number'] else "❌ None"

    text = (
        "⚙️ **CURRENT SETTINGS (VCF Generator)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📂 **File Name:** `{cfg['file_name']}`\n"
        f"👤 **Contact Name:** `{cfg['contact_name']}`\n"
        f"📏 **Limit Per File:** `{cfg['limit']}`\n"
        f"🔢 **Start Index:** `{cfg['contact_start']}`\n"
        f"📄 **VCF Start Index:** `{cfg['vcf_start']}`\n"
        f"🌍 **Country Code:** `{c_disp}`\n"
        f"🏷 **Group Tag:** `{g_disp}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👇 *Ready to process?*"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ START PROCESS", callback_data="gen_done")],
        [InlineKeyboardButton("✏️ EDIT SETTINGS", callback_data="gen")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]
    ])
    if hasattr(msg, 'edit_text'):
        await msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        await msg.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ================= HANDLERS =================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # 🔴 CHECK VERIFICATION FIRST
    if not await check_channel_membership(ctx.bot, user_id):
        text = (
            "🚨 **SYSTEM BREACH DETECTED** 🚨\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "❌ **ACCESS DENIED!**\n\n"
            "You must join BOTH channels to use this bot.\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        await update.message.reply_text(text, reply_markup=force_join_markup(), parse_mode=ParseMode.MARKDOWN)
        return
    
    # ✅ VERIFIED - Show Welcome + Features
    text = (
        f"👋 **Namaste {user.first_name}!**\n\n"
        f"🤖 **Welcome to Ultimate VCF Manager**\n"
        f"I am your all-in-one assistant for managing contact files.\n\n"
        f"👇 **MAIN MENU**\nSelect an option to begin:"
    )
    await update.message.reply_text(text, reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

async def buttons(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    ud = get_ud(uid)
