#!/usr/bin/env python3
"""
Quick crawler speed test for PythonAnywhere performance analysis.
Tests just HTTP fetch + BeautifulSoup parsing without database operations.
"""

import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

def test_page_fetch_speed(url):
    """Test just the HTTP fetch + parsing speed"""
    print(f"Testing fetch speed for: {url}")
    
    start_time = time.time()
    
    try:
        # HTTP fetch
        fetch_start = time.time()
        response = requests.get(url, timeout=30)
        fetch_time = time.time() - fetch_start
        print(f"  HTTP fetch: {fetch_time:.2f} seconds")
        
        # Parse with BeautifulSoup  
        parse_start = time.time()
        soup = BeautifulSoup(response.content, 'html.parser')
        parse_time = time.time() - parse_start
        print(f"  BeautifulSoup parse: {parse_time:.2f} seconds")
        
        # Extract basic content
        extract_start = time.time()
        title = soup.find('title')
        title_text = title.get_text().strip() if title else 'No title'
        
        # Get main content
        body = soup.find('body')
        content = body.get_text() if body else ''
        word_count = len(content.split())
        extract_time = time.time() - extract_start
        print(f"  Content extraction: {extract_time:.2f} seconds")
        
        total_time = time.time() - start_time
        print(f"  TOTAL TIME: {total_time:.2f} seconds")
        print(f"  Page info: {title_text} ({word_count} words)")
        
        return total_time
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

if __name__ == "__main__":
    # Test the same URL that's taking 3+ minutes in the crawler
    test_url = "https://scottandrewbailey.com/the-well-of-sunken-dreams"
    
    print("=== PythonAnywhere Crawler Speed Test ===")
    print(f"Time: {datetime.now()}")
    print()
    
    # Test the slow page
    result = test_page_fetch_speed(test_url)
    
    if result:
        print(f"\nResult: Page processing took {result:.2f} seconds")
        if result > 10:
            print("❌ VERY SLOW - PythonAnywhere performance issue")
        elif result > 3:
            print("⚠️  SLOW - Some performance degradation")  
        else:
            print("✅ NORMAL - Speed looks good")
    else:
        print("❌ FAILED - Could not fetch page")