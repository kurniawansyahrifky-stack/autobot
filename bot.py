import os
import requests
import time
import threading
import asyncio
import json
import re
import random   # 🔥 WAJIB
import html     # 🔥 biar ga error escape

from queue import Queue
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telethon import TelegramClient
import database4

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

TOKEN = "8621144366:AAFp7751PPtXsRv2IJ54C9klumMWcijY810"
API_URL = "http://127.0.0.1:5000/get"
TARGET_CHATS = [-1002208118831]
FORCE_GROUP = -1002208118831   # 🔥 WAJIB (buat cek join)
FORCE_LINK = "https://t.me/officiallgarfieldgrub"

OWNER_IDS = [8209644174, 6479082885]
PARTNER_FILE = "partner.json7"
SETTING_FILE = "setting.json7"

api_id = 33370509
api_hash = "669af6caebf2aca264b16cf8b40d37b2"
client = TelegramClient("session_new7", api_id, api_hash)

task_queue = Queue()
running_task = False  # 🔥 ANTI DOUBLE TASK

# ================= SETTING =================


def load_setting():
    try:
        with open(SETTING_FILE, "r") as f:
            return json.load(f)
    except BaseException:
        return {}


def save_setting(data):
    with open(SETTING_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================= FILE =================

def load_partner():
    if not os.path.exists(PARTNER_FILE):
        return []
    try:
        with open(PARTNER_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print("❌ load error:", e)
        return []


def save_partner(data):
    try:
        with open(PARTNER_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print("✅ KE SAVE:", data)
    except Exception as e:
        print("❌ save error:", e)


# ================= UTIL =================

def normalize_link(link):
    link = link.strip()
    link = link.replace("https://", "").replace("http://", "")
    link = link.replace("t.me/", "")
    return link.lower()


def get_group_name(link):
    username = normalize_link(link)

    # 1. TELETHON (kalau ada cache)
    try:
        entity = loop.run_until_complete(client.get_entity(username))
        if entity.title:
            return entity.title
    except Exception as e:
        print("❌ telethon fail:", e)

    # 2. SCRAPE PREVIEW (kayak Telegram preview)
    try:
        url = f"https://t.me/{username}"
        res = requests.get(url, timeout=5)

        match = re.search(r'<meta property="og:title" content="([^"]+)"', res.text)
        if match:
            return match.group(1)

    except Exception as e:
        print("❌ scrape fail:", e)

    return "Unknown Group"


# ================= COMMAND =================

def add_partner(update, context):
    if update.effective_user.id not in OWNER_IDS:
        return

    try:
        link = context.args[0]
    except BaseException:
        update.message.reply_text("❌   format: /addpartner link")
        return

    username = normalize_link(link)
    data = load_partner()

    for p in data:
        if p["username"] == username:
            update.message.reply_text("⚠️ sudah ada")
            return

    name = get_group_name(link)

    data.append({
        "link": f"https://t.me/{username}",
        "username": username,
        "name": name
    })

    save_partner(data)
    update.message.reply_text(f"✅ Partner ditambah:\n{name}")


def del_partner(update, context):
    if update.effective_user.id not in OWNER_IDS:
        return

    try:
        link = context.args[0]
    except BaseException:
        update.message.reply_text("❌   format: /delpartner link")
        return

    username = normalize_link(link)
    data = load_partner()

    new_data = [p for p in data if p["username"] != username]

    save_partner(new_data)
    update.message.reply_text("✅   Partner dihapus")


def list_partner(update, context):
    if update.effective_user.id not in OWNER_IDS:
        return

    data = load_partner()

    if not data:
        update.message.reply_text("❌   kosong")
        return

    text = "📋 𝐋𝐈𝐒𝐓 𝐏𝐀𝐑𝐓𝐍𝐄𝐑\n\n"

    for i, p in enumerate(data, 1):
        text += f"〔{i}〕 {p['name']}\n"
        text += f"🔗 {p['link']}\n\n"

    update.message.reply_text(text)



# ================= OWNER SET =================

def bot_on(update, context):
    global WORKER_ACTIVE
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return

    WORKER_ACTIVE = True
    update.message.reply_text("✅ Tagall dibuka (ON)")


def bot_off(update, context):
    global WORKER_ACTIVE
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return

    WORKER_ACTIVE = False
    update.message.reply_text("❌ Tagall dimatikan (OFF)")


def add_pict(update, context):
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        update.message.reply_text("❌  reply foto dengan /addpict")
        return
    file_id = update.message.reply_to_message.photo[-1].file_id
    data = load_setting()
    data["start_pict"] = file_id
    save_setting(data)
    update.message.reply_text("✅  foto disimpan")


def del_pict(update, context):
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return
    data = load_setting()
    data.pop("start_pict", None)
    save_setting(data)
    update.message.reply_text("✅  foto dihapus")


def add_pj(update, context):
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return
    username = context.args[0].replace("@", "")
    data = load_setting()
    data["pj"] = username
    save_setting(data)
    update.message.reply_text("✅  PJ disimpan")


def del_pj(update, context):
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return
    data = load_setting()
    data.pop("pj", None)
    save_setting(data)
    update.message.reply_text("✅  PJ dihapus")


def add_rules(update, context):
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return
    text = update.message.reply_to_message.text if update.message.reply_to_message else " ".join(context.args)
    if not text:
        update.message.reply_text("❌  isi rules")
        return
    data = load_setting()
    data["rules"] = text
    save_setting(data)
    update.message.reply_text("✅  rules disimpan")


def del_rules(update, context):
    if update.effective_user.id not in OWNER_IDS or update.effective_chat.type != "private":
        return
    data = load_setting()
    data.pop("rules", None)
    save_setting(data)
    update.message.reply_text("✅  rules dihapus")

def off_cmd(update, context):
    global WORKER_ACTIVE

    if update.effective_user.id not in OWNER_IDS:
        return

    WORKER_ACTIVE = False
    update.message.reply_text("✅ Tagall dimatikan")


def on_cmd(update, context):
    global WORKER_ACTIVE

    if update.effective_user.id not in OWNER_IDS:
        return

    WORKER_ACTIVE = True
    update.message.reply_text("✅ Tagall diaktifkan")

def start_cmd(update: Update, context: CallbackContext):
    data = load_setting()

    # ================= LOADING MESSAGE =================
    msg = update.message.reply_text("⚡  Initializing...")

    import time
    import os

    # ================= RGB GLITCH =================
    glitch = [
        "💜 NIGHT HAVEN 💜",
        "💙 NIGHT HAVEN 💙",
        "💚 NIGHT HAVEN 💚",
        "💛 NIGHT HAVEN 💛",
        "🧡 NIGHT HAVEN 🧡",
        "❤️ NIGHT HAVEN ❤️"
    ]

    for g in glitch:
        time.sleep(0.12)
        try:
            msg.edit_text(g)
        except:
            pass

    # ================= TYPING HACKER =================
    hacker_lines = [
        "⌬ connecting to core...",
        "⌬ bypass firewall...",
        "⌬ injecting payload...",
        "⌬ decrypting system...",
        "⌬ syncing modules..."
    ]

    for line in hacker_lines:
        words = line.split(" ")
        typed = ""

        for w in words:
            typed += w + " "
            try:
                msg.edit_text(typed)
            except:
                pass
            time.sleep(0.03)

        time.sleep(0.05)

    # ================= PROGRESS BAR =================
    for i in range(0, 101, 20):
        bar = "■" * (i // 20) + "□" * (5 - i // 20)
        time.sleep(0.12)
        try:
            msg.edit_text(f"⚡  Booting System...\n[{bar}] {i}%")
        except:
            pass

    # ================= FINAL TEXT (FIX CLEAN) =================
    text = (
        "𓊆 ✨ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐍𝐈𝐆𝐇𝐓 𝐇𝐀𝐕𝐄𝐍 ✨ 𓊇 \n\n"

        "╭───────────────╮\n"
        "│ ٬٬ ࣪ ، 𒀭 bot tag all dengan sistem otomatis.\n"
        "│ ٬٬ ࣪ ، 𒀭 silakan untuk screenshot sendiri.\n"
        "╰───────────────╯\n\n"

        "        ㅤ\n"
        "     ˖ ╲ ( II.᯽ request dan cek rules partner bisa tap opsi di bawah)"
    )

    # ================= BUTTON =================
    buttons = []

    if "pj" in data:
        buttons.append([
            InlineKeyboardButton(
                "📩 REQUEST PARTNER",
                url=f"https://t.me/{data['pj']}"
            )
        ])

    if "rules" in data:
        buttons.append([
            InlineKeyboardButton(
                "📜 RULES PARTNER",
                callback_data="rules"
            )
        ])

    markup = InlineKeyboardMarkup(buttons) if buttons else None

    time.sleep(0.2)

    try:
        msg.delete()
    except BaseException:
        pass

    # ================= FOTO SYSTEM =================
    photo_path = "database4/start.jpg"

    if data.get("start_pict"):
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=data["start_pict"],
            caption=text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif os.path.exists(photo_path):
        with open(photo_path, "rb") as p:
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=p,
                caption=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )

    else:
        update.message.reply_text(
            text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

# ================= CALLBACK =================

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = load_setting()

    # ✅ RULES (BEBAS, GA PERLU JOIN)
    if query.data == "rules":
        query.message.reply_text(data.get("rules", "tidak ada rules"))

    # 🔒 CEK JOIN (WAJIB JOIN)
    elif query.data == "cek_join":
        user_id = query.from_user.id

        if is_user_joined(user_id):
            query.message.edit_text("✅ Sudah join, kirim ulang perintah")
        else:
            query.answer("JOIN DULU WOI 😡", show_alert=True)

# ================= TELETHON =================


async def scrape(chat_id):
    users = {}
    try:
        dialogs = await client.get_dialogs()
        entity = None
        for d in dialogs:
            if d.id == chat_id:
                entity = d.entity
                break
        if not entity:
            print("❌  entity ga ketemu")
            return {}
        async for u in client.iter_participants(entity):
            if not u.bot and u.first_name:
                users[str(u.id)] = u.first_name
    except Exception as e:
        print("❌  scrape error:", e)
    return users

# ================= MEMBER =================


def get_members(chat_id):
    merged = {}
    try:
        r = requests.get(f"{API_URL}?chat_id={chat_id}", timeout=5)
        api_data = r.json()
    except BaseException:
        api_data = {}
    try:
        live_data = loop.run_until_complete(scrape(chat_id))
    except BaseException:
        live_data = {}
    for uid, name in api_data.items():
        merged[str(uid)] = name
    for uid, name in live_data.items():
        merged[str(uid)] = name
    return merged


# ================= LIMIT GC =================
LIMIT_FILE = "limit_gc.json4"

from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))

def get_today_wib():
    return datetime.now(WIB).strftime("%Y-%m-%d")

def load_limit():
    try:
        with open(LIMIT_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_limit(data):
    with open(LIMIT_FILE, "w") as f:
        json.dump(data, f)

# 🔥 WORKER SWITCH (ON / OFF)
WORKER_ACTIVE = True


# ================= TAGALL =================
task_queue = Queue()
running_task = False
user_queue = []
progress_map = {}
print("QUEUE INIT:", user_queue)


# ================= PROGRESS REAL =================
def update_progress(user_id, current, total):
    percent = int((current / total) * 100) if total else 0
    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
    try:
        if user_id in progress_map:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=progress_map[user_id]["msg_id"],
                text=f"🚀 𝐓𝐀𝐆𝐀𝐋𝐋 𝐏𝐑𝐎𝐒𝐄𝐒\n\n[{bar}] {percent}%\n👥 {current}/{total}"
            )
    except BaseException:
        pass

def start_progress(user_id):
    msg = bot.send_message(
        chat_id=user_id,
        text="🚀 𝐓𝐀𝐆𝐀𝐋𝐋 𝐃𝐈𝐌𝐔𝐋𝐀𝐈\n\n⏳    0%"
    )
    progress_map[user_id] = {
        "msg_id": msg.message_id
    }


# ================= AUTO DELETE =================
def auto_delete_messages(chat_id, message_ids):
    print("🧹 AUTO DELETE START")
    time.sleep(120)
    for msg_id in message_ids:
        if not msg_id:
            continue
        try:
            bot.delete_message(chat_id, msg_id)
            print("✔ hapus:", msg_id)
            time.sleep(0.3)
        except Exception as e:
            print("❌   GAGAL HAPUS:", msg_id, e)
    print("✅   AUTO DELETE SELESAI")


# ================= WORKER =================
def tagall_worker():
    global running_task
    print("🔥 WORKER HIDUP")

    while True:
        chat_id, text, user_id = task_queue.get()

        # ================= WORKER OFF =================
        if not WORKER_ACTIVE:
            try:
                bot.send_message(
                    user_id,
                    "❌ Maaf lagi close tagall dulu"
                )
            except:
                pass

            task_queue.task_done()
            continue

        # ================= LIMIT GC (RESET 00:00 WIB) =================
        limit_data = load_limit()
        today = get_today_wib()

        last_used = limit_data.get(str(chat_id))

        if last_used == today:
            task_queue.task_done()
            continue

        print("🔥 AMBIL TASK:", user_id)

        try:
            if user_queue and user_queue[0] != user_id:
                task_queue.put((chat_id, text, user_id))
                time.sleep(0.2)
                continue

            running_task = True
            print("🚀 PROSES USER:", user_id)

            links = re.findall(r"(https?://t\.me/\S+)", text)
            partner_link = links[0] if links else "-"

            start_msg = (
                "🚀 𝐓𝐀𝐆𝐀𝐋𝐋 𝐃𝐈𝐌𝐔𝐋𝐀𝐈\n\n"
                f"🔗 partner : {partner_link}\n"
                "⏰   durasi : 5 menit\n"
                "📍 JIKA BOT EROR SILAHKAN KESINI @TAGallnigth_bot"
            )

            bot.send_message(chat_id, start_msg)
            bot.send_message(user_id, start_msg)

# ================= START =================
            start_progress(user_id)
            sent_messages = []
            sent = 0

            members = get_members(chat_id)
            if not members:
                continue

            user_ids = list(members.keys())
            total = len(user_ids)

            random.shuffle(user_ids)

            BATCH_SIZE = 4
            BASE_DELAY = 0.75
            start_time = time.time()
            duration = 300

            # ================= LOOP TAG =================
            while time.time() - start_time < duration:
                for i in range(0, total, BATCH_SIZE):
                    if time.time() - start_time >= duration:
                        break

                    batch = user_ids[i:i + BATCH_SIZE]

                    mention_text = ""
                    for uid in batch:
                        name = html.escape(members[uid])
                        mention_text += f'<a href="tg://user?id={uid}">{name}</a> '

                    try:
                        msg = bot.send_message(
                            chat_id,
                            f" 💕 𝑩𝑶𝑻 𝑻𝑨𝑮𝑨𝑳𝑳 𝐍𝐈𝐆𝐇𝐓 𝐇𝐀𝐕𝐄𝐍 💖\n\n{text}\n\n{mention_text}",
                            parse_mode="HTML",
                        )

                        sent_messages.append(msg.message_id)
                        sent += len(batch)
                        update_progress(user_id, sent, total)

                    except Exception as e:
                        print("❌  ", e)
                        if "Too Many Requests" in str(e):
                            time.sleep(1.8)
                        else:
                            time.sleep(0.6)

                    time.sleep(BASE_DELAY + random.uniform(0.03, 0.12))

            # ================= SELESAI GC =================
            bot.send_message(
                chat_id,
                f"✅   𝐓𝐀𝐆𝐀𝐋𝐋 𝐒𝐄𝐋𝐄𝐒𝐀𝐈\n\n"
                f"🔗 partner : {partner_link}\n"
                f"👥 Total: {sent}"
            )

            # 🔥 SAVE LIMIT (BERDASARKAN TANGGAL WIB)
            limit_data[str(chat_id)] = today
            save_limit(limit_data)

            # 🔥 DEBUG
            print("TOTAL MSG:", len(sent_messages))
            print("LIST MSG:", sent_messages[:5])

            # 🔥 AUTO DELETE
            if sent_messages:
                threading.Thread(
                    target=auto_delete_messages,
                    args=(chat_id, sent_messages.copy()),
                    daemon=True
                ).start()

            # ============== PRIVATE ==============
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=progress_map[user_id]["msg_id"],
                    text=f"✅       𝐓𝐀𝐆𝐀𝐋𝐋 𝐒𝐄𝐋𝐄𝐒𝐀𝐈\n\n"
                         f"🔗 partner : {partner_link}\n"
                         f"🧹 semua mention dihapus otomatis\n"
                         f"👥 Total: {sent}\n"
                         f"⏱ 5 menit"
                )
            except:
                pass

# ================= HAPUS ANTRIAN =================
            if user_queue and user_queue[0] == user_id:
                user_queue.pop(0)

        except Exception as e:
            print("❌  ERROR:", e)

        finally:
            running_task = False
            task_queue.task_done()

# ================= CEK JOIN =================
def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(FORCE_GROUP, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= HANDLER =================
def handle_private(update: Update, context: CallbackContext):
    global running_task

    if not update.message:
        return

    msg = update.message

    if msg.chat.type != "private":
        return

    user_id = update.effective_user.id

    # ================= FORCE JOIN =================
    if not is_user_joined(user_id):
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 JOIN GROUP", url=FORCE_LINK)],
            [InlineKeyboardButton("✅ CEK LAGI", callback_data="cek_join")]
        ])

        msg.reply_text(
            "🚫 AKSES DITOLAK\n\n"
            "📢 Kamu wajib join group dulu!\n"
            "🔓 Setelah join klik CEK LAGI",
            reply_markup=buttons
        )
        return

    # ================= LANJUT =================
    text = msg.text or ""

    # ================= VALIDASI LINK =================
    links = re.findall(r"(https?://t\.me/\S+)", text)

    if not links:
        msg.reply_text("❌ Tidak ada link t.me")
        return

    data = load_partner()

    valid = any(normalize_link(l) == p["username"]
                for l in links for p in data)

    if not valid:
        msg.reply_text("❌ Link tidak terdaftar partner")
        return

    # ================= LIMIT =================
    antrian = task_queue.qsize()

    if antrian >= 3:
        msg.reply_text(
            "⚠️ 𝐀𝐍𝐓𝐑𝐈𝐀𝐍 𝐏𝐄𝐍𝐔𝐇\n\n"
            "⏳ Tunggu beberapa menit\n"
            "🚀 Bot sedang sibuk"
        )
        return

    user_id = msg.from_user.id

    # ================= MASUK ANTRIAN =================
    if user_id not in user_queue:
        user_queue.append(user_id)

    posisi = user_queue.index(user_id) + 1

    # ================= NOTIF PRIVATE =================
    if posisi == 1 and not running_task:
        msg.reply_text(
            "📢 Permintaan kamu sedang di proses\n"
            "⏳ Durasi: 5 menit\n"
            "📸 Mohon screenshot\n\n"
            "✨ Tunggu sampai selesai ya..."
        )
    else:
        msg.reply_text(
            f"⏳ 𝐌𝐀𝐒𝐔𝐊 𝐀𝐍𝐓𝐑𝐈𝐀𝐍\n\n"
            f"📊 Posisi kamu: {posisi}\n"
            f"🚀 Akan diproses setelah yang lain selesai"
        )

    # ================= MASUK TASK =================
    for chat_id in TARGET_CHATS:
        task_queue.put((chat_id, text, user_id))

    # ================= START WORKER =================
    if not running_task:
        threading.Thread(target=tagall_worker, daemon=True).start()

