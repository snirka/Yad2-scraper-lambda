"""Script to scrape real manufacturer and model IDs from Yad2."""

import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_yad2_page():
    """Get the main Yad2 cars page to extract manufacturer options."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'he-IL,he;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    
    url = 'https://www.yad2.co.il/vehicles/cars'
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to get page: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_manufacturers_from_html(html_content):
    """Extract manufacturer IDs and names from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("Looking for manufacturer select elements...")
    
    # Look for select elements that might contain manufacturers
    selects = soup.find_all('select')
    print(f"Found {len(selects)} select elements")
    
    for i, select in enumerate(selects):
        print(f"\nSelect {i+1}:")
        print(f"  Name: {select.get('name')}")
        print(f"  ID: {select.get('id')}")
        print(f"  Class: {select.get('class')}")
        
        options = select.find_all('option')
        print(f"  Options count: {len(options)}")
        
        if len(options) > 5:  # Likely a manufacturer dropdown
            print("  First few options:")
            for option in options[:10]:
                value = option.get('value')
                text = option.get_text(strip=True)
                print(f"    {value}: {text}")

def extract_manufacturers_from_scripts(html_content):
    """Look for manufacturer data in JavaScript sections."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\nLooking for manufacturer data in script tags...")
    
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} script tags")
    
    for i, script in enumerate(scripts):
        if script.string:
            content = script.string
            
            # Look for patterns that might contain manufacturer data
            if any(keyword in content.lower() for keyword in ['manufacturer', 'יצרן', 'brand', 'car']):
                print(f"\nScript {i+1} contains car-related data:")
                # Show first 500 chars
                print(content[:500] + "..." if len(content) > 500 else content)

def main():
    """Main function to scrape real manufacturer IDs."""
    print("🔍 Scraping real manufacturer and model IDs from Yad2...")
    print("=" * 60)
    
    # Get the page
    html_content = get_yad2_page()
    
    if not html_content:
        print("❌ Failed to get page content")
        return
    
    print(f"✅ Got page content ({len(html_content)} characters)")
    
    # Save HTML for inspection
    with open('yad2_page.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("💾 Saved page content to yad2_page.html")
    
    # Extract manufacturers from select elements
    extract_manufacturers_from_html(html_content)
    
    # Extract from JavaScript
    extract_manufacturers_from_scripts(html_content)
    
    print("\n" + "=" * 60)
    print("🔧 Manual extraction needed:")
    print("1. Open yad2_page.html in a browser")
    print("2. Use browser dev tools to inspect the manufacturer dropdown")
    print("3. Look for the actual select element or API calls")
    print("4. The real IDs will be in the option values or API responses")

if __name__ == "__main__":
    main()