"""Differ module for detecting changes between product states."""
import logging
from typing import List, Dict, Any
from src.scraper import Product

logger = logging.getLogger(__name__)


class ProductDiff:
    """Container for product differences."""
    
    def __init__(self):
        self.new_products: List[Product] = []
        self.removed_products: List[Product] = []
        self.price_changes: List[Dict[str, Any]] = []
    
    def has_changes(self) -> bool:
        """Check if there are any changes.
        
        Returns:
            True if there are any changes
        """
        return bool(self.new_products or self.removed_products or self.price_changes)
    
    def get_summary(self) -> str:
        """Get a summary of changes.
        
        Returns:
            String summary
        """
        parts = []
        if self.new_products:
            parts.append(f"{len(self.new_products)} new")
        if self.removed_products:
            parts.append(f"{len(self.removed_products)} removed")
        if self.price_changes:
            parts.append(f"{len(self.price_changes)} price changes")
        
        if not parts:
            return "No changes"
        
        return ", ".join(parts)


class Differ:
    """Compare product states and detect changes."""
    
    @staticmethod
    def compare(previous_products: List[Dict[str, Any]], 
                current_products: List[Product]) -> ProductDiff:
        """Compare previous and current product states.
        
        Args:
            previous_products: List of previous product dictionaries
            current_products: List of current Product objects
            
        Returns:
            ProductDiff object containing all changes
        """
        diff = ProductDiff()
        
        # Convert previous products to Product objects for easier comparison
        previous = {p['sku']: Product.from_dict(p) for p in previous_products}
        current = {p.sku: p for p in current_products}
        
        # Find new products
        new_skus = set(current.keys()) - set(previous.keys())
        diff.new_products = [current[sku] for sku in new_skus]
        
        # Find removed products
        removed_skus = set(previous.keys()) - set(current.keys())
        diff.removed_products = [previous[sku] for sku in removed_skus]
        
        # Find price changes
        common_skus = set(current.keys()) & set(previous.keys())
        for sku in common_skus:
            prev_product = previous[sku]
            curr_product = current[sku]
            
            if prev_product.price != curr_product.price:
                diff.price_changes.append({
                    'product': curr_product,
                    'old_price': prev_product.price,
                    'new_price': curr_product.price,
                    'change': curr_product.price - prev_product.price
                })
        
        logger.info(f"Diff results: {diff.get_summary()}")
        
        return diff
    
    @staticmethod
    def is_first_run(previous_products: List[Dict[str, Any]]) -> bool:
        """Check if this is the first run (no previous state).
        
        Args:
            previous_products: List of previous product dictionaries
            
        Returns:
            True if this is the first run
        """
        return len(previous_products) == 0

