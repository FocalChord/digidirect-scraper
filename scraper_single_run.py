"""Single run scraper for GitHub Actions."""
import asyncio
import logging
import sys
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
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def run_scrape_sync():
    """Run scraping synchronously."""
    logger.info("Starting scrape cycle")
    
    scraper = Scraper(config.site_config, config.headless_browser)
    storage = Storage(config.state_file)
    
    previous_state = storage.load_state()
    previous_products = storage.get_products_from_state(previous_state)
    
    logger.info(f"Scraping {config.site_config['name']}...")
    current_products = scraper.scrape()
    
    return previous_products, current_products


async def main():
    """Main function for single run."""
    try:
        config.validate()
        
        # Run scraping
        previous_products, current_products = await asyncio.to_thread(run_scrape_sync)
        
        if not current_products:
            logger.error("No products found")
            return False
        
        logger.info(f"Found {len(current_products)} products")
        
        # Initialize components
        notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
        storage = Storage(config.state_file)
        
        # Compare and notify
        if Differ.is_first_run(previous_products):
            logger.info("First run - establishing baseline")
        else:
            diff = Differ.compare(previous_products, current_products)
            
            if diff.has_changes():
                logger.info(f"Changes detected: {diff.get_summary()}")
                await notifier.send_diff_notifications(diff, config.site_config['name'])
            else:
                logger.info("No changes detected")
        
        # Save state
        products_dict = [p.to_dict() for p in current_products]
        storage.save_state(products_dict)
        
        logger.info("Scrape completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        
        try:
            notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
            await notifier.send_error_notification(str(e))
        except:
            pass
        
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

