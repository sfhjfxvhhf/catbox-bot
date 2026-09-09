import os
import time
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events
from requests_toolbelt.uploading import MultipartEncoder

# --- ১. Render-এর জন্য মিনি ওয়েব সার্ভার (সার্ভার অন রাখার জন্য) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Bot is Running 24/7 with 1 Gbps Speed!"

def start_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ওয়েব সার্ভার ব্যাকগ্রাউন্ডে চালু করা
threading.Thread(target=start_server, daemon=True).start()

# --- ২. টেলিগ্রাম বট ও Catbox কোড ---
API_ID = 39815337          # আপনার API ID দিন
API_HASH = "9b0d37e38bb885a01fbd024e1514c2f0"  # আপনার API Hash দিন
BOT_TOKEN = "8356182134:AAFBuUlIsXBGMm8RK0y3gW0-_6tXdh4Myk4" # আপনার Bot Token দিন

CATBOX_API_URL = "https://catbox.moe/user/api.php"

bot = TelegramClient("cloud_bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    await event.reply("👋 ক্লাউড সার্ভার থেকে স্বাগতম!\nযেকোনো ফাইল পাঠান, চোখের পলকে ডিরেক্ট লিংক তৈরি হয়ে যাবে।")

@bot.on(events.NewMessage)
async def media_handler(event):
    if event.text and event.text.startswith("/"):
        return
    if not (event.photo or event.video or event.document):
        return

    # Catbox লিমিট চেক
    file_size = event.file.size if event.file else 0
    if file_size > 200 * 1024 * 1024:
        await event.reply("❌ ফাইল সাইজ ২০০ MB-র বেশি! Catbox সর্বোচ্চ ২০০ MB সাপোর্ট করে।")
        return

    status_msg = await event.reply("⚡ ক্লাউড সার্ভারে ডাউনলোড ও আপলোড হচ্ছে...")

    # এক্সটেনশন নির্বাচন
    ext = ".jpg" if event.photo else ".mp4"
    if event.document:
        mime = event.document.mime_type or ""
        if "image" in mime:
            ext = ".jpg"
        elif "video" in mime:
            ext = ".mp4"

    local_filename = f"temp_{event.id}{ext}"

    try:
        # ক্লাউডের সুপারফাস্ট গতিতে ডাউনলোড
        await event.download_media(file=local_filename)

        # Catbox-এ আপলোড
        with open(local_filename, "rb") as f:
            encoder = MultipartEncoder(
                fields={"reqtype": "fileupload", "fileToUpload": (local_filename, f)}
            )
            headers = {"Content-Type": encoder.content_type}
            response = requests.post(CATBOX_API_URL, data=encoder, headers=headers)

        if os.path.exists(local_filename):
            os.remove(local_filename)

        if response.status_code == 200 and response.text.startswith("http"):
            direct_url = response.text.strip()
            await status_msg.edit(f"✅ **আপনার লিংক রেডি (সুপারফাস্ট):**\n`{direct_url}`")
        else:
            await status_msg.edit("❌ আপলোড ব্যর্থ হয়েছে!")

    except Exception as e:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        await status_msg.edit(f"❌ ত্রুটি: {str(e)}")

print("🤖 ক্লাউড বট চালু হয়েছে...")
bot.run_until_disconnected()
