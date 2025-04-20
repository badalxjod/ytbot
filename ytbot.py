import asyncio, os, signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError
import yt_dlp

BOT_TOKEN = '7783089947:AAF3Fw_7LT9ylGovsw0-cmQP1BxVgdCWPE8'
CHANNEL_USERNAME = "@Jhnetwork"
MAX_FILE_SIZE = 49 * 1024 * 1024  # 49MB limit for normal users

# Timeout handler
def timeout_handler(signum, frame):
    raise Exception("Process timed out")

signal.signal(signal.SIGALRM, timeout_handler)

# Check if user joined the channel
async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [[InlineKeyboardButton("✅ Join @Jhnetwork", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")]]
        await update.message.reply_text("⛔ Join [@Jhnetwork](https://t.me/Jhnetwork) to use this bot.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    await update.message.reply_text(f"Hi `{update.effective_user.first_name}`! Send any YouTube link to begin:", parse_mode="Markdown")

# Handle YouTube link
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        keyboard = [[InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")]]
        await update.message.reply_text("Join the channel to use the bot.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    url = update.message.text
    context.user_data['url'] = url
    keyboard = [[InlineKeyboardButton("▶️ Video", callback_data="video"), InlineKeyboardButton("🎧 Audio", callback_data="audio")]]
    await update.message.reply_text("What do you want to download?", reply_markup=InlineKeyboardMarkup(keyboard))

# Handle buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    url = context.user_data.get('url')

    if choice == "audio":
        await query.edit_message_text("Downloading audio...")
        await download_audio(query, url)
    elif choice == "video":
        keyboard = [
            [InlineKeyboardButton("144p", callback_data="144"), InlineKeyboardButton("240p", callback_data="240")],
            [InlineKeyboardButton("360p", callback_data="360"), InlineKeyboardButton("480p", callback_data="480")],
            [InlineKeyboardButton("720p", callback_data="720"), InlineKeyboardButton("1080p", callback_data="1080")]
        ]
        await query.edit_message_text("Choose video quality:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif choice in ["144", "240", "360", "480", "720", "1080"]:
        await download_video(query, url, choice)

# Fake progress
async def fake_progress(message, label):
    steps = ["⚙️ Initializing...", "⬇️ Connecting...", f"🔄 Processing {label}...", "⏳ Finalizing..."]
    for step in steps:
        await message.reply_text(step)
        await asyncio.sleep(1)

# Download audio
async def download_audio(query, url):
    try:
        await fake_progress(query.message, "Audio")
        signal.alarm(60)

        opts = {
            'format': 'bestaudio',
            'outtmpl': 'audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        if os.path.getsize(filename) > MAX_FILE_SIZE:
            await query.message.reply_text("❌ File too large to upload on Telegram.")
            os.remove(filename)
            return

        await query.message.reply_audio(audio=open(filename, 'rb'))
        os.remove(filename)
        signal.alarm(0)

    except Exception as e:
        await query.message.reply_text("❌ Audio download failed.")
        print(f"Audio Error: {e}")
        signal.alarm(0)

# Download video
async def download_video(query, url, quality):
    try:
        await fake_progress(query.message, f"{quality}p Video")
        signal.alarm(90)

        opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

        if os.path.getsize(filename) > MAX_FILE_SIZE:
            await query.message.reply_text("❌ File too large to upload on Telegram.")
            os.remove(filename)
            return

        await query.message.reply_video(video=open(filename, 'rb'), caption=f"✅ Done! {quality}p video.")
        os.remove(filename)
        signal.alarm(0)

    except Exception as e:
        await query.message.reply_text("❌ Video download failed.")
        print(f"Video Error: {e}")
        signal.alarm(0)

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Exception: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ Bot crashed. Try again later.")
    except TelegramError:
        pass

# Run bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_error_handler(error_handler)
app.run_polling()
