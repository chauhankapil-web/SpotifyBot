import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp

# Load environment variables
load_dotenv()

# Tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Ensure downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Hello! Send me a song name and I will give Spotify info + downloadable audio from YouTube."
    )

# Main handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(f"🔍 Searching for: {query}...")

    # --- Spotify part ---
    try:
        spotify_result = sp.search(q=query, limit=1, type='track')
        if spotify_result['tracks']['items']:
            track = spotify_result['tracks']['items'][0]
            song_name = track['name']
            artist = track['artists'][0]['name']
            spotify_url = track['external_urls']['spotify']
            thumbnail = track['album']['images'][0]['url']
            preview = track['preview_url']

            msg = f"🎶 *{song_name}* — {artist}\n🔗 [Open in Spotify]({spotify_url})"
            if preview:
                msg += f"\n▶️ [Preview Track]({preview})"
            
            await update.message.reply_photo(photo=thumbnail, caption=msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No Spotify results found.")
    except Exception as e:
        await update.message.reply_text(f"❌ Spotify Error: {e}")

    # --- YouTube part ---
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            video = info['entries'][0]
            file_path = ydl.prepare_filename(video)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file, title=video['title'])
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Failed to download audio from YouTube.")

    except Exception as e:
        await update.message.reply_text(f"❌ YouTube Error: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Bot is running...")
    app.run_polling()
