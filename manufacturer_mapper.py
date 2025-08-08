"""System to map manufacturer and model IDs to human-readable names."""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

from config import DATA_DIR, MANUFACTURERS_FILE, MODELS_FILE, YAD2_CARS_URL
from scraper import Yad2Scraper

# Import S3 storage for Lambda compatibility
try:
    from s3_storage import get_s3_storage, should_use_s3
except ImportError:
    # S3 storage not available (local mode)
    get_s3_storage = None
    should_use_s3 = lambda: False


class ManufacturerMapper:
    """Maps manufacturer and model IDs to human-readable names."""
    
    def __init__(self):
        """Initialize the mapper."""
        self.logger = logging.getLogger('manufacturer_mapper')
        self.scraper = Yad2Scraper()
        self.manufacturers = {}
        self.models = {}
        
    def load_manufacturers(self) -> Dict[str, str]:
        """Load manufacturers from S3 or local file."""
        try:
            if should_use_s3() and get_s3_storage:
                try:
                    # Try S3 storage first
                    s3_storage = get_s3_storage()
                    return s3_storage.load_json('manufacturers.json', {})
                except Exception as s3_error:
                    self.logger.warning(f"S3 storage failed, falling back to local: {s3_error}")
                    # Fall back to local storage
                    if os.path.exists(MANUFACTURERS_FILE):
                        with open(MANUFACTURERS_FILE, 'r', encoding='utf-8') as f:
                            return json.load(f)
            else:
                # Use local storage
                if os.path.exists(MANUFACTURERS_FILE):
                    with open(MANUFACTURERS_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load manufacturers: {e}")
        return {}
    
    def load_models(self) -> Dict[str, Dict]:
        """Load models from S3 or local file."""
        try:
            if should_use_s3() and get_s3_storage:
                try:
                    # Try S3 storage first
                    s3_storage = get_s3_storage()
                    return s3_storage.load_json('models.json', {})
                except Exception as s3_error:
                    self.logger.warning(f"S3 storage failed, falling back to local: {s3_error}")
                    # Fall back to local storage
                    if os.path.exists(MODELS_FILE):
                        with open(MODELS_FILE, 'r', encoding='utf-8') as f:
                            return json.load(f)
            else:
                # Use local storage
                if os.path.exists(MODELS_FILE):
                    with open(MODELS_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
        return {}
    
    def save_manufacturers(self, manufacturers: Dict[str, str]) -> bool:
        """Save manufacturers to S3 or local file."""
        try:
            if should_use_s3() and get_s3_storage:
                # Use S3 storage
                s3_storage = get_s3_storage()
                return s3_storage.save_json('manufacturers.json', manufacturers)
            else:
                # Use local storage
                with open(MANUFACTURERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(manufacturers, f, ensure_ascii=False, indent=2)
                return True
        except Exception as e:
            self.logger.error(f"Failed to save manufacturers: {e}")
            return False
    
    def save_models(self, models: Dict[str, Dict]) -> bool:
        """Save models to S3 or local file."""
        try:
            if should_use_s3() and get_s3_storage:
                # Use S3 storage
                s3_storage = get_s3_storage()
                return s3_storage.save_json('models.json', models)
            else:
                # Use local storage
                with open(MODELS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(models, f, ensure_ascii=False, indent=2)
                return True
        except Exception as e:
            self.logger.error(f"Failed to save models: {e}")
            return False
    
    def get_manufacturer_name(self, manufacturer_id: str) -> str:
        """Get manufacturer name by ID."""
        manufacturers = self.load_manufacturers()
        return manufacturers.get(manufacturer_id, f"Unknown Manufacturer ({manufacturer_id})")
    
    def get_model_name(self, model_id: str) -> str:
        """Get model name by ID."""
        models = self.load_models()
        model_data = models.get(model_id, {})
        return model_data.get('name', f"Unknown Model ({model_id})")
    
    def list_manufacturers(self) -> Dict[str, str]:
        """Get all known manufacturers."""
        return self.load_manufacturers()
    
    def list_models(self, manufacturer_id: str) -> Dict[str, str]:
        """Get all known models for a manufacturer."""
        models = self.load_models()
        manufacturer_models = {}
        
        for model_id, model_data in models.items():
            if model_data.get('manufacturer_id') == manufacturer_id:
                manufacturer_models[model_id] = model_data.get('name', model_data.get('model_name', f"Model {model_id}"))
        
        return manufacturer_models
    
    def initialize_mappings(self):
        """Initialize with default mappings if files don't exist."""
        # Common manufacturers mapping (based on real Yad2 data)
        common_manufacturers = {
            '1': 'אאודי (Audi)',
            '2': 'אופל (Opel)',
            '3': 'אינפיניטי (Infiniti)',
            '4': 'איסוזו (Isuzu)',
            '5': 'אלפא רומיאו (Alfa Romeo)',
            '6': 'אם ג\'י (MG)',
            '11': 'הונדה (Honda)',
            '13': 'טויוטה (Toyota)',
            '15': 'כרייזלר (Chrysler)',
            '16': 'דייהטסו (Daihatsu)',
            '18': 'יגואר (Jaguar)',
            '19': 'יונדאי (Hyundai)',
            '21': 'קיא (Kia)',
            '22': 'לקסוס (Lexus)',
            '23': 'לנד רובר (Land Rover)',
            '24': 'לינקולן (Lincoln)',
            '25': 'מאזדה (Mazda)',
            '26': 'מיני (MINI)',
            '32': 'ניסן (Nissan)',
            '33': 'פיאט (Fiat)',
            '34': 'פיג\'ו (Peugeot)',
            '35': 'פורד (Ford)',
            '36': 'רנו (Renault)',
            '37': 'סיאט (Seat)',
            '39': 'סובארו (Subaru)',
            '40': 'סאאב (Saab)',
            '41': 'סוזוקי (Suzuki)',
            '42': 'סקודה (Skoda)',
            '43': 'טסלה (Tesla)',
            '44': 'דאצ\'יה (Dacia)',
            '45': 'קדילק (Cadillac)',
            '46': 'פולקסווגן (Volkswagen)',
            '47': 'וולוו (Volvo)',
            '48': 'BMW',
            '49': 'מרצדס (Mercedes)',
            '50': 'מיצובישי (Mitsubishi)',
        }
        
        # Save initial manufacturers if file doesn't exist
        if not os.path.exists(MANUFACTURERS_FILE):
            self.save_manufacturers(common_manufacturers)
            self.logger.info(f"Initialized {len(common_manufacturers)} manufacturers")
        
        # Initialize empty models file if it doesn't exist
        if not os.path.exists(MODELS_FILE):
            # Add some common models for Seat as an example
            common_models = {
                '10507': {
                    'name': 'איביזה (סיאט)',
                    'manufacturer_id': '37',
                    'model_name': 'איביזה',
                    'manufacturer_name': 'סיאט'
                }
            }
            self.save_models(common_models)
            self.logger.info("Initialized models file with sample data")
    
    def scrape_manufacturers_from_page(self) -> Dict[str, str]:
        """Scrape manufacturer options from Yad2 cars page."""
        try:
            # Get the main cars page
            response = self.scraper.session.get(YAD2_CARS_URL)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch cars page: {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for manufacturer dropdown/select
            manufacturer_selects = soup.find_all('select', {'name': re.compile(r'manufacturer', re.I)})
            
            manufacturers = {}
            for select in manufacturer_selects:
                options = select.find_all('option')
                for option in options:
                    value = option.get('value', '').strip()
                    text = option.get_text(strip=True)
                    
                    if value and value.isdigit() and text and text != 'בחר יצרן':
                        manufacturers[value] = text
                        
            if manufacturers:
                self.logger.info(f"Scraped {len(manufacturers)} manufacturers from page")
                return manufacturers
            else:
                self.logger.warning("No manufacturers found on page")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error scraping manufacturers: {e}")
            return {}
    
    def scrape_models_for_manufacturer(self, manufacturer_id: str) -> Dict[str, str]:
        """Scrape model options for a specific manufacturer."""
        try:
            # Navigate to cars page with manufacturer selected
            url = f"{YAD2_CARS_URL}?manufacturer={manufacturer_id}"
            response = self.scraper.session.get(url)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch models for manufacturer {manufacturer_id}: {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for model dropdown/select
            model_selects = soup.find_all('select', {'name': re.compile(r'model', re.I)})
            
            models = {}
            for select in model_selects:
                options = select.find_all('option')
                for option in options:
                    value = option.get('value', '').strip()
                    text = option.get_text(strip=True)
                    
                    if value and value.isdigit() and text and text != 'בחר דגם':
                        models[value] = text
                        
            self.logger.info(f"Scraped {len(models)} models for manufacturer {manufacturer_id}")
            return models
            
        except Exception as e:
            self.logger.error(f"Error scraping models for manufacturer {manufacturer_id}: {e}")
            return {}

    def find_manufacturer_by_name(self, name: str, threshold: float = 0.6) -> Optional[str]:
        """
        Find manufacturer ID by Hebrew or English name using fuzzy matching.
        
        Args:
            name: Manufacturer name in Hebrew or English (e.g., "אאודי", "Audi", "אודי")
            threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            Manufacturer ID if found, None otherwise
        """
        manufacturers = self.load_manufacturers()
        name_lower = name.lower().strip()
        
        best_match = None
        best_score = 0.0
        
        for manufacturer_id, full_name in manufacturers.items():
            # Try matching against different parts of the stored name
            names_to_check = [
                full_name.lower(),  # Full name: "אאודי (Audi)"
                full_name.split('(')[0].strip().lower(),  # Hebrew part: "אאודי"
            ]
            
            # Extract English name if present
            if '(' in full_name and ')' in full_name:
                english_part = full_name.split('(')[1].split(')')[0].strip().lower()
                names_to_check.append(english_part)  # English part: "audi"
            
            for check_name in names_to_check:
                similarity = SequenceMatcher(None, name_lower, check_name).ratio()
                if similarity > best_score:
                    best_score = similarity
                    best_match = manufacturer_id
        
        if best_score >= threshold:
            manufacturer_name = manufacturers.get(best_match, f"ID {best_match}")
            self.logger.info(f"Found manufacturer: '{name}' -> ID {best_match} ({manufacturer_name}) [score: {best_score:.2f}]")
            return best_match
        
        self.logger.warning(f"No manufacturer found for '{name}' (best score: {best_score:.2f})")
        return None
    
    def find_model_by_name(self, manufacturer_id: str, model_name: str, threshold: float = 0.6) -> Optional[str]:
        """
        Find model ID by name within a specific manufacturer using fuzzy matching.
        
        Args:
            manufacturer_id: The manufacturer ID to search within
            model_name: Model name in Hebrew or English (e.g., "איביזה", "Ibiza", "איביזא")
            threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            Model ID if found, None otherwise
        """
        models = self.load_models()
        name_lower = model_name.lower().strip()
        
        # Filter models by manufacturer
        manufacturer_models = {
            model_id: model_data for model_id, model_data in models.items()
            if model_data.get('manufacturer_id') == manufacturer_id
        }
        
        if not manufacturer_models:
            self.logger.warning(f"No models found for manufacturer ID {manufacturer_id}")
            return None
        
        best_match = None
        best_score = 0.0
        
        for model_id, model_data in manufacturer_models.items():
            # Names to check for matching
            names_to_check = [
                model_data.get('model_name', '').lower(),  # "איביזה"
                model_data.get('name', '').lower(),        # "איביזה (סיאט)"
            ]
            
            # Also try without manufacturer part
            full_name = model_data.get('name', '')
            if '(' in full_name:
                model_only = full_name.split('(')[0].strip().lower()
                names_to_check.append(model_only)
            
            for check_name in names_to_check:
                if not check_name:
                    continue
                    
                similarity = SequenceMatcher(None, name_lower, check_name).ratio()
                if similarity > best_score:
                    best_score = similarity
                    best_match = model_id
        
        if best_score >= threshold:
            model_data = manufacturer_models.get(best_match, {})
            model_display_name = model_data.get('name', f"ID {best_match}")
            self.logger.info(f"Found model: '{model_name}' -> ID {best_match} ({model_display_name}) [score: {best_score:.2f}]")
            return best_match
        
        self.logger.warning(f"No model found for '{model_name}' in manufacturer {manufacturer_id} (best score: {best_score:.2f})")
        return None
    
    def get_models_for_manufacturer(self, manufacturer_id: str) -> Dict[str, Dict]:
        """
        Get all models for a specific manufacturer.
        
        Args:
            manufacturer_id: The manufacturer ID
            
        Returns:
            Dictionary of model_id -> model_data for the manufacturer
        """
        models = self.load_models()
        return {
            model_id: model_data for model_id, model_data in models.items()
            if model_data.get('manufacturer_id') == manufacturer_id
        }
    
    def list_manufacturer_names(self) -> List[Tuple[str, str]]:
        """
        Get a list of all manufacturer names and IDs for display.
        
        Returns:
            List of (id, name) tuples
        """
        manufacturers = self.load_manufacturers()
        return [(manufacturer_id, name) for manufacturer_id, name in manufacturers.items()]
    
    def list_model_names_for_manufacturer(self, manufacturer_id: str) -> List[Tuple[str, str]]:
        """
        Get a list of all model names and IDs for a specific manufacturer.
        
        Args:
            manufacturer_id: The manufacturer ID
            
        Returns:
            List of (model_id, model_name) tuples
        """
        models = self.get_models_for_manufacturer(manufacturer_id)
        return [(model_id, data.get('model_name', data.get('name', 'Unknown'))) 
                for model_id, data in models.items()]


def setup_manufacturer_mapper() -> ManufacturerMapper:
    """
    Set up and initialize the manufacturer mapper.
    
    Returns:
        ManufacturerMapper instance
    """
    mapper = ManufacturerMapper()
    
    # Initialize with common manufacturers if files don't exist
    if not os.path.exists(MANUFACTURERS_FILE) or not os.path.exists(MODELS_FILE):
        logging.info("Initializing manufacturer and model mappings...")
        mapper.initialize_mappings()
    
    return mapper