# ================= MAIN =================

def restore_cmd(update, context):
    if update.effective_user.id != OWNER_ID:
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        update.message.reply_text("❌ reply file zip dengan /restore")
        return

    try:
        update.message.reply_text("⏳ restore sedang diproses...")

        # ================= DOWNLOAD =================
        file = update.message.reply_to_message.document.get_file()
        file.download("restore.zip")

        import zipfile
        import os

        # ================= VALIDASI ZIP =================
        if not zipfile.is_zipfile("restore.zip"):
            update.message.reply_text("❌ file bukan zip valid")
            return

        with zipfile.ZipFile("restore.zip", 'r') as z:
            files = z.namelist()

            # ================= VALIDASI ISI =================
            valid = any("partner.json" in f for f in files) or \
                    any("setting.json" in f for f in files)

            if not valid:
                update.message.reply_text("❌ isi zip tidak valid")
                return

            # ================= BACKUP LAMA =================
            backup_name = f"backup_before_restore_{int(time.time())}.zip"
            with zipfile.ZipFile(backup_name, 'w') as backup:
                if os.path.exists("partner.json7"):
                    backup.write("partner.json7")
                if os.path.exists("setting.json7"):
                    backup.write("setting.json7")
                if os.path.exists("database4"):
                    for root, dirs, files2 in os.walk("database"):
                        for f in files2:
                            backup.write(os.path.join(root, f))

            # ================= EXTRACT =================
            z.extractall()

        update.message.reply_text("✅ restore sukses, bot akan restart...")

        # ================= AUTO RESTART =================
        import os
        os.execv("/root/partnerbot/venv/bin/python", ["python", "bot4.py"])

    except Exception as e:
        update.message.reply_text(f"❌ restore gagal\n{e}")

def main():
    global bot
    updater = Updater(TOKEN, use_context=True)
    bot = updater.bot

    database4.start_system(bot)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("restore", restore_cmd))
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("addpartner", add_partner))
    dp.add_handler(CommandHandler("delpartner", del_partner))
    dp.add_handler(CommandHandler("listpartner", list_partner))
    dp.add_handler(CommandHandler("addpict", add_pict))
    dp.add_handler(CommandHandler("delpict", del_pict))
    dp.add_handler(CommandHandler("addpj", add_pj))
    dp.add_handler(CommandHandler("delpj", del_pj))
    dp.add_handler(CommandHandler("addrules", add_rules))
    dp.add_handler(CommandHandler("delrules", del_rules))
    dp.add_handler(CommandHandler("off", off_cmd))
    dp.add_handler(CommandHandler("on", on_cmd))
    dp.add_handler(CallbackQueryHandler(button_handler))

    dp.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            handle_private
        )
    )

    client.start()
    print("✅ Telethon nyala")

    t = threading.Thread(target=tagall_worker)
    t.daemon = True
    t.start()

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()


	
