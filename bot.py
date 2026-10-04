import os
import sys
import time
import asyncio
import sqlite3
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

# Python 3.12+ এর জন্য Event Loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# --- ১. Render ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Pro Catbox Bot is Running 24/7!"

def start_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- ২. ডাটাবেজ সেটআপ (ইউজারদের সংরক্ষণ করার জন্য) ---
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return users

init_db()

# --- ৩. বটের ক্রিডেনশিয়াল ও কনফিগ ---
API_ID = 39815337
API_HASH = "9b0d37e38bb885a01fbd024e1514c2f0"
BOT_TOKEN = "8356182134:AAFBuUlIsXBGMm8RK0y3gW0-_6tXdh4Myk4"

# আপনার নিজস্ব টেলিগ্রাম নিউমেরিক আইডি বসান (যেমন @userinfobot থেকে পাবেন)
ADMIN_ID = 8042993801  # ⚠️ এখানে আপনার নিজের টেলিগ্রাম আইডি দিন

# ফোর্স সাবস্ক্রাইবের চ্যানেল ও গ্রুপ
CHANNELS = ["itsridoy013", "itsridoy01"]
CHANNEL_URL = "https://t.me/itsridoy013"
GROUP_URL = "https://t.me/itsridoy01"

CATBOX_API_URL = "https://catbox.moe/user/api.php"

bot = TelegramClient("cloud_bot_session", API_ID, API_HASH, loop=loop)

# ফোর্স সাবস্ক্রাইব চেকার
async def is_subscribed(user_id):
    for ch in CHANNELS:
        try:
            await bot(GetParticipantRequest(channel=ch, user_id=user_id))
        except UserNotParticipantError:
            return False
        except Exception:
            pass
    return True

# ফোর্স সাবস্ক্রাইব বাটন
def fsub_buttons():
    return [
        [Button.url("📢 Join Channel", CHANNEL_URL)],
        [Button.url("👥 Join Group", GROUP_URL)],
        [Button.inline("🔄 Joined / Try Again", b"check_fsub")]
    ]

# /start হ্যান্ডলার
@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = event.sender_id
    add_user(user_id)

    if not await is_subscribed(user_id):
        await event.reply(
            "⚠️ **বটটি ব্যবহার করার জন্য আপনাকে আমাদের চ্যানেল ও গ্রুপে যুক্ত হতে হবে!**\n\n"
            "নিচের বাটনগুলো দিয়ে জয়েন করে **Joined / Try Again** বাটনে চাপ দিন:",
            buttons=fsub_buttons()
        )
        return

    await event.reply(
        "👋 **স্বাগতম!**\n\n"
        "যেকোনো ভিডিও বা ছবি ফরোয়ার্ড করুন অথবা গ্যালারি থেকে সেন্ড করুন।\n"
        "মুহূর্তের মধ্যেই ডিরেক্ট পার্মানেন্ট লিংক তৈরি করে দেওয়া হবে। 🚀"
    )

# বাটন ক্লিক হ্যান্ডলার (Joined চেক)
@bot.on(events.CallbackQuery(data=b"check_fsub"))
async def callback_check(event):
    if await is_subscribed(event.sender_id):
        await event.edit("✅ আপনাকে ধন্যবাদ! আপনি সফলভাবে যুক্ত হয়েছেন। এবার যেকোনো ফাইল সেন্ড করুন।")
    else:
        await event.answer("❌ আপনি এখনো উভয় চ্যানেল ও গ্রুপে জয়েন করেননি! দয়া করে জয়েন করুন।", alert=True)

# ব্রডকাস্ট কমান্ড (শুধুমাত্র এডমিন ব্যবহার করতে পারবে)
@bot.on(events.NewMessage(pattern="/broadcast"))
async def broadcast_handler(event):
    if event.sender_id != ADMIN_ID:
        return

    msg = await event.get_reply_message()
    broadcast_text = event.text.replace("/broadcast", "").strip()

    if not msg and not broadcast_text:
        await event.reply("⚠️ কোনো মেসেজ লিখে `/broadcast <text>` দিন অথবা মেসেজে রিপ্লাই দিয়ে `/broadcast` লিখুন।")
        return

    users = get_all_users()
    status = await event.reply(f"📢 মোট {len(users)} জন ইউজারের কাছে ব্রডকাস্ট শুরু হচ্ছে...")
    sent, failed = 0, 0

    for uid in users:
        try:
            if msg:
                await bot.send_message(uid, msg)
            else:
                await bot.send_message(uid, broadcast_text)
            sent += 1
            await asyncio.sleep(0.05)  # Telegram FloodLimit এড়াতে
        except Exception:
            failed += 1

    await status.edit(f"✅ **ব্রডকাস্ট সম্পন্ন!**\n\n📤 সফল: `{sent}`\n❌ ব্যর্থ: `{failed}`")

