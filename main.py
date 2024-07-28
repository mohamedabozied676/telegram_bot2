import yt_dlp
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import os
from flask import Flask, request

# Use the provided API token
API_TOKEN = '7043298724:AAGyeN7pOTbK0lnWogg3l-GpGodCJWxjOQg'
bot = Bot(API_TOKEN)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app to keep the bot alive
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "OK"

# Command handler for the /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Send me a YouTube video URL and I will download it for you!')

# Progress hook for yt-dlp
def progress_hook(d):
    if d['status'] == 'downloading':
        message = f"Downloading: {d['_percent_str']} of {d['_total_bytes_str']} at {d['_speed_str']} ETA: {d['_eta_str']}"
        logger.info(message)
        # You can use `bot.send_message(chat_id=context.chat_id, text=message)` to send updates to the user

# Message handler for downloading the video
async def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    logger.info(f'Received URL: {url}')

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
        }

        # Create the 'downloads' directory if it does not exist
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)

        logger.info(f'Video downloaded to: {file_path}')

        # Check the file size and send appropriately
        if os.path.getsize(file_path) <= 50 * 1024 * 1024:  # Telegram file size limit for bot is 50MB
            with open(file_path, 'rb') as video_file:
                await update.message.reply_video(video_file)
            await update.message.reply_text('Video downloaded and sent!')
        else:
            await update.message.reply_text('Video is too large to send via Telegram.')

    except Exception as e:
        logger.error(f'Error downloading video: {e}')
        await update.message.reply_text(f'Error: {e}')

# Main function to set up the bot
def main():
    global dp
    application = Application.builder().token(API_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    dp = application.dispatcher

    # Start the Flask server
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
