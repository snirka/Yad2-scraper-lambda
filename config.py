"""Configuration file for Yad2 Car Scraper."""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Base URLs
YAD2_BASE_URL = "https://www.yad2.co.il"
YAD2_CARS_URL = "https://www.yad2.co.il/vehicles/cars"
YAD2_API_BASE = "https://gw.yad2.co.il"

# File paths
DATA_DIR = "data"
MANUFACTURERS_FILE = os.path.join(DATA_DIR, "manufacturers.json")
MODELS_FILE = os.path.join(DATA_DIR, "models.json")
LISTINGS_CACHE_FILE = os.path.join(DATA_DIR, "listings_cache.json")
FILTERS_FILE = os.path.join(DATA_DIR, "filters.json")

# Telegram configuration
TELEGRAM_CONFIG_FILE = os.path.join(DATA_DIR, "telegram_config.json")

# Scraping configuration
SCRAPE_INTERVAL_MINUTES = 15
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 2  # seconds between requests
DELAY_BETWEEN_REQUESTS = 2  # seconds

# User agents for rotating requests
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# HTTP headers for requests
DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,he;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

# Logging configuration
LOG_FILE = os.path.join(DATA_DIR, "scraper.log")
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

@dataclass
class SearchFilter:
    """Represents a search filter for car listings."""
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    km: Optional[str] = None
    price: Optional[str] = None
    hand: Optional[str] = None
    engine_size: Optional[str] = None
    gear: Optional[str] = None
    color: Optional[str] = None
    area: Optional[str] = None
    
    def to_url_params(self) -> Dict[str, str]:
        """Convert filter to URL parameters."""
        params = {}
        
        if self.manufacturer:
            params['manufacturer'] = self.manufacturer
        if self.model:
            params['model'] = self.model
        if self.year:
            params['year'] = self.year
        if self.km:
            params['km'] = self.km
        if self.price:
            params['price'] = self.price
        if self.hand:
            params['hand'] = self.hand
        if self.engine_size:
            params['engine_size'] = self.engine_size
        if self.gear:
            params['gear'] = self.gear
        if self.color:
            params['color'] = self.color
        if self.area:
            params['area'] = self.area
            
        return params
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'year': self.year,
            'km': self.km,
            'price': self.price,
            'hand': self.hand,
            'engine_size': self.engine_size,
            'gear': self.gear,
            'color': self.color,
            'area': self.area
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchFilter':
        """Create SearchFilter from dictionary."""
        return cls(**data)

# Default search filters (can be overridden by user configuration)
DEFAULT_SEARCH_FILTERS = {
    'manufacturer': '37',     # e.g., 37 for Seat
    'model': '10507',         # e.g., 10507 for Ibiza  
    'year': '2012-2016',      # e.g., '2012-2015'
    'km': '1-100000',         # e.g., '-1-89000' (from 1 to 89000)
    'price': None,            # e.g., '50000-150000'
    'hand': None,             # e.g., '1' for first hand
    'engine_size': None,      # e.g., '1000-1600'
    'gear': None,             # e.g., 'auto' or 'manual'
    'color': None,            # color code
    'area': None,             # area code
}

# Common manufacturer IDs (REAL DATA from Yad2 API!)
COMMON_MANUFACTURERS = {
    '1': 'אאודי (Audi)',
    '13': 'טויוטה (Toyota)', 
    '19': 'יונדאי (Hyundai)',
    '32': 'ניסן (Nissan)',
    '37': 'סיאט (Seat)',
    '46': 'פולקסווגן (Volkswagen)',
    '47': 'וולוו (Volvo)',
    '2': 'אופל (Opel)',
    '42': 'סקודה (Skoda)',
    '48': 'BMW',
    '49': 'מרצדס (Mercedes)',
    '50': 'מיצובישי (Mitsubishi)',
    '11': 'הונדה (Honda)',
    '15': 'כרייזלר (Chrysler)',
    '21': 'קיה (Kia)',
    '22': 'לקסוס (Lexus)',
    '25': 'מאזדה (Mazda)',
    '33': 'פיאט (Fiat)',
    '34': 'פיג\'ו (Peugeot)',
    '39': 'סובארו (Subaru)',
    '41': 'סוזוקי (Suzuki)',
    '16': 'דייהטסו (Daihatsu)',
    '26': 'מיני (MINI)',
    '5': 'אלפא רומיאו (Alfa Romeo)',
    '35': 'פורד (Ford)',
    '36': 'רנו (Renault)',
    '4': 'איסוזו (Isuzu)',
    '18': 'יגואר (Jaguar)',
    '3': 'אינפיניטי (Infiniti)',
    '23': 'לנד רובר (Land Rover)',
    '24': 'לינקולן (Lincoln)',
    '27': 'מיצובישי (Mitsubishi)',
    '28': 'נטיסאן (Nissan)',
    '30': 'פונטיאק (Pontiac)',
    '31': 'פורשה (Porsche)',
    '38': 'סמארט (Smart)',
    '40': 'סאאב (Saab)',
    '43': 'טסלה (Tesla)',
    '44': 'דאצ\'יה (Dacia)',
    '45': 'קדילק (Cadillac)'
}

def ensure_data_directory():
    """Ensure the data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

# Initialize data directory when module is imported
ensure_data_directory()