import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from youtubesearchpython import VideosSearch

# Your Telegram bot token
TOKEN = "8228790586:AAGaP0CYYvFP65Atb9OW9h-D85HrDrdYmEI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Hello! Send /play <song name> to get YouTube link instantly."
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a search query: /play <song name>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching for: {query}...")

    try:
        videos_search = VideosSearch(query, limit=1)
        result = videos_search.result()["result"][0]

        title = result["title"]
        url = result["link"]
        thumbnail = result["thumbnails"][0]["url"]

        message = f"🎶 *{title}*\n🔗 [Watch on YouTube]({url})"
        await update.message.reply_photo(photo=thumbnail, caption=message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))

    print("✅ Bot is running and ready!")
    app.run_polling()
