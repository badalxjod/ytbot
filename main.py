from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import asyncio

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("yt_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    name = message.from_user.first_name
    await message.reply(
        f"**👋 Hello {name.upper()}!**\n\n"
        "Send a **YouTube** link, and I'll help you download video or audio!",
    )

@app.on_message(filters.private & filters.text)
async def download(client, message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.reply("❌ Please send a valid YouTube URL.")
        return

    progress = await message.reply("⌛ Processing your link...")
    for i in range(1, 4):
        await asyncio.sleep(0.4)
        await progress.edit(f"⌛ Analyzing{'.' * i}")

    try:
        buttons = [
            [InlineKeyboardButton("144p", callback_data=f"video|18|{url}"),
             InlineKeyboardButton("240p", callback_data=f"video|133+140|{url}")],
            [InlineKeyboardButton("360p", callback_data=f"video|134+140|{url}"),
             InlineKeyboardButton("480p", callback_data=f"video|135+140|{url}")],
            [InlineKeyboardButton("720p", callback_data=f"video|22|{url}"),
             InlineKeyboardButton("1080p", callback_data=f"video|137+140|{url}")],
            [InlineKeyboardButton("1440p", callback_data=f"video|264+140|{url}"),
             InlineKeyboardButton("2160p (4K)", callback_data=f"video|313+140|{url}")],
            [InlineKeyboardButton("🎧 Audio Only", callback_data=f"audio|bestaudio|{url}")]
        ]

        await progress.edit("👇 Choose your desired quality to download:", reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        await progress.edit(f"❌ Error: {e}")

@app.on_callback_query()
async def callback_query(client, query):
    data = query.data
    action, fmt_id, url = data.split("|")
    msg = await query.message.edit("⬇️ Downloading your file... Please wait.")

    ydl_opts = {
        'format': fmt_id,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'merge_output_format': 'mp4' if action == 'video' else None,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if action == 'audio' else []
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        caption = info.get("title", "Here is your file")
        await client.send_document(query.message.chat.id, document=filename, caption=caption)
        os.remove(filename)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

app.run()
