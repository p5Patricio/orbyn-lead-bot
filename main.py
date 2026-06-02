"""Telegram polling entry point for the lead qualification bot."""

import asyncio
import logging
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

from telegram import Message, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import get_settings
from llm_service import analyze_lead
from sheets_service import log_lead

WELCOME_MESSAGE = (
    "Welcome to the Lead Qualification Bot.\n\n"
    "Send me a lead description with details such as company type, size, "
    "location, and automation or AI needs. I will analyze it, save the "
    "result, and send you the qualification decision."
)
PROCESSING_MESSAGE = "Processing lead..."
ERROR_MESSAGE = (
    "Sorry, I could not process this lead right now. Please try again later."
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
HEALTH_CHECK_HOST = "0.0.0.0"
HEALTH_CHECK_PORT = 7860
HEALTH_CHECK_RESPONSE = b"Bot is running"


class HealthCheckHandler(SimpleHTTPRequestHandler):
    """Return a simple success response for container health checks."""

    def do_GET(self) -> None:
        """Return a 200 OK response for any GET request."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(HEALTH_CHECK_RESPONSE)))
        self.end_headers()
        self.wfile.write(HEALTH_CHECK_RESPONSE)

    def log_message(self, format: str, *args: object) -> None:
        """Send HTTP server access logs through the application logger."""
        logger.info("Health check request: " + format, *args)


def run_health_check_server() -> None:
    """Start the HTTP health check server required by Hugging Face Spaces."""
    server_address = (HEALTH_CHECK_HOST, HEALTH_CHECK_PORT)
    http_server = HTTPServer(server_address, HealthCheckHandler)
    logger.info("Starting health check server on port %s.", HEALTH_CHECK_PORT)
    http_server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the user starts the bot."""
    del context
    if update.message is not None:
        await update.message.reply_text(WELCOME_MESSAGE)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Qualify incoming lead messages and store the result."""
    del context
    if update.message is None or update.message.text is None:
        return

    lead_text = update.message.text
    processing_message = await update.message.reply_text(PROCESSING_MESSAGE)

    try:
        analysis = await asyncio.to_thread(analyze_lead, lead_text)
        decision = "QUALIFIED" if analysis["qualified"] else "NOT QUALIFIED"
        reason = analysis["reason"]

        await asyncio.to_thread(log_lead, lead_text, decision, reason)
        await _send_result(processing_message, decision, reason)
    except Exception:
        logger.exception("Failed to process lead.")
        await processing_message.edit_text(ERROR_MESSAGE)


async def _send_result(
    processing_message: Message,
    decision: str,
    reason: str,
) -> None:
    """Edit the processing message with the final lead decision."""
    await processing_message.edit_text(f"Decision: {decision}\n\nReason:\n{reason}")


def main() -> None:
    """Start the Telegram bot in webhook or polling mode."""
    settings = get_settings()

    application = Application.builder().token(settings.telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    if settings.webhook_url:
        logger.info("Starting in webhook mode on port %s.", HEALTH_CHECK_PORT)
        application.run_webhook(
            listen=HEALTH_CHECK_HOST,
            port=HEALTH_CHECK_PORT,
            url_path="webhook",
            webhook_url=f"{settings.webhook_url}/webhook",
        )
    else:
        threading.Thread(target=run_health_check_server, daemon=True).start()
        logger.info("Starting Telegram polling.")
        application.run_polling()


if __name__ == "__main__":
    main()
