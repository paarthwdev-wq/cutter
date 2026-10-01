"""
Main entrypoint for Telegram AI Video Clipper Bot.
"""
import sys
import os
from pathlib import Path

# Add project root and /app to sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import logging
from telegram_clipper.telegram_bot.bot import build_application
from telegram_clipper.config.settings import TELEGRAM_BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("telegram_clipper")

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Telegram Clipper Bot is Running!")

def run_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

def main():
    print("=" * 60)
    print(" [READY] Telegram AI Video Clipping Bot (Render & Cloud Ready)")
    print("=" * 60)

    # Start health server on Render $PORT in background thread
    if os.environ.get("PORT"):
        t = threading.Thread(target=run_health_server, daemon=True)
        t.start()
        print(f"[*] Cloud Health Check Server running on port {os.environ.get('PORT')}")

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("\n[ERROR] TELEGRAM_BOT_TOKEN is missing or not configured in .env.")
        print("Please edit .env and provide your Telegram Bot Token obtained from @BotFather.")
        print("Example:\n  TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ\n")
        sys.exit(1)

    print("[*] Initializing Telegram bot polling engine...")
    app = build_application()
    print("[SUCCESS] Bot is online and listening for messages! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
