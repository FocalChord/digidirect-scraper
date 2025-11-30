# Generic Scraper Notifier

Monitors DigiDirect for Leica products and sends Telegram notifications on changes.

## Setup

### GitHub Actions (Recommended - Free)

1. Fork/create this repo on GitHub
2. Add secrets in Settings → Secrets and variables → Actions:
   - `TELEGRAM_BOT_TOKEN`: Your bot token
   - `TELEGRAM_CHAT_ID`: Your chat ID
3. Enable Actions in repo settings
4. Done! Runs every 5 minutes automatically

### Local

1. Install: `pip install -r requirements.txt && playwright install chromium`
2. Create `.env` with your tokens
3. Run: `python main.py`

## Features

- Monitors Leica products every 5 minutes
- Telegram notifications for new products, removals, price changes
- Generic/configurable for other sites

