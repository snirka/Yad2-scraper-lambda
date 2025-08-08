#!/usr/bin/env python3
"""
Test script to verify S3 fallback functionality.
"""

import os
from lambda_handler import LambdaCarScraper

def test_s3_fallback():
    """Test S3 fallback with different configurations."""
    
    print("🧪 Testing S3 Fallback Functionality")
    print("=" * 50)
    
    # Test 1: Local mode (no S3)
    print("\n1. Testing Local Mode (USE_S3_STORAGE=false)")
    os.environ['USE_S3_STORAGE'] = 'false'
    os.environ['MANUFACTURER'] = 'סיאט'
    os.environ['MODEL'] = 'איביזה'
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        del os.environ['AWS_LAMBDA_FUNCTION_NAME']
    
    try:
        scraper = LambdaCarScraper()
        print("✅ Local mode works correctly")
        print(f"   Filters: {len(scraper.filters)}")
        if scraper.filters:
            f = scraper.filters[0]
            print(f"   Filter: {f.name}, Manufacturer: {f.manufacturer}, Model: {f.model}")
    except Exception as e:
        print(f"❌ Local mode failed: {e}")
    
    # Test 2: Lambda mode without S3 bucket (fallback scenario)
    print("\n2. Testing Lambda Mode without S3_BUCKET_NAME (fallback)")
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test-function'
    if 'S3_BUCKET_NAME' in os.environ:
        del os.environ['S3_BUCKET_NAME']
    if 'USE_S3_STORAGE' in os.environ:
        del os.environ['USE_S3_STORAGE']
    
    try:
        scraper = LambdaCarScraper()
        print("✅ Lambda mode with fallback works correctly")
        print(f"   Filters: {len(scraper.filters)}")
        if scraper.filters:
            f = scraper.filters[0]
            print(f"   Filter: {f.name}, Manufacturer: {f.manufacturer}, Model: {f.model}")
    except Exception as e:
        print(f"❌ Lambda mode with fallback failed: {e}")
    
    # Test 3: Different manufacturer names
    print("\n3. Testing Different Manufacturer Names")
    test_names = ['Seat', 'סיאט', 'seat', 'SEAT', 'אאודי', 'Audi', 'Toyota', 'טויוטה']
    
    from manufacturer_mapper import ManufacturerMapper
    mapper = ManufacturerMapper()
    
    for name in test_names:
        result = mapper.find_manufacturer_by_name(name)
        status = "✅" if result else "❌"
        if result:
            manufacturer_name = mapper.get_manufacturer_name(result)
            print(f"   {status} '{name}' -> ID {result} ({manufacturer_name})")
        else:
            print(f"   {status} '{name}' -> Not found")
    
    print("\n🎉 S3 Fallback Test Complete!")

if __name__ == "__main__":
    test_s3_fallback()