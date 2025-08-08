#!/usr/bin/env python3
"""
Local test script for Lambda handler.

This script allows you to test the Lambda function locally before deploying to AWS.
Set environment variables to simulate the Lambda environment.
"""

import os
import json
from lambda_handler import lambda_handler

def test_lambda_locally():
    """Test the Lambda handler locally."""
    
    print("🧪 Testing Yad2 Car Scraper Lambda Handler Locally")
    print("=" * 60)
    
    # Check environment variables
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not telegram_chat_id:
        print("⚠️  Warning: Telegram credentials not set")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables for full testing")
        print()
    
    # Check filters
    filter_vars = [key for key in os.environ.keys() if key.startswith('FILTER')]
    if filter_vars:
        print(f"📋 Found {len(filter_vars)} filter environment variables:")
        for var in sorted(filter_vars):
            print(f"   {var}: {os.environ[var][:50]}...")
    else:
        print("📋 No filter environment variables found")
        print("Set FILTER_1, MANUFACTURER, or individual filter variables for testing")
    
    print()
    
    # Mock Lambda event and context
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
        "detail": {},
        "time": "2023-01-01T00:00:00Z"
    }
    
    print("🚀 Invoking Lambda handler...")
    print()
    
    try:
        # Call the Lambda handler
        result = lambda_handler(test_event, MockContext())
        
        print("✅ Lambda execution completed!")
        print()
        print("📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Lambda execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Example usage with environment variables
    print("💡 Example environment variable setup:")
    print()
    print("# Basic Telegram config:")
    print("export TELEGRAM_BOT_TOKEN='your_bot_token'")
    print("export TELEGRAM_CHAT_ID='your_chat_id'")
    print()
    print("# Single filter example:")
    print("export MANUFACTURER='אאודי'")
    print("export MODEL='A3'")
    print("export YEAR='2020-2023'")
    print()
    print("# Multiple filters example:")
    print("export FILTER_1='{\"name\":\"audi-a3\",\"manufacturer\":\"אאודי\",\"model\":\"A3\",\"year\":\"2020-2023\"}'")
    print("export FILTER_2='{\"name\":\"seat-ibiza\",\"manufacturer\":\"37\",\"model\":\"10507\",\"year\":\"2015-2020\"}'")
    print()
    print("# Individual variables example:")
    print("export FILTER_1_NAME='my-audi-filter'")
    print("export FILTER_1_MANUFACTURER='אאודי'")
    print("export FILTER_1_MODEL='A3'")
    print("export FILTER_1_YEAR='2020-2023'")
    print()
    print("-" * 60)
    print()
    
    test_lambda_locally()