"""Core scraper functionality for Yad2 car listings."""

import json
import logging
import os
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlencode
from dataclasses import dataclass
from datetime import datetime

from config import (
    YAD2_CARS_URL, USER_AGENTS, REQUEST_DELAY, REQUEST_TIMEOUT, MAX_RETRIES,
    DATA_DIR, LISTINGS_CACHE_FILE, SearchFilter
)

# Import S3 storage for Lambda compatibility
try:
    from s3_storage import get_s3_storage, should_use_s3
except ImportError:
    # S3 storage not available (local mode)
    get_s3_storage = None
    should_use_s3 = lambda: False


@dataclass
class CarListing:
    """Represents a car listing from Yad2."""
    id: str
    title: str
    price: str
    year: str
    km: str
    manufacturer: str
    model: str
    url: str
    image_url: Optional[str] = None
    location: Optional[str] = None
    hand: Optional[str] = None
    engine_size: Optional[str] = None
    gear: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    first_seen: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'year': self.year,
            'km': self.km,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'url': self.url,
            'image_url': self.image_url,
            'location': self.location,
            'hand': self.hand,
            'engine_size': self.engine_size,
            'gear': self.gear,
            'color': self.color,
            'description': self.description,
            'first_seen': self.first_seen or datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CarListing':
        """Create listing from dictionary."""
        return cls(**data)


