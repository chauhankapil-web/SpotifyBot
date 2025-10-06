import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp

# Load environment variables
load_dotenv()

# Tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Spotify API authentication
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

# Make sure 'downloads' folder exists
os.makedirs("downloads", exist_ok=True)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Hello! Send /play <song name> to get downloadable music instantly!"
    )

# Play command
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please enter a song name: /play <song name>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching Spotify for: {query}")

    try:
        # Search song on Spotify
        result = sp.search(q=query, limit=1, type='track')
        if not result['tracks']['items']:
            await update.message.reply_text("❌ No song found on Spotify.")
            return

        track = result['tracks']['items'][0]
        song_name = track['name']
        artist = track['artists'][0]['name']
        cover = track['album']['images'][0]['url']

        # Combine name + artist for YouTube search
        search_query = f"{song_name} {artist} audio"

        await update.message.reply_text(f"🎶 Found: {song_name} by {artist}\n⏬ Downloading audio...")

        # yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "outtmpl": f"downloads/{song_name}.%(ext)s",
        }

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([f"ytsearch1:{search_query}"]))

        # Find downloaded file
        file_path = None
        for f in os.listdir("downloads"):
            if f.startswith(song_name):
                file_path = os.path.join("downloads", f)
                break

        if not file_path:
            await update.message.reply_text("⚠️ Could not find downloaded file.")
            return

        # Send audio to user
        await update.message.reply_audio(audio=open(file_path, "rb"), title=song_name, performer=artist, thumbnail=cover)
        await update.message.reply_text("✅ Song sent successfully!")

        # Delete after sending
        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# Main function
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))

    print("✅ Spotify + YouTube Bot is running...")
    app.run_polling()
