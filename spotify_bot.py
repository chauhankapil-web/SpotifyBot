import os
import time
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8228790586:AAGaP0CYYvFP65Atb9OW9h-D85HrDrdYmEI"
bot = telebot.TeleBot(BOT_TOKEN)

# Local folder to cache downloaded songs
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Path to ffmpeg if installed (optional)
FFMPEG_PATH = r"C:\Program Files\ffmpeg8\bin\ffmpeg.exe"  # Update this path if necessary

# Dictionary to track pending format selections
pending_format = {}

# ────────────────────────────────────────────────
# 🧠 Utility: Download song using yt_dlp
# ────────────────────────────────────────────────
def download_song(query, fmt):
    start_time = time.time()
    cache_path = os.path.join(CACHE_DIR, f"{query}.{fmt}")

    # ✅ Use cache if already downloaded
    if os.path.exists(cache_path):
        return cache_path, 0, True

    try:
        # 🎧 Conditional format setup
        if fmt == "mp3":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": cache_path,
                "quiet": True,
                "noplaylist": True,
                "ffmpeg_location": FFMPEG_PATH,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            # m4a / webm — download directly without ffmpeg
            ydl_opts = {
                "format": f"bestaudio[ext={fmt}]",
                "outtmpl": cache_path,
                "quiet": True,
                "noplaylist": True,
            }

        # 🚀 Perform download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])

        elapsed_time = time.time() - start_time
        return cache_path, elapsed_time, False

    except Exception as e:
        return None, 0, str(e)


# ────────────────────────────────────────────────
# 💬 Handle incoming messages
# ────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    query = message.text.strip()

    # Store pending query for format selection
    pending_format[chat_id] = query

    # Popup keyboard for format choice
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton("MP3 🎵", callback_data="mp3"),
        InlineKeyboardButton("M4A 🎧", callback_data="m4a"),
        InlineKeyboardButton("WEBM 💽", callback_data="webm"),
    )
    bot.send_message(chat_id, "Select format for your song:", reply_markup=markup)


# ────────────────────────────────────────────────
# 🎛 Handle format selection
# ────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def callback_format(call):
    chat_id = call.message.chat.id
    fmt = call.data
    query = pending_format.get(chat_id)

    if not query:
        bot.send_message(chat_id, "No song requested.")
        return

    bot.send_message(chat_id, f"🎶 Searching and downloading '{query}' in {fmt.upper()} format... Please wait ⏳")

    # Download or fetch from cache
    file_path, elapsed, cached = download_song(query, fmt)

    if not file_path:
        bot.send_message(chat_id, f"❌ YouTube Error: {cached}")
        return

    # Calculate and show time
    if cached:
        msg_time = "⚡ Served instantly from cache!"
    else:
        msg_time = f"✅ Downloaded in {elapsed:.2f} seconds."

    bot.send_message(chat_id, msg_time)

    # Send the audio file to Telegram
    with open(file_path, "rb") as f:
        bot.send_audio(chat_id, f, caption=f"{query} ({fmt.upper()})")

    # Clear pending
    pending_format.pop(chat_id, None)


# ────────────────────────────────────────────────
# 🚀 Start bot
# ────────────────────────────────────────────────
print("🎧 Spotify Downloader Bot is running...")
bot.infinity_polling()
