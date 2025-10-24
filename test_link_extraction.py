#!/usr/bin/env python3
"""
Test link extraction functionality locally
Run this to test if link extraction is working properly
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def test_link_extraction(url="https://scottandrewbailey.com"):
    """Test link extraction from a URL"""
    print(f"🔍 Testing link extraction from: {url}")
    print("=" * 60)
    
    try:
        # Fetch the page
        print("📥 Fetching page...")
        response = requests.get(url, timeout=10)
        print(f"📊 Response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return
        
        # Parse HTML
        print("🔍 Parsing HTML...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get base domain
        base_domain = urlparse(url).netloc
        print(f"🏠 Base domain: {base_domain}")
        
        # Find all links
        links = soup.find_all('a', href=True)
        print(f"🔗 Found {len(links)} total links")
        
        new_urls = set()
        same_domain_count = 0
        
        for i, link in enumerate(links):
            href = link.get('href', '').strip()
            if not href or href.startswith('#'):
                continue
                
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            parsed = urlparse(absolute_url)
            
            # Check if same domain
            if parsed.netloc == base_domain:
                same_domain_count += 1
                
                # Skip non-HTTP schemes
                if parsed.scheme not in ['http', 'https']:
                    continue
                
                # Clean up URL (remove fragments)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                
                new_urls.add(clean_url)
                
                # Show first 10 links
                if len(new_urls) <= 10:
                    print(f"  {len(new_urls)}. {clean_url}")
        
        print(f"\n📊 Summary:")
        print(f"   Total links found: {len(links)}")
        print(f"   Same domain links: {same_domain_count}")
        print(f"   Unique crawlable URLs: {len(new_urls)}")
        
        if len(new_urls) > 10:
            print(f"   (showing first 10, {len(new_urls) - 10} more hidden)")
        
        if len(new_urls) == 0:
            print(f"\n❌ NO CRAWLABLE URLS FOUND!")
            print(f"   This explains why the crawler only finds one page.")
            print(f"   The website might:")
            print(f"   - Use JavaScript navigation")
            print(f"   - Have no internal links")
            print(f"   - Use different domain for links")
        else:
            print(f"\n✅ Link extraction should work - found {len(new_urls)} URLs to crawl")
        
    except Exception as e:
        print(f"❌ Error testing link extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with the actual URL
    test_link_extraction("https://scottandrewbailey.com")