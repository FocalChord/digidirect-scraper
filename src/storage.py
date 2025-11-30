"""Storage module for persisting product state in JSON format."""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Storage:
    """JSON-based storage for product state."""
    
    def __init__(self, state_file: Path):
        """Initialize storage with state file path.
        
        Args:
            state_file: Path to JSON state file
        """
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load previous state from JSON file.
        
        Returns:
            Dictionary containing previous state or None if no state exists
        """
        if not self.state_file.exists():
            logger.info("No previous state found")
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            logger.info(f"Loaded state with {len(state.get('products', []))} products")
            return state
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return None
    
    def save_state(self, products: List[Dict[str, Any]]) -> bool:
        """Save current state to JSON file.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            True if save was successful
        """
        state = {
            'last_check': datetime.now().isoformat(),
            'total_products': len(products),
            'products': products
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Saved state with {len(products)} products")
            return True
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False
    
    def get_products_from_state(self, state: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract products list from state.
        
        Args:
            state: State dictionary
            
        Returns:
            List of product dictionaries
        """
        if not state:
            return []
        return state.get('products', [])
    
    def clear_state(self) -> bool:
        """Clear the state file.
        
        Returns:
            True if successful
        """
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                logger.info("State file cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing state: {e}")
            return False

