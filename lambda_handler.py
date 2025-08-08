"""
AWS Lambda handler for Yad2 Car Scraper.

This module provides a serverless implementation of the car scraper
that can be triggered by CloudWatch Events on a schedule.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
import boto3

# Import our existing modules
from config import SearchFilter
from scraper import Yad2Scraper
from telegram_bot import TelegramNotifier
from manufacturer_mapper import ManufacturerMapper


class LambdaCarScraper:
    """Lambda-compatible car scraper implementation."""
    
    def __init__(self):
        """Initialize the Lambda scraper."""
        self.setup_logging()
        self.logger = logging.getLogger('lambda_car_scraper')
        
        # Initialize components
        self.scraper = Yad2Scraper()
        self.mapper = ManufacturerMapper()
        
        # Initialize Telegram with environment variables
        telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not telegram_token or not telegram_chat_id:
            self.logger.warning("Telegram credentials not provided via environment variables")
            self.telegram = None
        else:
            self.telegram = TelegramNotifier(telegram_token, telegram_chat_id)
        
        # Load filters from environment
        self.filters = self.load_filters_from_env()
        
    def setup_logging(self):
        """Set up logging for Lambda environment."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_filters_from_env(self) -> List[SearchFilter]:
        """
        Load search filters from environment variables.
        
        Environment variables should be in the format:
        FILTER_1={"name":"filter1","manufacturer":"37","model":"10507","year":"2012-2015","km":"1-89000"}
        FILTER_2={"name":"filter2","manufacturer":"1","model":"10004","year":"2020-2023"}
        
        Or use the simplified format with name translation:
        FILTER_1_NAME=audi-a3
        FILTER_1_MANUFACTURER=אאודי
        FILTER_1_MODEL=A3
        FILTER_1_YEAR=2020-2023
        FILTER_1_KM=1-50000
        FILTER_1_PRICE=100000-300000
        
        Returns:
            List of SearchFilter objects
        """
        filters = []
        
        # Method 1: JSON format (FILTER_1, FILTER_2, etc.)
        filter_num = 1
        while True:
            filter_env = os.environ.get(f'FILTER_{filter_num}')
            if not filter_env:
                break
                
            try:
                filter_data = json.loads(filter_env)
                # Translate names to IDs if needed
                filter_data = self.translate_filter_names(filter_data)
                filters.append(SearchFilter.from_dict(filter_data))
                self.logger.info(f"Loaded filter {filter_num}: {filter_data.get('name', f'filter_{filter_num}')}")
            except Exception as e:
                self.logger.error(f"Error parsing FILTER_{filter_num}: {e}")
            
            filter_num += 1
        
        # Method 2: Individual environment variables (FILTER_1_NAME, FILTER_1_MANUFACTURER, etc.)
        if not filters:
            filters = self.load_filters_from_individual_env_vars()
        
        # Method 3: Single filter from individual env vars (backwards compatibility)
        if not filters:
            single_filter = self.load_single_filter_from_env()
            if single_filter:
                filters.append(single_filter)
        
        if not filters:
            self.logger.warning("No filters configured via environment variables")
            
        return filters
    
    def load_filters_from_individual_env_vars(self) -> List[SearchFilter]:
        """Load filters from individual environment variables."""
        filters = []
        filter_num = 1
        
        while True:
            name = os.environ.get(f'FILTER_{filter_num}_NAME')
            if not name:
                break
            
            # Get manufacturer ID (with name translation)
            manufacturer_input = os.environ.get(f'FILTER_{filter_num}_MANUFACTURER')
            manufacturer_id = self.translate_manufacturer_name(manufacturer_input) if manufacturer_input else None
            
            # Get model ID (with name translation)
            model_input = os.environ.get(f'FILTER_{filter_num}_MODEL')
            model_id = None
            if model_input and manufacturer_id:
                model_id = self.translate_model_name(manufacturer_id, model_input)
            
            # Create filter
            filter_config = SearchFilter(
                name=name,
                manufacturer=manufacturer_id,
                model=model_id,
                year=os.environ.get(f'FILTER_{filter_num}_YEAR'),
                km=os.environ.get(f'FILTER_{filter_num}_KM'),
                price=os.environ.get(f'FILTER_{filter_num}_PRICE'),
                hand=os.environ.get(f'FILTER_{filter_num}_HAND'),
                engine_size=os.environ.get(f'FILTER_{filter_num}_ENGINE_SIZE'),
                gear=os.environ.get(f'FILTER_{filter_num}_GEAR'),
                color=os.environ.get(f'FILTER_{filter_num}_COLOR'),
                area=os.environ.get(f'FILTER_{filter_num}_AREA')
            )
            
            filters.append(filter_config)
            self.logger.info(f"Loaded filter {filter_num}: {name}")
            filter_num += 1
        
        return filters
    
    def load_single_filter_from_env(self) -> Optional[SearchFilter]:
        """Load a single filter from basic environment variables."""
        name = os.environ.get('FILTER_NAME', 'default')
        
        # Get manufacturer ID (with name translation)
        manufacturer_input = os.environ.get('MANUFACTURER')
        manufacturer_id = self.translate_manufacturer_name(manufacturer_input) if manufacturer_input else None
        
        # Get model ID (with name translation)
        model_input = os.environ.get('MODEL')
        model_id = None
        if model_input and manufacturer_id:
            model_id = self.translate_model_name(manufacturer_id, model_input)
        
        # Only create filter if we have at least manufacturer
        if not manufacturer_id:
            return None
        
        return SearchFilter(
            name=name,
            manufacturer=manufacturer_id,
            model=model_id,
            year=os.environ.get('YEAR'),
            km=os.environ.get('KM'),
            price=os.environ.get('PRICE'),
            hand=os.environ.get('HAND'),
            engine_size=os.environ.get('ENGINE_SIZE'),
            gear=os.environ.get('GEAR'),
            color=os.environ.get('COLOR'),
            area=os.environ.get('AREA')
        )
    
    def translate_filter_names(self, filter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate manufacturer and model names to IDs in filter data."""
        # Translate manufacturer name to ID
        manufacturer_input = filter_data.get('manufacturer')
        if manufacturer_input:
            manufacturer_id = self.translate_manufacturer_name(manufacturer_input)
            if manufacturer_id:
                filter_data['manufacturer'] = manufacturer_id
        
        # Translate model name to ID
        model_input = filter_data.get('model')
        manufacturer_id = filter_data.get('manufacturer')
        if model_input and manufacturer_id:
            model_id = self.translate_model_name(manufacturer_id, model_input)
            if model_id:
                filter_data['model'] = model_id
        
        return filter_data
    
    def translate_manufacturer_name(self, manufacturer_input: str) -> Optional[str]:
        """Translate manufacturer name to ID."""
        # If it's already an ID, return it
        manufacturers = self.mapper.load_manufacturers()
        if manufacturer_input in manufacturers:
            return manufacturer_input
        
        # Try to find by name
        manufacturer_id = self.mapper.find_manufacturer_by_name(manufacturer_input)
        if manufacturer_id:
            manufacturer_name = manufacturers.get(manufacturer_id, f"ID {manufacturer_id}")
            self.logger.info(f"Translated manufacturer '{manufacturer_input}' -> ID {manufacturer_id} ({manufacturer_name})")
            return manufacturer_id
        
        self.logger.warning(f"Could not translate manufacturer name: {manufacturer_input}")
        return None
    
    def translate_model_name(self, manufacturer_id: str, model_input: str) -> Optional[str]:
        """Translate model name to ID."""
        # If it's already an ID, return it
        models = self.mapper.get_models_for_manufacturer(manufacturer_id)
        if model_input in models:
            return model_input
        
        # Try to find by name
        model_id = self.mapper.find_model_by_name(manufacturer_id, model_input)
        if model_id:
            model_info = models.get(model_id, {})
            model_name = model_info.get('name', f"ID {model_id}")
            self.logger.info(f"Translated model '{model_input}' -> ID {model_id} ({model_name})")
            return model_id
        
        self.logger.warning(f"Could not translate model name: {model_input}")
        return None
    
    def process_filters(self) -> Dict[str, Any]:
        """
        Process all configured filters and return results.
        
        Returns:
            Dictionary with processing results
        """
        if not self.filters:
            self.logger.warning("No filters configured")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No filters configured'})
            }
        
        self.logger.info(f"Processing {len(self.filters)} filter(s)")
        
        results = {
            'total_filters': len(self.filters),
            'successful_filters': 0,
            'failed_filters': 0,
            'total_new_listings': 0,
            'filter_results': []
        }
        
        for i, search_filter in enumerate(self.filters, 1):
            try:
                self.logger.info(f"Processing filter {i}/{len(self.filters)}: {search_filter.name}")
                
                # Scrape listings
                listings = self.scraper.scrape_listings(search_filter)
                
                filter_result = {
                    'filter_name': search_filter.name,
                    'new_listings_count': len(listings) if listings else 0,
                    'status': 'success'
                }
                
                if listings:
                    self.logger.info(f"Found {len(listings)} new listings for filter '{search_filter.name}'")
                    results['total_new_listings'] += len(listings)
                    
                    # Send notifications
                    if self.telegram:
                        try:
                            if len(listings) == 1:
                                self.telegram.send_car_notification(listings[0])
                            else:
                                self.telegram.send_multiple_cars_notification(listings)
                            filter_result['notification_sent'] = True
                        except Exception as e:
                            self.logger.error(f"Failed to send Telegram notification: {e}")
                            filter_result['notification_sent'] = False
                            filter_result['notification_error'] = str(e)
                    else:
                        filter_result['notification_sent'] = False
                        filter_result['notification_error'] = 'Telegram not configured'
                else:
                    self.logger.info(f"No new listings found for filter '{search_filter.name}'")
                
                results['successful_filters'] += 1
                results['filter_results'].append(filter_result)
                
            except Exception as e:
                self.logger.error(f"Error processing filter '{search_filter.name}': {e}")
                results['failed_filters'] += 1
                results['filter_results'].append({
                    'filter_name': search_filter.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Response dict with statusCode and body
    """
    try:
        # Initialize scraper
        scraper = LambdaCarScraper()
        
        # Log environment info
        scraper.logger.info(f"Lambda function started. Event: {json.dumps(event, default=str)}")
        scraper.logger.info(f"Configured filters: {len(scraper.filters)}")
        
        if scraper.telegram:
            scraper.logger.info("Telegram notifications enabled")
        else:
            scraper.logger.info("Telegram notifications disabled")
        
        # Process filters
        results = scraper.process_filters()
        
        # Log summary
        scraper.logger.info(f"Processing completed. Results: {json.dumps(results, indent=2)}")
        
        # Send summary notification if Telegram is configured
        if scraper.telegram and results['total_new_listings'] > 0:
            try:
                summary_message = (
                    f"🤖 Yad2 Scraper Summary\\n"
                    f"📊 Processed {results['total_filters']} filters\\n"
                    f"🆕 Found {results['total_new_listings']} new listings\\n"
                    f"✅ Successful: {results['successful_filters']}\\n"
                    f"❌ Failed: {results['failed_filters']}"
                )
                scraper.telegram.send_status_notification(summary_message)
            except Exception as e:
                scraper.logger.error(f"Failed to send summary notification: {e}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Scraping completed successfully',
                'results': results
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        error_msg = f"Lambda function failed: {str(e)}"
        logging.error(error_msg, exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }


# For local testing
if __name__ == "__main__":
    """Local testing support."""
    import sys
    
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "yad2-car-scraper"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:yad2-car-scraper"
            self.memory_limit_in_mb = "512"
            self.remaining_time_in_millis = lambda: 300000
    
    # Test event
    test_event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {}
    }
    
    # Run handler
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2, ensure_ascii=False))