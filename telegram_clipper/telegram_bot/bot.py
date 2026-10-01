"""
Telegram Bot Application Initializer and Dispatcher.
"""
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram_clipper.config.settings import TELEGRAM_BOT_TOKEN
from telegram_clipper.telegram_bot.handlers import (
    start_command,
    help_command,
    status_command,
    handle_url_message
)

logger = logging.getLogger(__name__)

def build_application() -> Application:
    """Build and configure the Telegram Bot Application."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env! Please configure your token.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("clip", handle_url_message))

    # Catch direct text messages (like pasted YouTube URLs)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message))

    return app
