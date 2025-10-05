import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from ytmusicapi import YTMusic

# Telegram bot token
TOKEN = "8228790586:AAGaP0CYYvFP65Atb9OW9h-D85HrDrdYmEI"

ytmusic = YTMusic()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Hello! Send /play <song name> to get a YouTube Music link instantly."
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a search query: /play <song name>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching for: {query}...")

    try:
        results = ytmusic.search(query, filter="songs", limit=1)
        if not results:
            await update.message.reply_text("❌ No results found.")
            return

        song = results[0]
        title = song["title"]
        artists = ", ".join([artist["name"] for artist in song["artists"]])
        video_id = song["videoId"]
        thumbnail = song["thumbnails"][-1]["url"]
        url = f"https://music.youtube.com/watch?v={video_id}"

        message = f"🎶 *{title}*\n👤 {artists}\n🔗 [Listen on YouTube Music]({url})"
        await update.message.reply_photo(photo=thumbnail, caption=message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))

    print("✅ Bot is running...")
    app.run_polling()
