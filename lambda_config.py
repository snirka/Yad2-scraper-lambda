"""
Lambda-specific configuration for Yad2 Car Scraper.

This module provides configuration specifically optimized for AWS Lambda environment.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Lambda-specific settings
LAMBDA_TIMEOUT = 900  # 15 minutes (max for Lambda)
LAMBDA_MEMORY = 512   # MB
LAMBDA_RUNTIME = "python3.9"

# Base URLs (same as main config)
YAD2_BASE_URL = "https://www.yad2.co.il"
YAD2_CARS_URL = "https://www.yad2.co.il/vehicles/cars"
YAD2_API_BASE = "https://gw.yad2.co.il"

# Scraping configuration optimized for Lambda
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1  # Reduced for faster execution in Lambda
MAX_RETRIES = 2    # Reduced for Lambda timeout constraints

# User agents for rotating requests
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebLib/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
}

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

# Common manufacturer IDs (for reference in environment variables)
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
}