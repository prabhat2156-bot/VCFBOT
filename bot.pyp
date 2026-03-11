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

# 🔑 Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

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
    text = (
        f"👋 **Namaste {user.first_name}!**\n\n"
        f"🤖 **Welcome to Ultimate VCF Manager**\n"
        f"I am your all-in-one assistant for managing contact files.\n\n"
        f"👇 **MAIN MENU**\nSelect an option to begin:"
    )
    # 🔴 FIX: Ek single message mein text aur buttons dono
    await update.message.reply_text(text, reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

async def buttons(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    ud = get_ud(uid)

    if q.data == "main_menu":
        clear_ud(uid)
        await q.message.edit_text("🤖 **MAIN MENU**\nSelect an option to begin:", reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

    elif q.data == "mysettings":
        await show_summary(q.message, ud["settings"])
    elif q.data == "reset":
        ud["settings"] = DEFAULT_SETTINGS.copy()
        await q.message.edit_text("♻️ **Settings Reset to Default.**", reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

    elif q.data in ["analysis", "split_vcf"]:
        clear_ud(uid)
        ud["mode"] = q.data; ud["step"] = "upload"
        prompts = {
            "analysis": "🧐 **FILE ANALYSIS**\n\nUpload a file (TXT, VCF, CSV, XLSX) to see statistics.",
            "split_vcf": "✂️ **SPLIT FILE**\n\nUpload the file (VCF/TXT/CSV/XLSX) you want to split."
        }
        await q.message.edit_text(prompts[q.data], reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data in ["converter", "vcf_editor", "merge", "rename_files", "rename_contacts"]:
        clear_ud(uid)
        ud["mode"] = q.data; ud["step"] = "upload"
        msg = f"📤 **BULK UPLOAD MODE**\n\nUpload your files now. When you are finished, click **DONE UPLOADING**."
        await q.message.edit_text(msg, reply_markup=done_upload_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data == "done_uploading":
        if not ud["files"]: return await q.message.reply_text("❌ Please upload at least 1 file first!", reply_markup=done_upload_kb())

        ud["upload_msg"] = None
        file_count = len(ud["files"])

        # 🔴 FIX: Agar sirf 1 file hai, to "Merge/Single" mat pucho
        if file_count == 1:
            ud["merge_choice"] = "single"
            if ud["mode"] == "converter":
                ud["step"] = "ask_format"
                await q.message.edit_text("🔄 **Choose Target Format:**", reply_markup=convert_kb(), parse_mode=ParseMode.MARKDOWN)
            elif ud["mode"] == "vcf_editor":
                ud["step"] = "ask_action"
                await q.message.edit_text("🛠️ **Choose Action:**", reply_markup=editor_action_kb(), parse_mode=ParseMode.MARKDOWN)
            elif ud["mode"] == "rename_files":
                ud["step"] = "ask_name"
                await q.message.edit_text("✏️ Enter **New File Name**:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)
            elif ud["mode"] == "rename_contacts":
                ud["step"] = "ask_name"
                await q.message.edit_text("👤 Enter **New Contact Base Name**\n*(Note: Your file's original name will not change)*:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)
            elif ud["mode"] == "merge":
                ud["merge_choice"] = "merge"
                ud["step"] = "ask_name"
                await q.message.edit_text("✏️ Enter **New Base Name** for Output:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

        # Agar 1 se zyada file hai, tab pucho
        else:
            if ud["mode"] == "merge":
                ud["merge_choice"] = "merge"
                ud["step"] = "ask_name"
                await q.message.edit_text("✏️ Enter **New Base Name** for Merged Output:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)
            else:
                ud["step"] = "ask_merge"
                await q.message.edit_text("❓ **Merge or Single?**\n\nDo you want to combine all uploaded files into ONE, or process them individually?", reply_markup=merge_single_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data in ["choice_merge", "choice_single"]:
        ud["merge_choice"] = q.data.split("_")[1]
        if ud["mode"] == "converter":
            ud["step"] = "ask_format"
            await q.message.edit_text("🔄 **Choose Target Format:**", reply_markup=convert_kb(), parse_mode=ParseMode.MARKDOWN)
        elif ud["mode"] == "vcf_editor":
            ud["step"] = "ask_action"
            await q.message.edit_text("🛠️ **Choose Action:**", reply_markup=editor_action_kb(), parse_mode=ParseMode.MARKDOWN)
        elif ud["mode"] == "rename_files":
            ud["step"] = "ask_name"
            await q.message.edit_text("✏️ Enter **New File Name**:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)
        elif ud["mode"] == "rename_contacts":
            ud["step"] = "ask_name"
            await q.message.edit_text("👤 Enter **New Contact Base Name**\n*(Note: Your file's original name will not change)*:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data.startswith("cv_"):
        ud["format"] = q.data.split("_")[1]; ud["step"] = "ask_name"
        await q.message.edit_text("⌨️ Enter **Custom File Name** for Output:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data.startswith("edit_"):
        ud["action"] = q.data.split("_")[1]; ud["step"] = "ask_numbers"
        msg = "✍️ **Send Numbers to ADD:**" if ud["action"] == "add" else "🗑️ **Send Number to REMOVE:**"
        await q.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())

    elif q.data == "gen":
        clear_ud(uid)
        ud["mode"] = "gen"; ud["step"] = "file_name"
        await q.message.edit_text("📇 **PRO GENERATOR**\n\n⌨️ Enter **File Name**:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data == "gen_done":
        ud["step"] = "waiting_input"
        await q.message.edit_text("🔒 **Settings Locked.**\n\n📂 **Upload your file now** (TXT, VCF, CSV, XLSX)", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data == "skip_cc":
        ud["settings"]["country_code"] = ""
        ud["step"] = "group_number"
        await q.message.edit_text("📑 Enter **Group Name** (or Skip):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏩ SKIP", callback_data="skip_group"), InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]]), parse_mode=ParseMode.MARKDOWN)

    elif q.data == "skip_group":
        ud["settings"]["group_number"] = None; await show_summary(q.message, ud["settings"])

    elif q.data == "quick_vcf":
        clear_ud(uid)
        ud["mode"] = "quick"; ud["step"] = "file"
        ud["quick_data"] = []
        await q.message.edit_text("⚡ **QUICK VCF MODE**\n\n⌨️ Enter a filename for your VCF:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif q.data == "add_more_quick":
        ud["step"] = "contact"
        await q.message.edit_text("👤 Enter **Next Contact Name**:", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())

    elif q.data == "finish_quick":
        f_name = ud.get("custom_name", "QuickVCF")
        proc_msg = await q.message.reply_text("⏳ **Generating VCF...**", parse_mode=ParseMode.MARKDOWN)
        out, total_nums = "", 0
        for entry in ud["quick_data"]:
            c_name = entry['contact']
            for i, n in enumerate(entry['nums'], start=1):
                clean_n = "+" + n.replace("+", "")
                out += f"BEGIN:VCARD\nVERSION:3.0\nFN:{c_name}{str(i).zfill(3)}\nTEL;TYPE=CELL:{clean_n}\nEND:VCARD\n"
                total_nums += 1

        path = f"{f_name}.vcf"
        with open(path, "w", encoding="utf-8") as x: x.write(out)
        await proc_msg.delete()
        await q.message.reply_document(open(path, "rb"), caption=f"✅ **Done!**\nTotal Contacts: {total_nums}", parse_mode=ParseMode.MARKDOWN)
        os.remove(path); clear_ud(uid)
        await q.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())

    elif q.data == "name_gen":
        clear_ud(uid)
        ud["mode"] = "name_gen"; ud["step"] = "name"
        await q.message.edit_text("📝 **NAME GENERATOR**\n\n✏️ Enter Base Name (e.g. `Customer`):", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = get_ud(uid)
    cfg = ud["settings"]
    txt = update.message.text.strip()

    if ud["mode"] == "gen":
        if ud["step"] == "file_name":
            cfg["file_name"] = txt; ud["step"] = "contact_name"
            await update.message.reply_text("👤 Enter **Contact Name**:", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())
        elif ud["step"] == "contact_name":
            cfg["contact_name"] = txt; ud["step"] = "limit"
            await update.message.reply_text("📊 Enter **Limit Per File** (e.g. 100):", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())
        elif ud["step"] == "limit":
            cfg["limit"] = int(txt) if txt.isdigit() else 100; ud["step"] = "contact_start"
            await update.message.reply_text("🔢 Enter **Start Number** (e.g. 1):", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())
        elif ud["step"] == "contact_start":
            cfg["contact_start"] = int(txt) if txt.isdigit() else 1; ud["step"] = "vcf_start"
            await update.message.reply_text("📄 Enter **VCF File Start Index**:", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())
        elif ud["step"] == "vcf_start":
            cfg["vcf_start"] = int(txt) if txt.isdigit() else 1; ud["step"] = "country_code"
            await update.message.reply_text("🌍 Enter **Country Code** (e.g. +91) or Skip:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏩ AUTO DETECT", callback_data="skip_cc"), InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]]), parse_mode=ParseMode.MARKDOWN)
        elif ud["step"] == "country_code":
            cfg["country_code"] = txt if txt.startswith("+") else f"+{txt}"; ud["step"] = "group_number"
            await update.message.reply_text("📑 Enter **Group Name**:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏩ SKIP", callback_data="skip_group"), InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]]), parse_mode=ParseMode.MARKDOWN)
        elif ud["step"] == "group_number":
            cfg["group_number"] = txt; await show_summary(update.message, cfg)

    elif ud["step"] == "ask_split_limit":
        if txt.isdigit():
            ud["split_limit"] = int(txt); ud["step"] = "ask_name"
            await update.message.reply_text("⌨️ Enter **Custom File Name** for split files:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif ud["step"] == "ask_numbers":
        ud["edit_nums"] = list(dict.fromkeys(re.findall(r"\d{7,}", txt))); ud["step"] = "ask_name"
        await update.message.reply_text("⌨️ Enter **Custom File Name** for Output:", reply_markup=cancel_kb(), parse_mode=ParseMode.MARKDOWN)

    elif ud["step"] == "ask_name":
        ud["custom_name"] = re.sub(r'[\\/*?:"<>|]', "", txt)
        await process_engine(update, ctx, uid, ud)

    elif ud["mode"] == "quick" and ud["step"] == "file":
        ud["custom_name"] = txt; ud["step"] = "contact"
        await update.message.reply_text("👤 Enter **Contact Name**:", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())
    elif ud["mode"] == "quick" and ud["step"] == "contact":
        ud["contact"] = txt; ud["step"] = "numbers"
        await update.message.reply_text(f"📤 Paste Numbers for **'{txt}'**:", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())
    elif ud["mode"] == "quick" and ud["step"] == "numbers":
        raw_nums = re.findall(r"\d{7,}", txt)
        ud["quick_data"].append({"contact": ud["contact"], "nums": list(set(raw_nums))})
        await update.message.reply_text(f"✅ Added {len(set(raw_nums))} numbers.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ ADD MORE", callback_data="add_more_quick"), InlineKeyboardButton("🏁 FINISH", callback_data="finish_quick"), InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]]))

    elif ud["mode"] == "name_gen":
        if ud["step"] == "name":
            ud["base_name"] = txt; ud["step"] = "count"
            await update.message.reply_text("🔢 How many names?", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())
        elif ud["step"] == "count" and txt.isdigit():
            proc_msg = await update.message.reply_text("⏳ **Generating List...**", parse_mode=ParseMode.MARKDOWN)
            count = int(txt)
            content = "\n".join([f"{ud['base_name']} {i+1}" for i in range(count)])
            await proc_msg.delete()
            if len(content) > 4000:
                with open("names.txt", "w") as f: f.write(content)
                await update.message.reply_document(open("names.txt", "rb"))
                os.remove("names.txt")
            else:
                await update.message.reply_text(f"📝 **GENERATED LIST:**\n\n```\n{content}\n```", parse_mode=ParseMode.MARKDOWN)
            clear_ud(uid); await update.message.reply_text("✅ **Task Done.**", reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

async def handle_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ud = get_ud(uid)
    doc = update.message.document

    if ud["step"] not in ["upload", "waiting_input"]:
        return await update.message.reply_text("❌ Please select an option from the menu first.", reply_markup=main_menu())

    path = f"{uid}_{len(ud['files'])}_{doc.file_name}"
    file_obj = await ctx.bot.get_file(doc.file_id)
    await file_obj.download_to_drive(path)
    ud["files"].append(path)

    if ud["mode"] == "analysis":
        proc_msg = await update.message.reply_text("⏳ **Analyzing...**", parse_mode=ParseMode.MARKDOWN)
        nums = extract_all_numbers(path)
        report = generate_analysis_report(doc.file_name, nums)
        await proc_msg.delete()
        await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())
        clear_ud(uid)

    elif ud["mode"] == "split_vcf":
        ud["step"] = "ask_split_limit"
        nums = extract_all_numbers(path)
        ud["split_nums"] = nums
        await update.message.reply_text(f"📊 Found **{len(nums)}** numbers.\nEnter Limit per file (e.g. 100):", parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb())

    elif ud["mode"] == "gen" and ud["step"] == "waiting_input":
        proc_msg = await update.message.reply_text("⚙️ **Processing VCF Generator...**", parse_mode=ParseMode.MARKDOWN)
        cfg = ud["settings"]
        nums = extract_all_numbers(path)
        detected_country = "Manual"
        if not cfg["country_code"]: detected_country = detect_primary_country(nums)

        generated_files = []
        for i, c in enumerate(chunk(nums, cfg["limit"])):
            f = make_vcf(c, cfg, i)
            await update.message.reply_document(open(f, "rb"))
            generated_files.append(f)
            await asyncio.sleep(0.3)

        await proc_msg.delete()
        summary = (
            f"✅ **GENERATION COMPLETE**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📂 File Name: `{cfg['file_name']}`\n"
            f"🔢 Total: `{len(nums)}` | 📁 Files: `{len(generated_files)}`\n"
            f"🌍 Detect: `{detected_country}`\n"
        )
        await update.message.reply_text(summary, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())
        for f in generated_files:
            if os.path.exists(f): os.remove(f)
        clear_ud(uid)

    else:
        text = f"📥 **Files Uploaded:** `{len(ud['files'])}`\n📄 **Latest:** `{doc.file_name}`\n\n👇 Send more files or click **DONE UPLOADING**."
        if not ud.get("upload_msg"):
            ud["upload_msg"] = await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=done_upload_kb())
        else:
            try:
                await ud["upload_msg"].edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=done_upload_kb())
            except Exception:
                pass

