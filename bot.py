import os
import sys
import asyncio
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events

# Python 3.12+ এর জন্য Event Loop তৈরি
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# --- ১. Render-এর জন্য ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Bot is Running 24/7 with 1 Gbps Speed!"

def start_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- ২. টেলিগ্রাম বট ও Catbox কোড ---
API_ID = 39815337
API_HASH = "9b0d37e38bb885a01fbd024e1514c2f0"
BOT_TOKEN = "8356182134:AAFBuUlIsXBGMm8RK0y3gW0-_6tXdh4Myk4"

CATBOX_API_URL = "https://catbox.moe/user/api.php"

bot = TelegramClient("cloud_bot_session", API_ID, API_HASH, loop=loop)

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    await event.reply("👋 ক্লাউড সার্ভার থেকে স্বাগতম!\nযেকোনো ভিডিও বা ছবি পাঠান, সুপারফাস্ট গতিতে ডিরেক্ট লিংক তৈরি হয়ে যাবে।")

@bot.on(events.NewMessage)
async def media_handler(event):
    if event.text and event.text.startswith("/"):
        return
    if not (event.photo or event.video or event.document):
        return

    # Catbox সর্বোচ্চ ২০০ MB সাপোর্ট করে
    file_size = event.file.size if event.file else 0
    if file_size > 200 * 1024 * 1024:
        await event.reply("❌ ফাইল সাইজ ২০০ MB-র বেশি! Catbox সর্বোচ্চ ২০০ MB সাপোর্ট করে।")
        return

    status_msg = await event.reply("⚡ ক্লাউড সার্ভারে ডাউনলোড ও আপলোড শুরু হচ্ছে...")

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
        # ক্লাউডের ১০০০ Mbps গতিতে ডাউনলোড
        await event.download_media(file=local_filename)

        # সাধারণ requests দিয়ে সরাসরি Catbox-এ আপলোড
        with open(local_filename, "rb") as f:
            data = {"reqtype": "fileupload"}
            files = {"fileToUpload": (local_filename, f)}
            response = requests.post(CATBOX_API_URL, data=data, files=files)

        # সার্ভার ক্লিন রাখতে ফাইল ডিলিট
        if os.path.exists(local_filename):
            os.remove(local_filename)

        if response.status_code == 200 and response.text.startswith("http"):
            direct_url = response.text.strip()
            await status_msg.edit(f"✅ **আপনার লিংক রেডি (সুপারফাস্ট):**\n`{direct_url}`")
        else:
            await status_msg.edit("❌ আপলোড ব্যর্থ হয়েছে! অনুগ্রহ করে আবার চেষ্টা করুন।")

    except Exception as e:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        await status_msg.edit(f"❌ সমস্যা হয়েছে: {str(e)}")

# মেইন রানার
async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 ক্লাউড বট সফলভাবে চালু হয়েছে এবং টেলিগ্রামের সাথে কানেক্টেড!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    # ওয়েব সার্ভার ব্যাকগ্রাউন্ডে চালু করা
    threading.Thread(target=start_server, daemon=True).start()

    # বট চালু
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"🔥 Startup Error: {e}", file=sys.stderr)
        sys.exit(1)
