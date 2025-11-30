"""Notifier module for sending Telegram notifications."""
import logging
from typing import Dict, Any
from telegram import Bot
from telegram.error import TelegramError
from src.scraper import Product
from src.differ import ProductDiff

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
        """
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
    
    async def send_diff_notifications(self, diff: ProductDiff, site_name: str = "Products"):
        """Send notifications for all changes in diff.
        
        Args:
            diff: ProductDiff object containing changes
            site_name: Name of the site being monitored
        """
        if not diff.has_changes():
            logger.info("No changes to notify")
            return
        
        logger.info(f"Sending notifications for: {diff.get_summary()}")
        
        # Send notifications for new products
        for product in diff.new_products:
            await self._send_new_product_notification(product, site_name)
        
        # Send notifications for removed products
        for product in diff.removed_products:
            await self._send_removed_product_notification(product, site_name)
        
        # Send notifications for price changes
        for change in diff.price_changes:
            await self._send_price_change_notification(change, site_name)
    
    async def _send_new_product_notification(self, product: Product, site_name: str):
        """Send notification for a new product.
        
        Args:
            product: Product object
            site_name: Name of the site
        """
        # Format price display
        price_display = f"${product.price:,.2f}"
        if product.original_price and product.original_price > product.price:
            price_display += f" (was ${product.original_price:,.2f})"
        
        message = (
            f"🆕 New {site_name} Product!\n\n"
            f"{product.title}\n"
            f"💰 {price_display}\n"
            f"🏷️ SKU: {product.sku}\n\n"
            f"🔗 <a href='{product.url}'>View Product</a>"
        )
        
        try:
            if product.image:
                # Send with image
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=product.image,
                    caption=message,
                    parse_mode='HTML'
                )
            else:
                # Send text only
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )
            logger.info(f"Sent new product notification for SKU {product.sku}")
        except TelegramError as e:
            logger.error(f"Error sending new product notification: {e}")
    
    async def _send_removed_product_notification(self, product: Product, site_name: str):
        """Send notification for a removed product.
        
        Args:
            product: Product object
            site_name: Name of the site
        """
        message = (
            f"❌ Product No Longer Available\n\n"
            f"{product.title}\n"
            f"🏷️ SKU: {product.sku}\n"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Sent removed product notification for SKU {product.sku}")
        except TelegramError as e:
            logger.error(f"Error sending removed product notification: {e}")
    
    async def _send_price_change_notification(self, change: Dict[str, Any], site_name: str):
        """Send notification for a price change.
        
        Args:
            change: Dictionary with product, old_price, new_price, change
            site_name: Name of the site
        """
        product = change['product']
        old_price = change['old_price']
        new_price = change['new_price']
        price_change = change['change']
        
        # Determine if price increased or decreased
        if price_change > 0:
            emoji = "📈"
            change_text = f"+${abs(price_change):,.2f}"
        else:
            emoji = "📉"
            change_text = f"-${abs(price_change):,.2f}"
        
        message = (
            f"💲 Price Update!\n\n"
            f"{product.title}\n"
            f"{emoji} ${old_price:,.2f} → ${new_price:,.2f} ({change_text})\n"
            f"🏷️ SKU: {product.sku}\n\n"
            f"🔗 <a href='{product.url}'>View Product</a>"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            logger.info(f"Sent price change notification for SKU {product.sku}")
        except TelegramError as e:
            logger.error(f"Error sending price change notification: {e}")
    
    async def send_test_message(self):
        """Send a test message to verify bot configuration.
        
        Returns:
            True if successful
        """
        message = "✅ Generic Scraper Notifier is running!"
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            logger.info("Test message sent successfully")
            return True
        except TelegramError as e:
            logger.error(f"Error sending test message: {e}")
            return False
    
    async def send_error_notification(self, error_message: str):
        """Send error notification.
        
        Args:
            error_message: Error message to send
        """
        message = f"⚠️ Scraper Error\n\n{error_message}"
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("Error notification sent")
        except TelegramError as e:
            logger.error(f"Error sending error notification: {e}")

