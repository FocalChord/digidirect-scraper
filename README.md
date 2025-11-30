# DigiDirect Scraper

Monitors DigiDirect for Leica products and sends Telegram notifications on changes.

## Setup

### GitHub Actions

1. Add secrets in Settings > Secrets and variables > Actions:
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_CHAT_ID
2. Enable Actions in repo settings
3. Runs every 5 minutes automatically

### Local

1. Install dependencies: `pip install -r requirements.txt && playwright install chromium`
2. Create `.env` file with your tokens
3. Run: `python main.py`

## Features

- Monitors Leica products every 5 minutes
- Telegram notifications for new products, removals, price changes
- Generic and configurable for other sites

