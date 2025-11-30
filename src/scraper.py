"""Web scraper module using Playwright for JavaScript-rendered pages."""
import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class Product:
    """Product data class."""
    
    def __init__(self, sku: str, title: str, price: float, original_price: Optional[float],
                 url: str, image: str, discount: Optional[str] = None):
        self.sku = sku
        self.title = title
        self.price = price
        self.original_price = original_price
        self.url = url
        self.image = image
        self.discount = discount
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary."""
        return {
            'sku': self.sku,
            'title': self.title,
            'price': self.price,
            'original_price': self.original_price,
            'url': self.url,
            'image': self.image,
            'discount': self.discount
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create product from dictionary."""
        return cls(
            sku=data['sku'],
            title=data['title'],
            price=data['price'],
            original_price=data.get('original_price'),
            url=data['url'],
            image=data['image'],
            discount=data.get('discount')
        )
    
    def __eq__(self, other):
        """Compare products by SKU."""
        if not isinstance(other, Product):
            return False
        return self.sku == other.sku
    
    def __hash__(self):
        """Hash product by SKU."""
        return hash(self.sku)


class Scraper:
    """Generic web scraper using Playwright."""
    
    def __init__(self, site_config: Dict[str, Any], headless: bool = True):
        """Initialize scraper with site configuration.
        
        Args:
            site_config: Dictionary containing site-specific selectors and URLs
            headless: Whether to run browser in headless mode
        """
        self.site_config = site_config
        self.headless = headless
        self.url = site_config['url']
        self.selectors = site_config['selectors']
        self.wait_for_selector = site_config['wait_for_selector']
        self.wait_timeout = site_config.get('wait_timeout', 30000)
    
    def scrape(self) -> List[Product]:
        """Scrape products from the configured website.
        
        Returns:
            List of Product objects
        """
        logger.info(f"Starting scrape of {self.url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Navigate to URL
                logger.info("Navigating to page...")
                page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                
                # Handle cookie popup if present
                try:
                    logger.info("Checking for cookie popup...")
                    cookie_button = page.locator('button:has-text("Allow Cookies")').first
                    if cookie_button.is_visible(timeout=5000):
                        logger.info("Clicking cookie accept button...")
                        cookie_button.click()
                        page.wait_for_timeout(1000)
                except Exception as e:
                    logger.info(f"No cookie popup or already dismissed: {e}")
                
                # Wait for products to load
                logger.info(f"Waiting for products selector: {self.wait_for_selector}")
                page.wait_for_selector(self.wait_for_selector, timeout=self.wait_timeout)
                
                # Additional wait for JS rendering
                page.wait_for_timeout(3000)
                
                # Extract products
                products = self._extract_products(page)
                
                browser.close()
                
                logger.info(f"Successfully scraped {len(products)} products")
                return products
                
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout while scraping: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
    
    def _extract_products(self, page: Page) -> List[Product]:
        """Extract product data from the page.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of Product objects
        """
        products = []
        
        # Find all product containers
        product_elements = page.query_selector_all(self.selectors['product_container'])
        
        logger.info(f"Found {len(product_elements)} product elements")
        
        for element in product_elements:
            try:
                product = self._extract_product(element)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error extracting product: {e}")
                continue
        
        return products
    
    def _extract_product(self, element) -> Optional[Product]:
        """Extract product data from a single product element.
        
        Args:
            element: Playwright element locator
            
        Returns:
            Product object or None if extraction fails
        """
        try:
            # Extract URL first (it's on the parent a.result element)
            url_element = element.query_selector(self.selectors['url'])
            if not url_element:
                return None
            url = url_element.get_attribute('href')
            if url and not url.startswith('http'):
                base_url = self.url.split('/digiseconds')[0]
                url = base_url + url
            
            # Extract SKU from URL or data attribute
            data_objectid = url_element.get_attribute('data-objectid')
            if data_objectid:
                sku = data_objectid
            else:
                # Try to extract from URL
                sku = url.split('/')[-1] if url else 'unknown'
            
            # Extract title
            title_element = element.query_selector(self.selectors['title'])
            if not title_element:
                return None
            title = title_element.inner_text().strip()
            
            # Extract price - try multiple selectors for the sale price
            price = None
            price_selectors = [
                self.selectors['price'],
                'span.after_special.custom_final_price',
                'span.custom_final_price.black-friday'
            ]
            for selector in price_selectors:
                price_element = element.query_selector(selector)
                if price_element:
                    price_text = price_element.inner_text().strip()
                    try:
                        price = self._parse_price(price_text)
                        break
                    except:
                        continue
            
            if price is None:
                logger.warning(f"Could not extract price for {title}")
                return None
            
            # Extract original price (optional)
            original_price = None
            original_price_element = element.query_selector(self.selectors['original_price'])
            if original_price_element:
                try:
                    original_price_text = original_price_element.inner_text().strip()
                    original_price = self._parse_price(original_price_text)
                except:
                    pass
            
            # Extract image
            image_element = element.query_selector(self.selectors['image'])
            image = image_element.get_attribute('src') if image_element else ''
            
            # Extract discount (optional)
            discount = None
            discount_selector = self.selectors.get('discount', '')
            if discount_selector:
                discount_element = element.query_selector(discount_selector)
                if discount_element:
                    discount = discount_element.inner_text().strip()
            
            return Product(
                sku=sku,
                title=title,
                price=price,
                original_price=original_price,
                url=url,
                image=image,
                discount=discount
            )
            
        except Exception as e:
            logger.warning(f"Error extracting product details: {e}")
            return None
    
    @staticmethod
    def _parse_price(price_text: str) -> float:
        """Parse price string to float.
        
        Args:
            price_text: Price string like "$6,554.05"
            
        Returns:
            Float price value
        """
        # Remove currency symbols and commas
        clean_price = price_text.replace('$', '').replace(',', '').strip()
        return float(clean_price)

