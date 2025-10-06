import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp

# Load environment variables from .env file
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

# FFmpeg path
FFMPEG_PATH = r"C:\Users\LATITUDE 5501\Downloads\Video\video\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe"  # <-- replace with your actual path

# Ensure downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Hello! Send me a song name and I will give Spotify info + downloadable audio from YouTube."
    )

# Main handler for messages
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
        # File path for cached audio
        safe_name = "".join([c for c in query if c.isalnum() or c in " _-"])
        file_path = os.path.join("downloads", f"{safe_name}.mp3")

        if os.path.exists(file_path):
            # If file already exists, send it directly
            with open(file_path, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file, title=query)
            return

        # Notify user before download
        await update.message.reply_text("⏳ Downloading audio from YouTube, please wait...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'nocheckcertificate': True,
            'ffmpeg_location': FFMPEG_PATH,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            video = info['entries'][0]
            downloaded_file = ydl.prepare_filename(video)
            mp3_file = os.path.splitext(downloaded_file)[0] + ".mp3"

        if os.path.exists(mp3_file):
            with open(mp3_file, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file, title=video['title'])
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
