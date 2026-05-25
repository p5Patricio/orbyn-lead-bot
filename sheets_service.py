"""Google Sheets service for storing lead qualification records."""

import logging
from datetime import datetime, timezone

import gspread

from config import get_settings

logger = logging.getLogger(__name__)
CREDENTIALS_FILE = "google_creds.json"


def log_lead(raw_data: str, decision: str, reason: str) -> None:
    """Append a lead qualification record to the configured Google Sheet."""
    settings = get_settings()
    created_at = datetime.now(timezone.utc).isoformat()
    row = [created_at, raw_data, decision, reason]

    try:
        logger.info("Connecting to Google Sheets.")
        client = gspread.service_account(filename=CREDENTIALS_FILE)
        sheet = client.open_by_key(settings.google_sheet_id).sheet1
        sheet.append_row(row)
        logger.info("Lead qualification record appended to Google Sheets.")
    except Exception:
        logger.exception("Failed to append lead qualification record.")
        raise
