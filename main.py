"""Main entry point for the generic scraper notifier."""
import asyncio
import logging
import signal
import sys
import time
from datetime import datetime

from src.config import config
from src.scraper import Scraper
from src.storage import Storage
from src.differ import Differ
from src.notifier import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle interrupt signal for graceful shutdown."""
    global running
    logger.info("Interrupt received, shutting down gracefully...")
    running = False


def run_scrape_cycle_sync():
    """Run a single scrape cycle synchronously."""
    logger.info("=" * 50)
    logger.info(f"Starting scrape cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # Initialize components
    scraper = Scraper(config.site_config, config.headless_browser)
    storage = Storage(config.state_file)
    
    # Load previous state
    previous_state = storage.load_state()
    previous_products = storage.get_products_from_state(previous_state)
    
    # Scrape current products
    logger.info(f"Scraping {config.site_config['name']}...")
    current_products = scraper.scrape()
    
    return previous_products, current_products


async def run_scrape_cycle():
    """Run a single scrape, compare, and notify cycle."""
    try:
        # Run scraping in sync context
        previous_products, current_products = await asyncio.to_thread(run_scrape_cycle_sync)
        
        if not current_products:
            logger.warning("No products found in current scrape")
            return
        
        logger.info(f"Found {len(current_products)} products")
        
        # Initialize notifier and storage
        notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
        storage = Storage(config.state_file)
        
        # Compare with previous state
        if Differ.is_first_run(previous_products):
            logger.info("First run detected - establishing baseline state")
            logger.info("No notifications will be sent on first run")
        else:
            # Detect changes
            diff = Differ.compare(previous_products, current_products)
            
            if diff.has_changes():
                logger.info(f"Changes detected: {diff.get_summary()}")
                
                # Send notifications
                await notifier.send_diff_notifications(diff, config.site_config['name'])
            else:
                logger.info("No changes detected")
        
        # Save current state
        products_dict = [p.to_dict() for p in current_products]
        storage.save_state(products_dict)
        
        logger.info("Scrape cycle completed successfully")
        
    except Exception as e:
        logger.error(f"Error during scrape cycle: {e}", exc_info=True)
        
        # Try to send error notification
        try:
            notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
            await notifier.send_error_notification(str(e))
        except Exception as notify_error:
            logger.error(f"Could not send error notification: {notify_error}")


async def test_telegram_connection():
    """Test Telegram bot connection and send test message."""
    try:
        logger.info("Testing Telegram connection...")
        notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
        success = await notifier.send_test_message()
        
        if success:
            logger.info("Telegram connection successful")
            return True
        else:
            logger.error("Telegram connection test failed")
            return False
    except Exception as e:
        logger.error(f"Error testing Telegram connection: {e}")
        return False


async def main():
    """Main function with scheduling loop."""
    global running
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("Generic Scraper Notifier Starting")
    logger.info("=" * 50)
    
    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
    
    # Test Telegram connection
    telegram_ok = await test_telegram_connection()
    if not telegram_ok:
        logger.error("Telegram connection failed. Please check your bot token and chat ID.")
        sys.exit(1)
    
    logger.info(f"Monitoring: {config.site_config['name']}")
    logger.info(f"URL: {config.site_config['url']}")
    logger.info(f"Check interval: {config.check_interval} seconds")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)
    
    # Run first cycle immediately
    await run_scrape_cycle()
    
    # Schedule regular runs
    while running:
        try:
            # Wait for the check interval
            for _ in range(config.check_interval):
                if not running:
                    break
                await asyncio.sleep(1)
            
            if running:
                await run_scrape_cycle()
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            # Wait a bit before retrying
            await asyncio.sleep(60)
    
    logger.info("Scraper stopped")


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

