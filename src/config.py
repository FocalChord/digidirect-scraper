"""Configuration module for loading environment variables and site configs."""
import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Main configuration class."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Telegram settings
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Scraper settings
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))
        self.headless_browser = os.getenv('HEADLESS_BROWSER', 'true').lower() == 'true'
        
        # Site configuration file path
        self.site_config_path = os.getenv('SITE_CONFIG', 'config/sites/digidirect.json')
        
        # Data directory
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        self.state_file = self.data_dir / 'products_state.json'
        
        # Load site configuration
        self.site_config = self._load_site_config()
    
    def _load_site_config(self) -> Dict[str, Any]:
        """Load site-specific configuration from JSON file."""
        config_path = Path(self.site_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Site config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        if not self.telegram_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is not set")
        if not self.site_config:
            raise ValueError("Site configuration could not be loaded")
        return True


# Global config instance
config = Config()