async def process_engine(update, ctx, uid, ud):
    proc_msg = await update.message.reply_text("⏳ **Processing Files... Please wait!**", parse_mode=ParseMode.MARKDOWN)

    try:
        mode = ud["mode"]
        merge_choice = ud["merge_choice"]
        c_name = ud["custom_name"]
        file_count = len(ud["files"])

        # ======== SPLIT ========
        if mode == "split_vcf":
            nums = ud["split_nums"]
            limit = ud["split_limit"]
            orig_fmt = get_file_format(ud["files"][0]) if ud["files"] else "vcf"

            for i, p in enumerate(chunk(nums, limit), start=1):
                out_name = f"{c_name}{i}.{orig_fmt}"
                f = save_format(p, orig_fmt, out_name, ud["settings"])
                await update.message.reply_document(open(f, "rb"))
                os.remove(f)
                await asyncio.sleep(0.3)
            await proc_msg.delete()
            await update.message.reply_text("✅ **Split Complete.**", reply_markup=main_menu())
            clear_ud(uid)
            return

        # ======== MERGE LOGIC ========
        if merge_choice == "merge" or mode == "merge":
            all_nums = []

            if mode == "rename_contacts":
                for f in ud["files"]: all_nums.extend(extract_all_numbers(f))
                ud["settings"]["contact_name"] = c_name
                out_file = make_vcf(list(dict.fromkeys(all_nums)), ud["settings"], custom_limit=len(all_nums), custom_fname=f"{c_name}.vcf")
                await update.message.reply_document(open(out_file, "rb"))
                os.remove(out_file)

            elif mode == "rename_files":
                for f in ud["files"]: all_nums.extend(extract_all_numbers(f))
                out_file = make_vcf(list(dict.fromkeys(all_nums)), ud["settings"], custom_limit=len(all_nums), custom_fname=f"{c_name}.vcf")
                await update.message.reply_document(open(out_file, "rb"))
                os.remove(out_file)

            else:
                for f in ud["files"]:
                    all_nums.extend(extract_all_numbers(f))
                all_nums = list(dict.fromkeys(all_nums))

                if mode in ["converter", "merge"]:
                    if mode == "converter":
                        fmt = ud["format"] if ud["format"] else "vcf"
                    else:
                        fmt = get_file_format(ud["files"][0]) if ud["files"] else "vcf"

                    out_file = save_format(all_nums, fmt, f"{c_name}.{fmt}", ud["settings"])
                    await update.message.reply_document(open(out_file, "rb"))
                    os.remove(out_file)

                elif mode == "vcf_editor":
                    if ud["action"] == "add":
                        all_nums.extend(ud["edit_nums"])
                        all_nums = list(dict.fromkeys(all_nums))
                    elif ud["action"] == "remove":
                        remove_set = set([n.replace("+","") for n in ud["edit_nums"]])
                        all_nums = [n for n in all_nums if n.replace("+","") not in remove_set]
                    out_file = make_vcf(all_nums, ud["settings"], custom_limit=len(all_nums), custom_fname=f"{c_name}.vcf")
                    await update.message.reply_document(open(out_file, "rb"))
                    os.remove(out_file)

        # ======== SINGLE LOGIC ========
        elif merge_choice == "single":
            for i, fpath in enumerate(ud["files"], start=1):
                # Ek file thi to direct c_name use karo, warna c_name + number
                single_name = c_name if file_count == 1 else f"{c_name}{i}"

                # Fetch original filename accurately
                orig_name = fpath.split("_", 2)[-1]
                orig_ext = os.path.splitext(orig_name)[1]

                if mode == "rename_files":
                    # 🔴 FIX: Rename File sirf file rename karega, data nahi chhedega
                    new_name = f"{single_name}{orig_ext}"
                    os.rename(fpath, new_name)
                    await update.message.reply_document(open(new_name, "rb"))
                    os.remove(new_name)

                elif mode == "rename_contacts":
                    # 🔴 FIX: File name bilkul Original rahega, sirf andar ke contact change honge
                    out_text, idx = "", 1
                    with open(fpath, "r", errors="ignore") as r:
                        for line in r:
                            if line.startswith("FN:"):
                                out_text += f"FN:{c_name}{str(idx).zfill(3)}\n"; idx += 1
                            else: out_text += line
                    # Using exactly original name for output
                    with open(orig_name, "w", encoding="utf-8") as w: w.write(out_text)
                    await update.message.reply_document(open(orig_name, "rb"))
                    os.remove(orig_name)

                elif mode == "converter":
                    nums = extract_all_numbers(fpath)
                    out_file = save_format(nums, ud["format"], f"{single_name}.{ud['format']}", ud["settings"])
                    await update.message.reply_document(open(out_file, "rb"))
                    os.remove(out_file)

                elif mode == "vcf_editor":
                    nums = extract_all_numbers(fpath)
                    if ud["action"] == "add":
                        nums.extend(ud["edit_nums"])
                    elif ud["action"] == "remove":
                        remove_set = set([n.replace("+","") for n in ud["edit_nums"]])
                        nums = [n for n in nums if n.replace("+","") not in remove_set]
                    out_file = make_vcf(list(dict.fromkeys(nums)), ud["settings"], custom_limit=len(nums), custom_fname=f"{single_name}.vcf")
                    await update.message.reply_document(open(out_file, "rb"))
                    os.remove(out_file)

                await asyncio.sleep(0.3)

        await proc_msg.delete()
        await update.message.reply_text("✅ **All Files Processed Successfully!**", reply_markup=main_menu())
        clear_ud(uid)

    except Exception as e:
        await proc_msg.delete()
        await update.message.reply_text(f"❌ Error occurred: {e}", reply_markup=main_menu())
        clear_ud(uid)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("🚀 PREMIUM BOT STARTED: AUTO-SKIP MERGE PROMPT & FILE RENAME FIXED")
    app.run_polling()
