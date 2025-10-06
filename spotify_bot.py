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

# Load environment variables
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
        "🎵 Send a song name — Spotify info + fast YouTube audio download (cached)."
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

    # --- YouTube download with caching ---
    # Sanitize file name
    safe_filename = "".join(c for c in query if c.isalnum() or c in " _-").rstrip()
    cached_file_path = os.path.join(DOWNLOADS_DIR, f"{safe_filename}.m4a")

    if os.path.exists(cached_file_path):
        # Send cached file
        await update.message.reply_text("✅ Sending cached audio...")
        with open(cached_file_path, "rb") as f:
            await update.message.reply_audio(audio=f, title=safe_filename)
        return

    await update.message.reply_text("⏳ Downloading audio from YouTube, please wait...")

    cmd = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "--no-playlist",
        "--no-check-certificate",
        "-o", cached_file_path,
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

        # Send downloaded file
        with open(cached_file_path, "rb") as f:
            await update.message.reply_audio(audio=f, title=safe_filename)

    except Exception as e:
        await update.message.reply_text(f"⚠️ YouTube error: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("✅ Bot running…")
    app.run_polling()
