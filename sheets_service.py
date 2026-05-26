"""Google Sheets service for storing lead qualification records."""

import json
import logging
from datetime import datetime, timezone

import gspread

from config import get_settings

logger = logging.getLogger(__name__)


def log_lead(raw_data: str, decision: str, reason: str) -> None:
    """Append a lead qualification record to the configured Google Sheet."""
    settings = get_settings()
    created_at = datetime.now(timezone.utc).isoformat()
    row = [created_at, raw_data, decision, reason]

    try:
        logger.info("Connecting to Google Sheets.")
        credentials = json.loads(settings.GOOGLE_CREDS_JSON)
        client = gspread.service_account_from_dict(credentials)
        sheet = client.open_by_key(settings.google_sheet_id).sheet1
        sheet.append_row(row)
        logger.info("Lead qualification record appended to Google Sheets.")
    except Exception:
        logger.exception("Failed to append lead qualification record.")
        raise
