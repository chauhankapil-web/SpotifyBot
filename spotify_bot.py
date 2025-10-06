import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import subprocess
import time

# Load .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Spotify auth
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Send a song name — Spotify info + fast YouTube audio download."
    )

# Main handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return

    await update.message.reply_text(f"🔍 Searching for: {query}...")

    # --- Spotify info ---
    try:
        res = sp.search(q=query, limit=1, type="track")
        if res["tracks"]["items"]:
            track = res["tracks"]["items"][0]
            title = track["name"]
            artist = track["artists"][0]["name"]
            url = track["external_urls"]["spotify"]
            img = track["album"]["images"][0]["url"]
            preview = track.get("preview_url")
            caption = f"🎶 *{title}* — {artist}\n🔗 [Spotify]({url})"
            if preview:
                caption += f"\n▶️ [Preview]({preview})"
            await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No Spotify result.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Spotify error: {e}")

    # --- YouTube download ---
    await update.message.reply_text("⏳ Downloading fast audio from YouTube...")

    out_template = os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "--no-playlist",
        "-o", out_template,
        f"ytsearch1:{query}"
    ]

    loop = asyncio.get_running_loop()

    def run_download():
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        proc = await loop.run_in_executor(None, run_download)
        if proc.returncode != 0:
            await update.message.reply_text(f"❌ Download failed:\n{proc.stderr}")
            return

        # Get the downloaded file path (latest file in downloads)
        files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR)]
        latest_file = max(files, key=os.path.getctime)

        # Send file via Telegram
        with open(latest_file, "rb") as f:
            await update.message.reply_audio(audio=f, title=os.path.basename(latest_file))

        # Remove after sending
        os.remove(latest_file)

    except Exception as e:
        await update.message.reply_text(f"⚠️ YouTube error: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("✅ Bot running…")
    app.run_polling()
