import os
import sys
import time
import asyncio
import sqlite3
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events, Button

# ছবির ওয়াটারমার্কের জন্য Pillow
try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Python 3.12+ Event Loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# --- ১. Render ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Fast Pro Catbox Bot is Running 24/7!"

def start_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- ২. বটের কনফিগারেশন ---
API_ID = 39815337
API_HASH = "9b0d37e38bb885a01fbd024e1514c2f0"

# ⚠️ BotFather থেকে পাওয়া আপনার একদম নতুন টোকেনটি এখানে বসান
BOT_TOKEN = "8356182134:AAEWJwX5iubW1pTWa2LC9n5uZ2mJ4u07Le0"

# আপনার আইডি (না জানলে বটে /broadcast লিখলে বট স্বয়ংক্রিয়ভাবে আপনার আইডি জানিয়ে দেবে)
ADMIN_ID = 8042993801  

BOT_BRAND_NAME = "Photo Hud 🎀"
CATBOX_API_URL = "https://catbox.moe/user/api.php"

# --- ৩. ডাটাবেজ সেটআপ (ইউজার সংরক্ষণের জন্য) ---
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

bot = TelegramClient("cloud_bot_session", API_ID, API_HASH, loop=loop)

# ছবির গায়ে ছোট্ট ওয়াটারমার্ক স্ট্যাম্প লাগানোর ফাংশন
def apply_watermark(image_path):
    if not HAS_PIL:
        return
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)
            text = f"🤖 {BOT_BRAND_NAME} ⚡"
            
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = img.width - text_width - 20
            y = img.height - text_height - 20
            
            draw.text((x+2, y+2), text, fill=(0, 0, 0))
            draw.text((x, y), text, fill=(255, 255, 255))
            img.save(image_path, "JPEG", quality=95)
    except Exception as e:
        print(f"Watermark Error: {e}")

# /start কমান্ড
@bot.on(events.NewMessage(pattern=r"^/start"))
async def start_handler(event):
    add_user(event.sender_id)
    caption = (
        "╔══════════════════════════════════╗\n"
        f"   ⚡ **WELCOME TO {BOT_BRAND_NAME.upper()} CLOUD** ⚡\n"
        "╚══════════════════════════════════╝\n\n"
        "👋 **হ্যালো! আমি সুপারফাস্ট ডিরেক্ট লিংক জেনারেটর বট।**\n\n"
        "🎬 **ভিডিও** দিলে পাবেন সরাসরি `.mp4` স্ট্রিমিং লিংক!\n"
        "🖼️ **ছবি** দিলে পাবেন সরাসরি `.jpg` হাই-কোয়ালিটি লিংক!\n\n"
        "🚀 **সার্ভার স্পিড :** `1 Gbps Ultra Fast`\n"
        "💾 **ফাইল লিমিট   :** `সর্বোচ্চ ২০০ MB`\n"
        "🔒 **সুরক্ষা       :** `পার্মানেন্ট ক্লাউড স্টোরেজ`\n\n"
        "👇 *যেকোনো ছবি বা ভিডিও এখনই সেন্ড বা ফরোয়ার্ড করুন!*"
    )
    buttons = [
        [Button.url("📢 Developer", "https://t.me/itsridoy013")],
        [Button.inline("ℹ️ Help / নিয়ম", b"help_callback")]
    ]
    await event.reply(caption, buttons=buttons)

# বাটন হেল্প কলব্যাক
@bot.on(events.CallbackQuery(data=b"help_callback"))
async def help_callback(event):
    await event.answer("যেকোনো ছবি বা ভিডিও সেন্ড করলেই সরাসরি ডিরেক্ট লিংক পেয়ে যাবেন!", alert=True)

