#!/usr/bin/env python3
"""
Script to fetch the complete car catalog (manufacturers and models) from Yad2's API.

This script attempts to fetch all manufacturers and their models in a single request
using comma-separated manufacturer IDs, as suggested by the user.

Usage:
    python3 scrape_all_models.py
"""

import json
import requests
import time
from typing import Dict, Any, List

from manufacturer_mapper import ManufacturerMapper


class CatalogScraper:
    """Scraper for the complete Yad2 car catalog."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.mapper = ManufacturerMapper()
        
    def get_all_manufacturer_ids(self) -> List[str]:
        """Get all manufacturer IDs from existing data."""
        manufacturers = self.mapper.load_manufacturers()
        return list(manufacturers.keys())
    
    def get_complete_catalog(self) -> Dict[str, Any]:
        """
        Fetch the complete catalog using comma-separated manufacturer IDs.
        
        Returns:
            Dictionary containing the catalog data
        """
        # Get all manufacturer IDs
        manufacturer_ids = self.get_all_manufacturer_ids()
        
        if not manufacturer_ids:
            print("❌ No manufacturer IDs found! Please run update_mappings.py first.")
            return {}
        
        # Create comma-separated list
        manufacturers_param = ','.join(manufacturer_ids)
        
        # API endpoint
        url = f"https://gw.yad2.co.il/vehicles-cars-catalog/?manufacturer={manufacturers_param}"
        
        print(f"🚗 Fetching complete catalog for {len(manufacturer_ids)} manufacturers...")
        print(f"📡 URL: {url}")
        
        # Enhanced headers to look more like a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,he;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.yad2.co.il/vehicles/cars',
            'Origin': 'https://www.yad2.co.il',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=60)
            
            # Check for CAPTCHA or blocking
            if "אבטחת אתר" in response.text or "Are you for real" in response.text:
                print("🤖 CAPTCHA detected! Yad2 is blocking automated requests.")
                print("💡 Suggestions:")
                print("   1. Try running update_all_mappings.py instead (slower but more reliable)")
                print("   2. Wait a few hours and try again")
                print("   3. Use a VPN or different IP address")
                return {}
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Successfully fetched catalog data!")
                    return data
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON response: {e}")
                    print(f"Response content (first 500 chars): {response.text[:500]}")
                    return {}
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}")
                return {}
                
        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            return {}
    
    def process_catalog_data(self, data: Dict[str, Any]) -> bool:
        """
        Process the catalog data and update the mappings.
        
        Args:
            data: The catalog data from the API
            
        Returns:
            True if successful, False otherwise
        """
        if not data:
            return False
        
        try:
            # Extract manufacturers
            manufacturers_data = data.get('data', {}).get('manufacturer', [])
            if not manufacturers_data:
                print("❌ No manufacturer data found in response")
                return False
            
            # Process manufacturers
            manufacturers = {}
            for manufacturer in manufacturers_data:
                manufacturer_id = str(manufacturer.get('id', ''))
                title = manufacturer.get('title', '')
                eng_title = manufacturer.get('engTitle', '')
                
                if manufacturer_id and title:
                    if eng_title:
                        full_name = f"{title} ({eng_title})"
                    else:
                        full_name = title
                    manufacturers[manufacturer_id] = full_name
            
            print(f"📊 Found {len(manufacturers)} manufacturers")
            
            # Save manufacturers
            if manufacturers:
                if self.mapper.save_manufacturers(manufacturers):
                    print("✅ Manufacturers saved successfully")
                else:
                    print("❌ Failed to save manufacturers")
                    return False
            
            # Extract and process models
            models_data = data.get('data', {}).get('model', [])
            if not models_data:
                print("⚠️  No model data found in response")
                return True  # Manufacturers were saved successfully
            
            # Process models
            models = {}
            for model in models_data:
                model_id = str(model.get('id', ''))
                model_title = model.get('title', '')
                model_eng_title = model.get('engTitle', '')
                manufacturer_id = str(model.get('manufacturerId', ''))
                
                if model_id and model_title and manufacturer_id:
                    # Get manufacturer name
                    manufacturer_name = manufacturers.get(manufacturer_id, f"Manufacturer {manufacturer_id}")
                    manufacturer_hebrew = manufacturer_name.split('(')[0].strip()
                    
                    # Create model entry
                    if model_eng_title:
                        full_model_name = f"{model_title} ({manufacturer_hebrew})"
                    else:
                        full_model_name = f"{model_title} ({manufacturer_hebrew})"
                    
                    models[model_id] = {
                        'name': full_model_name,
                        'manufacturer_id': manufacturer_id,
                        'model_name': model_title,
                        'manufacturer_name': manufacturer_hebrew
                    }
            
            print(f"📊 Found {len(models)} models")
            
            # Save models
            if models:
                if self.mapper.save_models(models):
                    print("✅ Models saved successfully")
                else:
                    print("❌ Failed to save models")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing catalog data: {e}")
            return False


def main():
    """Main function."""
    print("🚗 Yad2 Complete Catalog Scraper")
    print("=" * 50)
    print("This script attempts to fetch ALL manufacturers and models in one request.")
    print("If this fails due to CAPTCHA, use update_all_mappings.py instead.")
    print()
    
    scraper = CatalogScraper()
    
    # Check if we have manufacturer IDs
    manufacturer_ids = scraper.get_all_manufacturer_ids()
    if not manufacturer_ids:
        print("❌ No manufacturer data found!")
        print("Please run 'python3 update_mappings.py' first to get initial manufacturer data.")
        return
    
    print(f"📋 Using {len(manufacturer_ids)} manufacturer IDs for the request")
    
    # Fetch catalog
    catalog_data = scraper.get_complete_catalog()
    
    if catalog_data:
        print("\\n🔄 Processing catalog data...")
        if scraper.process_catalog_data(catalog_data):
            print("\\n🎉 Catalog update completed successfully!")
            print("\\n📋 Summary:")
            
            # Show summary
            manufacturers = scraper.mapper.load_manufacturers()
            models = scraper.mapper.load_models()
            
            print(f"   📊 Total manufacturers: {len(manufacturers)}")
            print(f"   📊 Total models: {len(models)}")
            
            # Show some examples
            print("\\n📝 Examples:")
            for i, (mid, mname) in enumerate(manufacturers.items()):
                if i >= 5:  # Show first 5
                    break
                manufacturer_models = [
                    model_id for model_id, model_data in models.items()
                    if model_data.get('manufacturer_id') == mid
                ]
                print(f"   {mid}: {mname} ({len(manufacturer_models)} models)")
            
            print("\\n✅ You can now use commands like:")
            print("   python3 main.py search-manufacturer --manufacturer-name 'אאודי'")
            print("   python3 main.py search-model --manufacturer-name 'סיאט' --model-name 'איביזה'")
            print("   python3 main.py add-filter-by-name")
        else:
            print("\\n❌ Failed to process catalog data")
    else:
        print("\\n❌ Failed to fetch catalog data")
        print("\\n💡 Try using update_all_mappings.py instead:")
        print("   python3 update_all_mappings.py")


if __name__ == "__main__":
    main()