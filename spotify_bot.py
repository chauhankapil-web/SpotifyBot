import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config.config import TOKEN
import os
TOKEN = os.environ['8228790586:AAGaP0CYYvFP65Atb9OW9h-D85HrDrdYmEI']
import yt_dlp

# Replace with your bot token
TOKEN = "8228790586:AAGaP0CYYvFP65Atb9OW9h-D85HrDrdYmEI"

# Make downloads folder if not exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send /play <song name> to download a song from YouTube.")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a search query: /play <song name>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"Searching and downloading: {query} ...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            video = info['entries'][0]
            file_path = ydl.prepare_filename(video)
        
        # Send downloaded audio
        await update.message.reply_audio(audio=open(file_path, 'rb'), title=video['title'])
    
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))

    print("Bot is running...")
    app.run_polling()