# /help কমান্ড
@bot.on(events.NewMessage(pattern=r"^/help"))
async def help_handler(event):
    await event.reply(
        "📖 **বট ব্যবহারের নিয়মাবলী:**\n\n"
        "১. যেকোনো ছবি বা ভিডিও (সর্বোচ্চ ২০০ MB) বটে ফরোয়ার্ড বা আপলোড করুন।\n"
        "২. কয়েক সেকেন্ডের মধ্যে আপনি সরাসরি ক্লাউড ডিরেক্ট লিংক পেয়ে যাবেন।\n"
        "৩. লিংকটি যেকোনো ব্রাউজার বা ভিডিও প্লেয়ারে সরাসরি চলবে।\n\n"
        "💡 যেকোনো সাহায্যে যোগাযোগ করুন: @itsridoy013"
    )

# /ping কমান্ড (স্পিড চেকার)
@bot.on(events.NewMessage(pattern=r"^/ping"))
async def ping_handler(event):
    start = time.time()
    msg = await event.reply("🏓 **Pinging server...**")
    ping_ms = round((time.time() - start) * 1000)
    await msg.edit(f"🚀 **Pong!** `{ping_ms} ms`\n⚡ সার্ভার ফুল স্পিডে সচল আছে!")

# /stats কমান্ড (এডমিনের জন্য)
@bot.on(events.NewMessage(pattern=r"^/stats"))
async def stats_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    users = get_all_users()
    await event.reply(
        "📊 **বট অ্যানালিটিক্স রিপোর্ট:**\n\n"
        f"👥 **মোট ইউজার :** `{len(users)}` জন\n"
        f"⚙️ **সার্ভার স্ট্যাটাস :** `Healthy & Active (1 Gbps)`\n"
        f"🏷️ **বট ব্র্যান্ডিং :** `{BOT_BRAND_NAME}`"
    )

