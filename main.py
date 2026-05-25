"""Telegram polling entry point for the lead qualification bot."""

import asyncio
import logging

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
    """Start the Telegram bot in polling mode."""
    settings = get_settings()
    application = Application.builder().token(settings.telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Starting Telegram polling.")
    application.run_polling()


if __name__ == "__main__":
    main()
