import os
import time
import yt_dlp
import telebot
import zipfile
import requests
import subprocess
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ────────────────────────────────────────────────
# 🤖 BOT CONFIGURATION
# ────────────────────────────────────────────────
BOT_TOKEN = "8228790586:AAGaP0CYYvFP65Atb9OW9h-D85HrDrdYmEI"
bot = telebot.TeleBot(BOT_TOKEN)
CACHE_DIR = "cache"
FFMPEG_DIR = "ffmpeg"
os.makedirs(CACHE_DIR, exist_ok=True)

pending_format = {}

# ────────────────────────────────────────────────
# 🧠 FFMPEG VERIFICATION / AUTO-INSTALL
# ────────────────────────────────────────────────
def verify_or_install_ffmpeg():
    ffmpeg_exe = os.path.join(FFMPEG_DIR, "bin", "ffmpeg.exe")

    # Check if ffmpeg already installed
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg found in system PATH.")
            return None  # None = system ffmpeg
    except FileNotFoundError:
        pass

    # If not installed, auto-download
    if not os.path.exists(ffmpeg_exe):
        print("⬇️ Downloading FFmpeg (Gyan.dev build)...")
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = "ffmpeg.zip"

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Extract
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall("temp_ffmpeg")
        os.remove(zip_path)

        # Move folder
        extracted = next(iter(os.listdir("temp_ffmpeg")))
        os.rename(os.path.join("temp_ffmpeg", extracted), FFMPEG_DIR)
        os.rmdir("temp_ffmpeg")

        print("✅ FFmpeg installed successfully!")

    # Verify installation
    if os.path.exists(ffmpeg_exe):
        print("✅ FFmpeg ready at:", ffmpeg_exe)
        return os.path.join(FFMPEG_DIR, "bin")
    else:
        print("❌ FFmpeg installation failed.")
        return None


# ────────────────────────────────────────────────
# 🎧 DOWNLOAD SONG FUNCTION
# ────────────────────────────────────────────────
def download_song(query, fmt, ffmpeg_path=None):
    start = time.time()
    safe_name = "".join(c for c in query if c.isalnum() or c in (" ", "_", "-")).strip()
    cache_path = os.path.join(CACHE_DIR, f"{safe_name}.{fmt}")

    if os.path.exists(cache_path):
        return cache_path, 0, True

    try:
        if fmt == "mp3":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(CACHE_DIR, "%(title)s.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            if ffmpeg_path:
                ydl_opts["ffmpeg_location"] = ffmpeg_path
        else:
            ydl_opts = {
                "format": f"bestaudio[ext={fmt}]/bestaudio",
                "outtmpl": cache_path,
                "quiet": True,
                "noplaylist": True,
            }

        target = query if query.startswith("http") else f"ytsearch1:{query}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target, download=True)
            downloaded = ydl.prepare_filename(info)
            if fmt == "mp3":
                mp3_file = os.path.splitext(downloaded)[0] + ".mp3"
                if os.path.exists(mp3_file):
                    os.rename(mp3_file, cache_path)

        elapsed = time.time() - start
        return cache_path, elapsed, False

    except Exception as e:
        return None, 0, str(e)


# ────────────────────────────────────────────────
# 💬 MESSAGE HANDLER
# ────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    query = message.text.strip()
    pending_format[chat_id] = query

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("MP3 🎵", callback_data="mp3"),
        InlineKeyboardButton("M4A 🎧", callback_data="m4a"),
        InlineKeyboardButton("WEBM 💽", callback_data="webm"),
    )
    bot.send_message(chat_id, "🎶 Choose the format for your song:", reply_markup=markup)


# ────────────────────────────────────────────────
# 🎛 FORMAT SELECTION HANDLER
# ────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def handle_format(call):
    chat_id = call.message.chat.id
    fmt = call.data
    query = pending_format.pop(chat_id, None)

    if not query:
        bot.send_message(chat_id, "⚠️ No pending song request.")
        return

    bot.send_message(chat_id, f"🔎 Searching '{query}' in {fmt.upper()} format... Please wait ⏳")

    file_path, elapsed, cached = download_song(query, fmt, ffmpeg_path=FFMPEG_BIN)

    if not file_path:
        bot.send_message(chat_id, f"❌ Error: {cached}")
        return

    msg = "⚡ From cache!" if cached else f"✅ Downloaded in {elapsed:.1f}s"
    bot.send_message(chat_id, msg)

    with open(file_path, "rb") as f:
        bot.send_audio(chat_id, f, caption=f"{os.path.basename(file_path)} ({fmt.upper()})")


# ────────────────────────────────────────────────
# 🚀 STARTUP
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print("🎧 Starting Spotify Downloader Bot...")
    FFMPEG_BIN = verify_or_install_ffmpeg()
    bot.infinity_polling()
