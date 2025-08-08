#!/usr/bin/env python3
"""
Yad2 Car Scraper - Main Application

This script scrapes Yad2.co.il for new car listings based on user-defined filters
and sends notifications via Telegram when new listings are found.
"""

import argparse
import json
import logging
import os
import schedule
import signal
import sys
import time
from typing import Dict, List, Optional

from config import (
    DATA_DIR, SCRAPE_INTERVAL_MINUTES, LOG_FILE, LOG_LEVEL, LOG_FORMAT,
    FILTERS_FILE, SearchFilter, DEFAULT_SEARCH_FILTERS
)
from scraper import Yad2Scraper
from telegram_bot import setup_telegram_bot
from manufacturer_mapper import setup_manufacturer_mapper


class CarScraperApp:
    """Main application class for the Yad2 car scraper."""
    
    def __init__(self):
        """Initialize the application."""
        self.setup_logging()
        self.logger = logging.getLogger('car_scraper_app')
        
        # Initialize components
        self.scraper = Yad2Scraper()
        self.telegram = setup_telegram_bot()
        self.mapper = setup_manufacturer_mapper()
        
        # Load search filters
        self.filters = self.load_filters()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True

    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL.upper()),
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def load_filters(self) -> List[SearchFilter]:
        """Load search filters from file."""
        if not os.path.exists(FILTERS_FILE):
            # Create default filter if none exist
            default_filter = SearchFilter(
                name="default",
                **DEFAULT_SEARCH_FILTERS
            )
            self.save_filters([default_filter])
            return [default_filter]
        
        try:
            with open(FILTERS_FILE, 'r', encoding='utf-8') as f:
                filters_data = json.load(f)
                return [SearchFilter.from_dict(f) for f in filters_data]
        except Exception as e:
            self.logger.error(f"Error loading filters: {e}")
            return []

    def save_filters(self, filters: List[SearchFilter]) -> bool:
        """Save search filters to file."""
        try:
            filters_data = [f.to_dict() for f in filters]
            with open(FILTERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(filters_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving filters: {e}")
            return False

    def add_filter(self, search_filter: SearchFilter) -> bool:
        """Add a new search filter."""
        # Check if filter with same name already exists
        existing_names = [f.name for f in self.filters]
        if search_filter.name in existing_names:
            self.logger.error(f"Filter with name '{search_filter.name}' already exists")
            return False
        
        self.filters.append(search_filter)
        return self.save_filters(self.filters)

    def remove_filter(self, filter_name: str) -> bool:
        """Remove a search filter by name."""
        original_count = len(self.filters)
        self.filters = [f for f in self.filters if f.name != filter_name]
        
        if len(self.filters) < original_count:
            return self.save_filters(self.filters)
        return False

    def list_filters(self) -> List[SearchFilter]:
        """Get all configured filters."""
        return self.filters.copy()

    def scrape_single_run(self):
        """Perform a single scraping run for all filters."""
        if not self.filters:
            self.logger.warning("No filters configured. Add a filter first.")
            return
        
        self.logger.info(f"Starting scrape run for {len(self.filters)} filter(s)")
        
        for search_filter in self.filters:
            try:
                self.logger.info(f"Scraping filter: {search_filter.name}")
                
                # Scrape listings
                listings = self.scraper.scrape_listings(search_filter)
                
                if listings:
                    self.logger.info(f"Found {len(listings)} new listings for filter '{search_filter.name}'")
                    
                    # Send notifications
                    if len(listings) == 1:
                        self.telegram.send_car_notification(listings[0])
                    else:
                        self.telegram.send_multiple_cars_notification(listings)
                else:
                    self.logger.info(f"No new listings found for filter '{search_filter.name}'")
                    
            except Exception as e:
                self.logger.error(f"Error processing filter '{search_filter.name}': {e}")

    def run_scheduler(self):
        """Run the scraper on a schedule."""
        # Schedule the scraping job
        schedule.every(SCRAPE_INTERVAL_MINUTES).minutes.do(self.scrape_single_run)
        
        self.logger.info(f"Scheduler started. Will scrape every {SCRAPE_INTERVAL_MINUTES} minutes.")
        self.logger.info("Press Ctrl+C to stop")
        
        # Run initial scrape
        self.scrape_single_run()
        
        # Main scheduler loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(5)  # Wait before retrying
        
        self.logger.info("Scheduler stopped")


def create_interactive_filter(mapper) -> Optional[SearchFilter]:
    """Create a search filter interactively."""
    print("\\n🔍 Create New Search Filter")
    print("=" * 40)
    
    name = input("Enter filter name: ").strip()
    if not name:
        print("Filter name is required!")
        return None
    
    print("\\nSelect manufacturer (press Enter to skip):")
    manufacturers = mapper.list_manufacturers()
    
    # Show some common manufacturers
    print("Common manufacturers:")
    common_ids = ['1', '13', '19', '32', '37', '46', '47', '48', '49']
    for mid in common_ids:
        if mid in manufacturers:
            print(f"  {mid}: {manufacturers[mid]}")
    
    manufacturer_input = input("Enter manufacturer ID or name (e.g., '1', 'אאודי', 'Audi'): ").strip()
    manufacturer = None
    
    if manufacturer_input:
        # Check if input is a direct ID
        if manufacturer_input in manufacturers:
            manufacturer = manufacturer_input
            print(f"✅ Selected manufacturer: {manufacturers[manufacturer]}")
        else:
            # Try to find by name
            manufacturer = mapper.find_manufacturer_by_name(manufacturer_input)
            if manufacturer:
                print(f"✅ Found manufacturer: {manufacturers[manufacturer]}")
            else:
                print(f"❌ Manufacturer '{manufacturer_input}' not found!")
                print("Please use an exact ID or try a different name.")
    
    model = None
    if manufacturer:
        print(f"\\nSelect model for {manufacturers.get(manufacturer, manufacturer)}:")
        models = mapper.list_models(manufacturer)
        if models:
            print(f"\\nAvailable models for {manufacturers.get(manufacturer, manufacturer)} (showing first 10):")
            for model_id, model_name in list(models.items())[:10]:  # Show first 10
                print(f"  {model_id}: {model_name}")
            print("  ... (use 'list-models' command to see all)")
        
        model_input = input("Enter model ID or name (e.g., '10507', 'איביזה', 'Ibiza') or leave empty: ").strip()
        
        if model_input:
            # Check if input is a direct ID
            if models and model_input in models:
                model = model_input
                print(f"✅ Selected model: {models[model]}")
            else:
                # Try to find by name
                model = mapper.find_model_by_name(manufacturer, model_input)
                if model:
                    if models and model in models:
                        print(f"✅ Found model: {models[model]}")
                    else:
                        # Get from full models data
                        all_models = mapper.get_models_for_manufacturer(manufacturer)
                        if model in all_models:
                            print(f"✅ Found model: {all_models[model].get('name', f'ID {model}')}")
                else:
                    print(f"❌ Model '{model_input}' not found for this manufacturer!")
                    print("Please use an exact ID or try a different name.")
    
    year = input("Enter year range (e.g., '2012-2015' or leave empty): ").strip()
    km = input("Enter km range (e.g., '-1-89000' or leave empty): ").strip()
    price = input("Enter price range (e.g., '50000-150000' or leave empty): ").strip()
    
    filter_config = SearchFilter(
        name=name,
        manufacturer=manufacturer if manufacturer else None,
        model=model if model else None,
        year=year if year else None,
        km=km if km else None,
        price=price if price else None
    )
    
    print("\\nFilter created:")
    print(f"Name: {filter_config.name}")
    if filter_config.manufacturer:
        print(f"Manufacturer: {manufacturers.get(filter_config.manufacturer, filter_config.manufacturer)}")
    if filter_config.model:
        models = mapper.list_models(filter_config.manufacturer or '')
        print(f"Model: {models.get(filter_config.model, filter_config.model)}")
    if filter_config.year:
        print(f"Year: {filter_config.year}")
    if filter_config.km:
        print(f"Kilometers: {filter_config.km}")
    if filter_config.price:
        print(f"Price: {filter_config.price}")
    
    return filter_config


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Yad2 Car Scraper')
    parser.add_argument('command', nargs='?', default='run', 
                       choices=['run', 'scrape-once', 'add-filter', 'list-filters', 
                               'remove-filter', 'list-manufacturers', 'list-models', 'test-telegram',
                               'search-manufacturer', 'search-model', 'add-filter-by-name'],
                       help='Command to execute')
    parser.add_argument('--filter-name', help='Filter name for remove-filter command')
    parser.add_argument('--manufacturer-id', help='Manufacturer ID for list-models command')
    parser.add_argument('--manufacturer-name', help='Manufacturer name to search for')
    parser.add_argument('--model-name', help='Model name to search for')
    
    args = parser.parse_args()
    
    # Initialize app
    app = CarScraperApp()
    
    if args.command == 'run':
        print("Starting car scraper in scheduled mode...")
        print(f"Press Ctrl+C to stop")
        app.run_scheduler()
    
    elif args.command == 'scrape-once':
        print("Running single scrape...")
        app.scrape_single_run()
        print("Single scrape completed!")
    
    elif args.command == 'add-filter':
        filter_config = create_interactive_filter(app.mapper)
        if filter_config:
            if app.add_filter(filter_config):
                print(f"Filter '{filter_config.name}' added successfully!")
            else:
                print(f"Failed to add filter '{filter_config.name}'")
    
    elif args.command == 'list-filters':
        filters = app.list_filters()
        if filters:
            print("\\nConfigured filters:")
            print("=" * 50)
            for f in filters:
                print(f"\\nFilter: {f.name}")
                if f.manufacturer:
                    manufacturer_name = app.mapper.get_manufacturer_name(f.manufacturer)
                    print(f"  Manufacturer: {manufacturer_name}")
                if f.model:
                    model_name = app.mapper.get_model_name(f.model)
                    print(f"  Model: {model_name}")
                if f.year:
                    print(f"  Year: {f.year}")
                if f.km:
                    print(f"  Kilometers: {f.km}")
                if f.price:
                    print(f"  Price: {f.price}")
        else:
            print("No filters configured.")
    
    elif args.command == 'remove-filter':
        if not args.filter_name:
            filter_name = input("Enter filter name to remove: ").strip()
        else:
            filter_name = args.filter_name
        
        if app.remove_filter(filter_name):
            print(f"Filter '{filter_name}' removed successfully!")
        else:
            print(f"Filter '{filter_name}' not found!")
    
    elif args.command == 'list-manufacturers':
        manufacturers = app.mapper.list_manufacturers()
        print("\\nAvailable Manufacturers:")
        print("=" * 50)
        for mid, mname in manufacturers.items():
            print(f"{mid}: {mname}")
    
    elif args.command == 'list-models':
        if not args.manufacturer_id:
            manufacturer_id = input("Enter manufacturer ID: ").strip()
        else:
            manufacturer_id = args.manufacturer_id
        
        models = app.mapper.list_models(manufacturer_id)
        if models:
            manufacturer_name = app.mapper.get_manufacturer_name(manufacturer_id)
            print(f"\\nModels for {manufacturer_name}:")
            print("=" * 50)
            for model_id, model_name in models.items():
                print(f"{model_id}: {model_name}")
        else:
            print(f"No models found for manufacturer ID: {manufacturer_id}")
    
    elif args.command == 'test-telegram':
        print("Testing Telegram connection...")
        if app.telegram.test_connection():
            app.telegram.send_status_notification("🧪 Test message from Yad2 Car Scraper")
            print("Telegram test successful!")
        else:
            print("Telegram test failed! Check your bot token and chat ID.")
    
    elif args.command == 'search-manufacturer':
        manufacturer_name = args.manufacturer_name or input("Enter manufacturer name (Hebrew or English): ").strip()
        if not manufacturer_name:
            print("Manufacturer name is required!")
            return
        
        manufacturer_id = app.mapper.find_manufacturer_by_name(manufacturer_name)
        if manufacturer_id:
            manufacturer_full_name = app.mapper.get_manufacturer_name(manufacturer_id)
            print(f"✅ Found: '{manufacturer_name}' -> ID {manufacturer_id} ({manufacturer_full_name})")
        else:
            print(f"❌ No manufacturer found for '{manufacturer_name}'")
            print("Try using 'list-manufacturers' to see all available manufacturers")
    
    elif args.command == 'search-model':
        manufacturer_name = args.manufacturer_name or input("Enter manufacturer name: ").strip()
        model_name = args.model_name or input("Enter model name: ").strip()
        
        if not manufacturer_name or not model_name:
            print("Both manufacturer and model names are required!")
            return
        
        # First find manufacturer
        manufacturer_id = app.mapper.find_manufacturer_by_name(manufacturer_name)
        if not manufacturer_id:
            print(f"❌ Manufacturer '{manufacturer_name}' not found!")
            return
        
        manufacturer_full_name = app.mapper.get_manufacturer_name(manufacturer_id)
        print(f"✅ Found manufacturer: {manufacturer_full_name} (ID: {manufacturer_id})")
        
        # Then find model
        model_id = app.mapper.find_model_by_name(manufacturer_id, model_name)
        if model_id:
            models = app.mapper.get_models_for_manufacturer(manufacturer_id)
            if model_id in models:
                model_full_name = models[model_id].get('name', f"ID {model_id}")
                print(f"✅ Found model: '{model_name}' -> ID {model_id} ({model_full_name})")
            else:
                print(f"✅ Found model ID: {model_id}")
        else:
            print(f"❌ No model found for '{model_name}' in {manufacturer_full_name}")
            print(f"Use 'list-models --manufacturer-id {manufacturer_id}' to see available models")
    
    elif args.command == 'add-filter-by-name':
        print("🎯 Create a new filter using manufacturer and model names")
        print("=" * 60)
        
        # Get filter name
        name = input("Enter filter name: ").strip()
        if not name:
            print("Filter name is required!")
            return
        
        # Get manufacturer by name
        manufacturer_name = input("Enter manufacturer name (e.g., 'סיאט', 'Seat', 'אאודי'): ").strip()
        manufacturer_id = None
        if manufacturer_name:
            manufacturer_id = app.mapper.find_manufacturer_by_name(manufacturer_name)
            if not manufacturer_id:
                print(f"❌ Manufacturer '{manufacturer_name}' not found!")
                print("Available manufacturers:")
                manufacturers = app.mapper.list_manufacturer_names()
                for mid, mname in manufacturers[:10]:  # Show first 10
                    print(f"  {mid}: {mname}")
                print("  ... (use 'list-manufacturers' to see all)")
                return
            else:
                manufacturer_full_name = app.mapper.get_manufacturer_name(manufacturer_id)
                print(f"✅ Selected manufacturer: {manufacturer_full_name}")
        
        # Get model by name
        model_id = None
        if manufacturer_id:
            model_name = input("Enter model name (e.g., 'איביזה', 'Ibiza') or leave empty: ").strip()
            if model_name:
                model_id = app.mapper.find_model_by_name(manufacturer_id, model_name)
                if not model_id:
                    print(f"❌ Model '{model_name}' not found for this manufacturer!")
                    print("Available models:")
                    models = app.mapper.list_model_names_for_manufacturer(manufacturer_id)
                    for mid, mname in models[:10]:  # Show first 10
                        print(f"  {mid}: {mname}")
                    print("  ... (use 'list-models' to see all)")
                    return
                else:
                    models = app.mapper.get_models_for_manufacturer(manufacturer_id)
                    if model_id in models:
                        model_full_name = models[model_id].get('name', f"ID {model_id}")
                        print(f"✅ Selected model: {model_full_name}")
        
        # Get other parameters
        year = input("Enter year range (e.g., '2012-2015') or leave empty: ").strip()
        km = input("Enter km range (e.g., '-1-89000') or leave empty: ").strip()
        price = input("Enter price range (e.g., '50000-150000') or leave empty: ").strip()
        
        # Create filter
        filter_config = SearchFilter(
            name=name,
            manufacturer=manufacturer_id if manufacturer_id else None,
            model=model_id if model_id else None,
            year=year if year else None,
            km=km if km else None,
            price=price if price else None
        )
        
        # Show summary
        print("\\n📋 Filter Summary:")
        print("=" * 30)
        print(f"Name: {filter_config.name}")
        if manufacturer_id:
            print(f"Manufacturer: {app.mapper.get_manufacturer_name(manufacturer_id)} (ID: {manufacturer_id})")
        if model_id:
            models = app.mapper.get_models_for_manufacturer(manufacturer_id)
            if model_id in models:
                model_info = models[model_id]
                print(f"Model: {model_info.get('name', f'ID {model_id}')} (ID: {model_id})")
        if year:
            print(f"Year: {year}")
        if km:
            print(f"Kilometers: {km}")
        if price:
            print(f"Price: {price}")
        
        # Confirm and save
        confirm = input("\\nSave this filter? (y/n): ").lower().strip()
        if confirm == 'y':
            if app.add_filter(filter_config):
                print(f"✅ Filter '{name}' created successfully!")
            else:
                print(f"❌ Failed to create filter '{name}'")
        else:
            print("Filter creation cancelled.")


if __name__ == "__main__":
    main()