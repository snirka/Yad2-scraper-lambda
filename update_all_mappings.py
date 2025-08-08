#!/usr/bin/env python3
"""
Script to fetch all models for all manufacturers by scraping them individually.

This script is more robust against bot detection since it makes individual requests
for each manufacturer with delays, rather than one large request.

Usage:
    python3 update_all_mappings.py
"""

import json
import random
import requests
import time
from typing import Dict, Any, List

from manufacturer_mapper import ManufacturerMapper


class IndividualModelScraper:
    """Scraper that fetches models for each manufacturer individually."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.mapper = ManufacturerMapper()
        
        # Random user agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers to avoid detection."""
        return {
            'User-Agent': random.choice(self.user_agents),
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
    
    def fetch_models_for_manufacturer(self, manufacturer_id: str, manufacturer_name: str) -> Dict[str, Dict]:
        """
        Fetch models for a specific manufacturer.
        
        Args:
            manufacturer_id: The manufacturer ID
            manufacturer_name: The manufacturer name for display
            
        Returns:
            Dictionary of model_id -> model_data
        """
        url = f"https://gw.yad2.co.il/vehicles-cars-catalog/?manufacturer={manufacturer_id}"
        
        print(f"🚗 Fetching models for {manufacturer_name} (ID: {manufacturer_id})...")
        
        try:
            headers = self.get_random_headers()
            response = self.session.get(url, headers=headers, timeout=30)
            
            # Check for CAPTCHA or blocking
            if "אבטחת אתר" in response.text or "Are you for real" in response.text:
                print(f"⚠️  CAPTCHA detected for {manufacturer_name}. Skipping...")
                return {}
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Extract models
                    models_data = data.get('data', {}).get('model', [])
                    if not models_data:
                        print(f"   ℹ️  No models found for {manufacturer_name}")
                        return {}
                    
                    models = {}
                    manufacturer_hebrew = manufacturer_name.split('(')[0].strip()
                    
                    for model in models_data:
                        model_id = str(model.get('id', ''))
                        model_title = model.get('title', '')
                        
                        if model_id and model_title:
                            full_model_name = f"{model_title} ({manufacturer_hebrew})"
                            
                            models[model_id] = {
                                'name': full_model_name,
                                'manufacturer_id': manufacturer_id,
                                'model_name': model_title,
                                'manufacturer_name': manufacturer_hebrew
                            }
                    
                    print(f"   ✅ Found {len(models)} models for {manufacturer_name}")
                    return models
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse JSON for {manufacturer_name}: {e}")
                    return {}
            else:
                print(f"   ❌ HTTP Error {response.status_code} for {manufacturer_name}")
                return {}
                
        except requests.RequestException as e:
            print(f"   ❌ Request failed for {manufacturer_name}: {e}")
            return {}
    
    def update_all_models(self) -> bool:
        """
        Update models for all manufacturers.
        
        Returns:
            True if successful, False otherwise
        """
        # Load existing manufacturers
        manufacturers = self.mapper.load_manufacturers()
        if not manufacturers:
            print("❌ No manufacturers found! Please run update_mappings.py first.")
            return False
        
        print(f"🔄 Starting model update for {len(manufacturers)} manufacturers...")
        print("⏱️  This will take several minutes to avoid being blocked...")
        print()
        
        all_models = {}
        successful_count = 0
        failed_manufacturers = []
        
        for i, (manufacturer_id, manufacturer_name) in enumerate(manufacturers.items(), 1):
            print(f"[{i}/{len(manufacturers)}] ", end="")
            
            # Fetch models for this manufacturer
            models = self.fetch_models_for_manufacturer(manufacturer_id, manufacturer_name)
            
            if models:
                all_models.update(models)
                successful_count += 1
            else:
                failed_manufacturers.append((manufacturer_id, manufacturer_name))
            
            # Add delay between requests to avoid being blocked
            if i < len(manufacturers):  # Don't delay after the last request
                delay = random.uniform(2, 5)  # Random delay between 2-5 seconds
                print(f"   💤 Waiting {delay:.1f}s before next request...")
                time.sleep(delay)
        
        print()
        print("=" * 50)
        print(f"📊 Update Summary:")
        print(f"   ✅ Successful: {successful_count}/{len(manufacturers)} manufacturers")
        print(f"   📊 Total models collected: {len(all_models)}")
        
        if failed_manufacturers:
            print(f"   ❌ Failed manufacturers:")
            for mid, mname in failed_manufacturers:
                print(f"      {mid}: {mname}")
        
        # Save the collected models
        if all_models:
            print()
            print("💾 Saving models...")
            
            # Load existing models to merge
            existing_models = self.mapper.load_models()
            
            # Merge with existing models
            combined_models = {**existing_models, **all_models}
            
            if self.mapper.save_models(combined_models):
                print(f"✅ Successfully saved {len(combined_models)} total models")
                print(f"   📈 Added {len(all_models)} new models")
                return True
            else:
                print("❌ Failed to save models")
                return False
        else:
            print("❌ No models were collected")
            return False
    
    def show_statistics(self):
        """Show statistics about the collected data."""
        manufacturers = self.mapper.load_manufacturers()
        models = self.mapper.load_models()
        
        print()
        print("📊 Final Statistics:")
        print("=" * 30)
        print(f"Total manufacturers: {len(manufacturers)}")
        print(f"Total models: {len(models)}")
        
        # Show models per manufacturer
        manufacturer_model_counts = {}
        for model_data in models.values():
            manufacturer_id = model_data.get('manufacturer_id', 'unknown')
            manufacturer_model_counts[manufacturer_id] = manufacturer_model_counts.get(manufacturer_id, 0) + 1
        
        print()
        print("📈 Models per manufacturer (top 10):")
        sorted_counts = sorted(manufacturer_model_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (manufacturer_id, count) in enumerate(sorted_counts[:10], 1):
            manufacturer_name = manufacturers.get(manufacturer_id, f"ID {manufacturer_id}")
            print(f"   {i:2d}. {manufacturer_name}: {count} models")
        
        print()
        print("✅ You can now use the name-based commands:")
        print("   python3 main.py search-manufacturer --manufacturer-name 'אאודי'")
        print("   python3 main.py search-model --manufacturer-name 'סיאט' --model-name 'איביזה'")
        print("   python3 main.py add-filter-by-name")


def main():
    """Main function."""
    print("🚗 Yad2 Individual Model Scraper")
    print("=" * 50)
    print("This script fetches models for each manufacturer individually with delays.")
    print("This approach is more reliable but slower than the bulk fetch method.")
    print()
    
    scraper = IndividualModelScraper()
    
    # Check if we have manufacturer data
    manufacturers = scraper.mapper.load_manufacturers()
    if not manufacturers:
        print("❌ No manufacturer data found!")
        print("Please run 'python3 update_mappings.py' first to get manufacturer data.")
        return
    
    print(f"📋 Found {len(manufacturers)} manufacturers to process")
    
    # Ask for confirmation
    estimated_time = len(manufacturers) * 3.5 / 60  # Rough estimate in minutes
    print(f"⏱️  Estimated time: {estimated_time:.1f} minutes")
    
    confirm = input("\\nProceed with model update? (y/n): ").lower().strip()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    print()
    
    # Start the update process
    if scraper.update_all_models():
        scraper.show_statistics()
        print()
        print("🎉 Model update completed successfully!")
    else:
        print()
        print("❌ Model update failed or was incomplete")


if __name__ == "__main__":
    main()