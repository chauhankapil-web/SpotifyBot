import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()

# Tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Spotify API auth
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Hello! Send /play <song name> to get Spotify song info instantly.")

# Play command
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a song name: /play <song name>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching for: {query}...")

    try:
        # Search song on Spotify
        result = sp.search(q=query, limit=1, type='track')
        if not result['tracks']['items']:
            await update.message.reply_text("❌ No song found.")
            return

        track = result['tracks']['items'][0]
        song_name = track['name']
        artist = track['artists'][0]['name']
        url = track['external_urls']['spotify']
        thumbnail = track['album']['images'][0]['url']
        preview = track['preview_url']

        msg = f"🎶 *{song_name}* — {artist}\n🔗 [Open in Spotify]({url})"
        if preview:
            msg += f"\n▶️ [Preview Track]({preview})"

        await update.message.reply_photo(photo=thumbnail, caption=msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))

    print("✅ Bot is running...")
    app.run_polling()