# /stats কমান্ড (এডমিন চেক করবে ইউজার সংখ্যা)
@bot.on(events.NewMessage(pattern="/stats"))
async def stats_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    total_users = len(get_all_users())
    await event.reply(f"📊 **বট অ্যানালিটিক্স:**\n\n👥 মোট রেজিস্টার্ড ইউজার: `{total_users}` জন।")

# মিডিয়া হ্যান্ডলার
@bot.on(events.NewMessage)
async def media_handler(event):
    if event.text and event.text.startswith("/"):
        return
    if not (event.photo or event.video or event.document):
        return

    user_id = event.sender_id
    add_user(user_id)

    # ফোর্স সাবস্ক্রাইব যাচাই
    if not await is_subscribed(user_id):
        await event.reply(
            "⚠️ **ফাইল প্রসেস করতে প্রথমে আমাদের চ্যানেল ও গ্রুপে যুক্ত হন!**",
            buttons=fsub_buttons()
        )
        return

    file_size = event.file.size if event.file else 0
    if file_size > 200 * 1024 * 1024:
        await event.reply("❌ ফাইল সাইজ ২০০ MB-র বেশি! Catbox সর্বোচ্চ ২০০ MB সাপোর্ট করে।")
        return

    # ফাইল টাইপ ও নাম নির্ধারণ
    ext = ".jpg" if event.photo else ".mp4"
    file_type = "JPG Image" if event.photo else "MP4 Video"
    original_name = "image.jpg" if event.photo else "video.mp4"

    if event.file and event.file.name:
        original_name = event.file.name
    elif event.document:
        mime = event.document.mime_type or ""
        if "image" in mime:
            ext = ".jpg"
            file_type = "JPG Image"
        elif "video" in mime:
            ext = ".mp4"
            file_type = "MP4 Video"

    size_mb = round(file_size / (1024 * 1024), 2)
    local_filename = f"temp_{event.id}{ext}"

    # ডাইনামিক লোডিং অ্যানিমেশন শুরু
    status_msg = await event.reply("⏳ `[■□□□□□□□□□] ১০%` ডাউনলোড শুরু হচ্ছে...")
    total_start = time.time()

    try:
        # ডাউনলোড
        await status_msg.edit("⚡ `[■■■■□□□□□□] ৪০%` সার্ভারে ডাউনলোড হচ্ছে...")
        await event.download_media(file=local_filename)

        # আপলোড
        await status_msg.edit("🚀 `[■■■■■■■□□□] ৭০%` Catbox-এ আপলোড হচ্ছে...")
        with open(local_filename, "rb") as f:
            data = {"reqtype": "fileupload"}
            files = {"fileToUpload": (local_filename, f)}
            response = requests.post(CATBOX_API_URL, data=data, files=files)

        await status_msg.edit("✨ `[■■■■■■■■■■] ১০০%` লিংক রেডি করা হচ্ছে...")

        if os.path.exists(local_filename):
            os.remove(local_filename)

        duration = round(time.time() - total_start, 1)

        if response.status_code == 200 and response.text.startswith("http"):
            direct_url = response.text.strip()

            # প্রিমিয়াম ফাইল কার্ড লেআউট
            caption = (
                "╔══════════════════════╗\n"
                "   📁 **FILE UPLOADED SUCCESSFULLY!**\n"
                "╚══════════════════════╝\n"
                f"🔹 **ফাইলের নাম**   : `{original_name}`\n"
                f"🔹 **ফাইলের ধরন**   : `{file_type}`\n"
                f"🔹 **ফাইল সাইজ**    : `{size_mb} MB`\n"
                f"🔹 **সময় লেগেছে**   : `{duration}s (🚀 Superfast)`\n\n"
                f"🔗 **ডিরেক্ট লিংক :**\n`{direct_url}`"
            )

            # রঙিন ইন্টারঅ্যাক্টিভ বাটন
            share_link = f"https://t.me/share/url?url={direct_url}&text=Check%20out%20this%20direct%20link!"
            buttons = [
                [Button.url("🌐 Open Link", direct_url), Button.url("↗️ Share Link", share_link)],
                [Button.url("📢 Channel", CHANNEL_URL), Button.url("👥 Group", GROUP_URL)]
            ]

            await status_msg.edit(caption, buttons=buttons)
        else:
            await status_msg.edit("❌ আপলোড ব্যর্থ হয়েছে! অনুগ্রহ করে আবার চেষ্টা করুন।")

    except Exception as e:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        await status_msg.edit(f"❌ সমস্যা হয়েছে: {str(e)}")

# মেইন রানার
async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 প্রফেশনাল বট সফলভাবে চালু হয়েছে এবং রানিং!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"🔥 Startup Error: {e}", file=sys.stderr)
        sys.exit(1)