class Yad2Scraper:
    """Main scraper class for Yad2 car listings."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.logger = self._setup_logging()
        self._ensure_data_dir()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration for Lambda/CloudWatch."""
        logger = logging.getLogger('yad2_scraper')
        logger.setLevel(logging.INFO)  # Use INFO level for production
        
        # Only add handler if none exists (avoid duplicate logs)
        if not logger.handlers:
            # Console handler only (Lambda sends this to CloudWatch)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter optimized for CloudWatch
            formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
            console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
        
        return logger
    
    def _ensure_data_dir(self):
        """Ensure data directory exists (for local mode only)."""
        # Skip directory creation in Lambda environment
        if not os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            os.makedirs(DATA_DIR, exist_ok=True)
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        return random.choice(USER_AGENTS)
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Make a HTTP request with retries and random delays.
        
        Args:
            url: URL to request
            params: Query parameters
            
        Returns:
            Response object or None if failed
        """
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'he-IL,he;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                self.logger.info(f"Making request to {url} (attempt {attempt + 1})")
                
                # Add random delay to avoid being blocked
                time.sleep(REQUEST_DELAY + random.uniform(0, 2))
                
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limited, wait longer
                    wait_time = (attempt + 1) * 5
                    self.logger.warning(f"Rate limited, waiting {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                self.logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep((attempt + 1) * 2)
        
        self.logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts")
        return None
    
    def _parse_listing_element(self, element) -> Optional[CarListing]:
        """
        Parse a car listing element from the HTML.
        
        Args:
            element: BeautifulSoup element containing listing data
            
        Returns:
            CarListing object or None if parsing failed
        """
        try:
            # Extract listing ID from data attributes or URL
            listing_id = None
            
            # First, try to get ID from data-testid (Yad2's current pattern)
            listing_id = element.get('data-testid')
            
            # If not found, try from URL
            if not listing_id:
                link_elem = element.find('a', href=True)
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    # Try to extract ID from URL
                    if '/item/' in href:
                        listing_id = href.split('/item/')[-1].split('?')[0]
                    elif 'itemId=' in href:
                        listing_id = href.split('itemId=')[-1].split('&')[0]
            
            # Fallback: try other data attributes
            if not listing_id:
                listing_id = element.get('data-item-id') or element.get('data-id')
            
            if not listing_id:
                # Log more details about the element for debugging
                element_html = str(element)[:200] + "..." if len(str(element)) > 200 else str(element)
                self.logger.warning(f"Could not extract listing ID from element: {element_html}")
                return None
            
            # Extract title
            title_elem = element.find(['h3', 'h4', '.title', '.item-title']) or element.find('a')
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            # Extract price
            price_elem = element.find(['span', 'div'], class_=lambda x: x and ('price' in x.lower() or 'cost' in x.lower()))
            if not price_elem:
                price_elem = element.find(string=lambda text: text and '₪' in text)
                if price_elem:
                    price_elem = price_elem.parent
            price = price_elem.get_text(strip=True) if price_elem else "Price not listed"
            
            # Extract URL
            url = ""
            link_elem = element.find('a', href=True)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                if href.startswith('/'):
                    url = urljoin(YAD2_CARS_URL, href)
                else:
                    url = href
            
            # Extract image URL
            img_elem = element.find('img')
            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
            if image_url and image_url.startswith('/'):
                image_url = urljoin(YAD2_CARS_URL, image_url)
            
            # Extract other details - these might need adjustment based on actual HTML structure
            details = element.find_all(['span', 'div'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['detail', 'info', 'spec', 'meta']
            ))
            
            year = km = manufacturer = model = location = hand = engine_size = gear = color = ""
            
            # Try to extract details from text content
            text_content = element.get_text()
            
            # Look for year (4 digits)
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', text_content)
            if year_match:
                year = year_match.group()
            
            # Look for km
            km_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:ק"מ|קמ|km)', text_content)
            if km_match:
                km = km_match.group(1)
            
            # Extract description (if available)
            desc_elem = element.find(['p', 'div'], class_=lambda x: x and 'desc' in x.lower())
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            return CarListing(
                id=listing_id,
                title=title,
                price=price,
                year=year,
                km=km,
                manufacturer=manufacturer,
                model=model,
                url=url,
                image_url=image_url,
                location=location,
                hand=hand,
                engine_size=engine_size,
                gear=gear,
                color=color,
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing listing element: {e}")
            return None
    
    def scrape_listings(self, search_filter: SearchFilter) -> List[CarListing]:
        """
        Scrape car listings based on search filter.
        
        Args:
            search_filter: SearchFilter object with search criteria
            
        Returns:
            List of CarListing objects
        """
        self.logger.info(f"Scraping listings for filter: {search_filter.name}")
        
        # Build URL with parameters
        params = search_filter.to_url_params()
        
        # Build full URL for logging
        if params:
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{YAD2_CARS_URL}?{param_string}"
        else:
            full_url = YAD2_CARS_URL
        
        self.logger.info(f"Making request to: {full_url}")
        response = self._make_request(YAD2_CARS_URL, params)
        
        if not response:
            self.logger.error("Failed to get response from Yad2")
            return []
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find listing containers - look for the main feed items first
        listing_containers = soup.find_all('div', class_=lambda x: x and 'feed-item-base_feedItemBox' in x)
        
        if not listing_containers:
            # Fallback: look for elements with data-testid that look like listing IDs
            listing_containers = soup.find_all('div', attrs={'data-testid': True})
            # Filter to only those with short alphanumeric testids (likely listing IDs)
            listing_containers = [
                elem for elem in listing_containers 
                if elem.get('data-testid') and len(elem.get('data-testid', '')) <= 12 
                and elem.get('data-testid').replace('_', '').replace('-', '').isalnum()
            ]
        
        self.logger.info(f"Found {len(listing_containers)} potential listing containers")
        
        # Log sample container for debugging
        if listing_containers:
            sample_container = str(listing_containers[0])[:300] + "..." if len(str(listing_containers[0])) > 300 else str(listing_containers[0])
            self.logger.debug(f"Sample container HTML: {sample_container}")
        
        listings = []
        successful_parses = 0
        for i, container in enumerate(listing_containers):
            listing = self._parse_listing_element(container)
            if listing:
                listings.append(listing)
                successful_parses += 1
            elif i < 3:  # Log first 3 failures for debugging
                self.logger.debug(f"Failed to parse container {i+1}")
        
        self.logger.info(f"Successfully parsed {successful_parses} out of {len(listing_containers)} containers")
        
        self.logger.info(f"Successfully parsed {len(listings)} listings")
        return listings
    
    def load_cached_listings(self) -> Set[str]:
        """
        Load previously seen listing IDs from cache (S3 or local).
        
        Returns:
            Set of listing IDs
        """
        try:
            if should_use_s3() and get_s3_storage:
                try:
                    # Try S3 storage first
                    s3_storage = get_s3_storage()
                    data = s3_storage.load_json('listings_cache.json', {})
                    return set(data.get('listing_ids', []))
                except Exception as s3_error:
                    self.logger.warning(f"S3 cache failed, falling back to local: {s3_error}")
                    # Fall back to local storage
                    if os.path.exists(LISTINGS_CACHE_FILE):
                        with open(LISTINGS_CACHE_FILE, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            return set(data.get('listing_ids', []))
            else:
                # Use local storage
                if os.path.exists(LISTINGS_CACHE_FILE):
                    with open(LISTINGS_CACHE_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return set(data.get('listing_ids', []))
        except Exception as e:
            self.logger.error(f"Error loading cached listings: {e}")
        
        return set()
    
    def save_cached_listings(self, listing_ids: Set[str], all_listings: List[CarListing]):
        """
        Save listing IDs and full listing data to cache (S3 or local).
        
        Args:
            listing_ids: Set of listing IDs
            all_listings: List of all listings for reference
        """
        try:
            cache_data = {
                'listing_ids': list(listing_ids),
                'last_updated': datetime.now().isoformat(),
                'listings': [listing.to_dict() for listing in all_listings]
            }
            
            if should_use_s3() and get_s3_storage:
                try:
                    # Try S3 storage first
                    s3_storage = get_s3_storage()
                    if s3_storage.save_json('listings_cache.json', cache_data):
                        self.logger.info(f"Cached {len(listing_ids)} listing IDs to S3")
                    else:
                        self.logger.error("Failed to save cache to S3")
                        # In Lambda environment, we must not fall back to local storage
                        # as it will be lost when the execution ends
                        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
                            raise Exception("S3 cache save failed in Lambda - cannot fall back to ephemeral local storage")
                except Exception as s3_error:
                    # In Lambda environment, fail hard if S3 doesn't work
                    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
                        self.logger.error(f"CRITICAL: S3 cache save failed in Lambda environment: {s3_error}")
                        raise Exception(f"Lambda execution cannot continue without S3 cache: {s3_error}")
                    else:
                        # In local development, fall back to local storage
                        self.logger.warning(f"S3 cache save failed, falling back to local: {s3_error}")
                        with open(LISTINGS_CACHE_FILE, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, indent=2, ensure_ascii=False)
                        self.logger.info(f"Cached {len(listing_ids)} listing IDs to local file")
            else:
                # Use local storage
                with open(LISTINGS_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Cached {len(listing_ids)} listing IDs to local file")
            
        except Exception as e:
            self.logger.error(f"Error saving cached listings: {e}")
    
    def find_new_listings(self, current_listings: List[CarListing]) -> List[CarListing]:
        """
        Find new listings that haven't been seen before.
        
        Args:
            current_listings: List of current listings
            
        Returns:
            List of new listings
        """
        cached_ids = self.load_cached_listings()
        current_ids = {listing.id for listing in current_listings}
        new_ids = current_ids - cached_ids
        
        new_listings = [listing for listing in current_listings if listing.id in new_ids]
        
        self.logger.info(f"Found {len(new_listings)} new listings out of {len(current_listings)} total")
        
        # Update cache with all current listings
        all_ids = cached_ids | current_ids
        self.save_cached_listings(all_ids, current_listings)
        
        return new_listings