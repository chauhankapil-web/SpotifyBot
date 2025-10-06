import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
from youtubesearchpython import VideosSearch

# Load environment variables
load_dotenv()

# Tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Ensure downloads folder exists
os.makedirs("downloads", exist_ok=True)

# ---- /start command ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Hello! Send me a song name — I'll fetch Spotify info + YouTube audio."
    )

# ---- Main song handler ----
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(f"🔍 Searching for: {query}...")

    # === Spotify Section ===
    try:
        result = sp.search(q=query, limit=1, type='track')
        if result['tracks']['items']:
            track = result['tracks']['items'][0]
            name = track['name']
            artist = track['artists'][0]['name']
            url = track['external_urls']['spotify']
            image = track['album']['images'][0]['url']
            preview = track['preview_url']

            msg = f"🎶 *{name}* — {artist}\n🔗 [Open in Spotify]({url})"
            if preview:
                msg += f"\n▶️ [Preview Track]({preview})"

            await update.message.reply_photo(photo=image, caption=msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No Spotify results found.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Spotify Error: {e}")

    # === YouTube Section ===
    try:
        await update.message.reply_text("🎧 Searching on YouTube...")

        # Fast search first
        search = VideosSearch(query, limit=1)
        video = search.result()['result'][0]
        yt_url = video['link']
        yt_title = video['title']

        await update.message.reply_text(f"🎬 Found: {yt_title}\n🔗 {yt_url}")
        await update.message.reply_text("⏳ Downloading audio... please wait (max 10s)")

        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'nocheckcertificate': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'socket_timeout': 10,   # prevent long timeouts
            'retries': 1,
            'source_address': '0.0.0.0'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=True)
            file_path = ydl.prepare_filename(info)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                await update.message.reply_audio(audio=f, title=info.get('title', 'Audio'))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Failed to find downloaded file.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ YouTube Error: {e}\n(Tip: Try shorter song name or check internet.)")

# ---- Run Bot ----
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Bot is running...")
    app.run_polling()