# /broadcast কমান্ড (স্মার্ট ব্রডকাস্টার)
@bot.on(events.NewMessage(pattern=r"^/broadcast"))
async def broadcast_handler(event):
    # ইউজার এডমিন না হলে তাকে তার আইডি জানিয়ে দেবে
    if event.sender_id != ADMIN_ID:
        await event.reply(
            f"❌ **অনুমতি নেই!** আর তুমি একটা বোকাচুদা, আপনি এই বটের এডমিন হিসেবে সেট করা নেই।\n\n"
            f"🆔 **আপনার আসল Telegram User ID:** `{event.sender_id}`\n\n"
            f"👉 এই আইডি নম্বরটি কপি করে আপনার `bot.py` ফাইলের `ADMIN_ID = {event.sender_id}` লাইনে বসিয়ে সেভ করুন।"
        )
        return

    reply_msg = await event.get_reply_message()
    broadcast_text = event.raw_text.replace("/broadcast", "", 1).strip()

    if not reply_msg and not broadcast_text:
        await event.reply(
            "⚠️ **কীভাবে ব্রডকাস্ট করবেন:**\n\n"
            "১. যেকোনো মেসেজে রিপ্লাই করে `/broadcast` লিখুন।\n"
            "অথবা\n"
            "২. সরাসরি লিখুন: `/broadcast আপনার মেসেজের লেখা`"
        )
        return

    users = get_all_users()
    if not users:
        await event.reply("⚠️ ডাটাবেজে এখনো কোনো ইউজার যুক্ত হয়নি!")
        return

    progress = await event.reply(f"📢 **ব্রডকাস্ট শুরু হচ্ছে...**\n👥 মোট প্রাপক: `{len(users)}` জন")
    sent, failed = 0, 0

    for uid in users:
        try:
            if reply_msg:
                await bot.send_message(uid, reply_msg)
            else:
                await bot.send_message(uid, broadcast_text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await progress.edit(
        f"🎉 **ব্রডকাস্ট সম্পন্ন!**\n\n"
        f"✅ সফল ডেলিভারি : `{sent}`\n"
        f"❌ ব্যর্থ (ব্লক/ডিলিট) : `{failed}`\n"
        f"📊 মোট ইউজার : `{len(users)}`"
    )

# ফাইল ও মিডিয়া প্রসেসর
@bot.on(events.NewMessage)
async def media_handler(event):
    if event.text and event.text.startswith("/"):
        return
    if not (event.photo or event.video or event.document):
        return

    add_user(event.sender_id)

    file_size = event.file.size if event.file else 0
    if file_size > 200 * 1024 * 1024:
        await event.reply("❌ **ফাইল সাইজ ২০০ MB-র বেশি!** Catbox সর্বোচ্চ ২০০ MB সাপোর্ট করে।")
        return

    ext = ".jpg" if event.photo else ".mp4"
    file_type = "JPG Image" if event.photo else "MP4 Video"
    original_name = "media" + ext

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
    branded_filename = f"[{BOT_BRAND_NAME}]_{int(time.time())}_{original_name}"
    local_path = f"temp_{branded_filename}"

    # লোডিং অ্যানিমেশন
    status_msg = await event.reply("🌀 ⠋ `[■□□□□□□□□□] ১০%` 📥 ফাইল গ্রহণ করা হচ্ছে...")
    total_start = time.time()

    try:
        # ডাউনলোড
        await status_msg.edit("⚡ ⠹ `[■■■■□□□□□□] ৪০%` ⚙️ ক্লাউড সার্ভারে ডাউনলোড হচ্ছে...")
        await event.download_media(file=local_path)

        # ছবিতে ওয়াটারমার্ক
        if ext == ".jpg":
            apply_watermark(local_path)

        # আপলোড
        await status_msg.edit("🚀 ⠴ `[■■■■■■■□□□] ৭০%` 📤 সুপারফাস্ট ক্লাউডে আপলোড হচ্ছে...")
        with open(local_path, "rb") as f:
            data = {"reqtype": "fileupload"}
            files = {"fileToUpload": (branded_filename, f)}
            response = requests.post(CATBOX_API_URL, data=data, files=files)

        await status_msg.edit("✨ ⠧ `[■■■■■■■■■■] ১০০%` 🔗 ডিরেক্ট পার্মানেন্ট লিংক তৈরি হচ্ছে...")

        if os.path.exists(local_path):
            os.remove(local_path)

        duration = round(time.time() - total_start, 1)

        if response.status_code == 200 and response.text.startswith("http"):
            direct_url = response.text.strip()

            # প্রিমিয়াম ফাইল কার্ড
            caption = (
                "╔══════════════════════════════════╗\n"
                "   ✨ **FILE UPLOADED SUCCESSFULLY!** ✨\n"
                "╚══════════════════════════════════╝\n\n"
                f"🏷️ **ফাইলের নাম**   : `{original_name}`\n"
                f"📁 **ফাইলের ধরন**   : `{file_type}`\n"
                f"📦 **ফাইল সাইজ**    : `{size_mb} MB`\n"
                f"⚡ **সময় লেগেছে**   : `{duration}s (Ultra Fast)`\n"
                f"🛡️ **ব্র্যান্ড স্ট্যাম্প** : `@{BOT_BRAND_NAME}`\n\n"
                f"🔗 **ডিরেক্ট পার্মানেন্ট লিংক :**\n`{direct_url}`"
            )

            # বাটন
            share_link = f"https://t.me/share/url?url={direct_url}&text=Check%20out%20this%20direct%20link!"
            buttons = [
                [Button.url("🌐 Open Link", direct_url), Button.url("↗️ Share Link", share_link)],
                [Button.url("🤖 Developer", "https://t.me/itsridoy013")]
            ]

            await status_msg.edit(caption, buttons=buttons)
        else:
            await status_msg.edit("❌ আপলোড ব্যর্থ হয়েছে! অনুগ্রহ করে আবার চেষ্টা করুন।")

    except Exception as e:
        if os.path.exists(local_path):
            os.remove(local_path)
        await status_msg.edit(f"❌ সমস্যা হয়েছে: {str(e)}")

# মেইন রানার
async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 আল্ট্রা প্রফেশনাল বট সফলভাবে চালু হয়েছে এবং রানিং!")
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
