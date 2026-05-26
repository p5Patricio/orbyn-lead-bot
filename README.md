# Orbyn Lead Qualification Bot

Orbyn Lead Qualification Bot is a Python Telegram bot that qualifies inbound B2B leads with Groq and stores every decision in Google Sheets.

The bot checks whether each lead matches this ICP:

- Service or consulting company
- 5 or more employees
- Spain or LATAM market
- Clear automation, AI, efficiency, or process optimization need

## Features

- Telegram polling with `python-telegram-bot`
- Groq lead analysis with JSON-only responses
- Google Sheets logging through a service account
- Environment-based configuration with `pydantic-settings`
- Safe defaults for local credentials through `.gitignore`

## Project structure

```text
.
├── config.py          # Environment configuration
├── llm_service.py     # Groq lead analysis logic
├── main.py            # Telegram bot entry point
├── sheets_service.py  # Google Sheets logging logic
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## Requirements

- Python 3.11 or newer
- Telegram bot token from BotFather
- Groq API key
- Google Cloud service account JSON credentials
- A Google Sheet shared with the service account email

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a local `.env` file in the project root:

   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   GROQ_API_KEY=your_groq_api_key
   GOOGLE_SHEET_ID=your_google_sheet_id
   GOOGLE_CREDS_JSON={"type":"service_account","project_id":"..."}
   ```

4. Set `GOOGLE_CREDS_JSON` to the raw JSON string from the Google service
   account credentials file. In cloud environments, add the full JSON object as
   an environment variable or secret.

5. Share the target Google Sheet with the service account email from the
   credentials JSON.

## Running the bot

Start the bot with:

```bash
python main.py
```

Then open Telegram, start the bot, and send a lead description. The bot will analyze the lead, save the result to Google Sheets, and reply with the final decision.

## Security notes

The following local files and directories are intentionally ignored by git:

- `.env`
- `google_creds.json`
- `venv/`
- `__pycache__/`

Do not commit API keys, Telegram tokens, Google credentials, or generated virtual environment files.
