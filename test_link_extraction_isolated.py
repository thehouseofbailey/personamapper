#!/usr/bin/env python3
"""
Test the exact _extract_and_add_links method from the crawler
Run this on PythonAnywhere to test link extraction in isolation
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.crawl_url import CrawlUrl

def test_link_extraction_method():
    """Test the actual _extract_and_add_links method logic"""
    app = create_app()
    with app.app_context():
        print("🔧 Testing Link Extraction Method")
        print("=" * 50)
        
        # Get the base URL that was crawled
        base_url = "https://scottandrewbailey.com"
        crawl_job_id = 1  # Assuming job ID is 1
        
        print(f"🌐 Testing with: {base_url}")
        print(f"📋 Job ID: {crawl_job_id}")
        
        try:
            # Fetch and parse the page (same as crawler does)
            print("\n📥 Fetching page...")
            response = requests.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract links (exact same logic as crawler)
            print("🔗 Extracting links...")
            
            # Get base domain for filtering
            base_domain = urlparse(base_url).netloc
            print(f"🏠 Base domain: {base_domain}")
            
            # Find all links
            links = soup.find_all('a', href=True)
            print(f"📊 Found {len(links)} total links")
            
            new_urls = set()
            
            for link in links:
                href = link.get('href', '').strip()
                if not href or href.startswith('#'):
                    continue
                    
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                parsed = urlparse(absolute_url)
                
                # Only crawl URLs from the same domain
                if parsed.netloc != base_domain:
                    continue
                
                # Skip non-HTTP schemes
                if parsed.scheme not in ['http', 'https']:
                    continue
                
                # Clean up URL (remove fragments)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                
                new_urls.add(clean_url)
            
            print(f"✅ Extracted {len(new_urls)} unique crawlable URLs")
            
            # Show first 10 URLs
            for i, url in enumerate(sorted(new_urls)[:10]):
                print(f"   {i+1}. {url}")
            if len(new_urls) > 10:
                print(f"   ... and {len(new_urls) - 10} more")
            
            # Test database addition (simulate what crawler does)
            print(f"\n💾 Testing database addition...")
            
            added_count = 0
            for url in new_urls:
                # Check if URL already exists in crawl queue
                existing = CrawlUrl.query.filter_by(
                    crawl_job_id=crawl_job_id,
                    url=url
                ).first()
                
                if not existing:
                    print(f"   ➕ Would add: {url}")
                    # Don't actually add to avoid messing up the database
                    # Just simulate the addition
                    added_count += 1
                else:
                    print(f"   ⏭️  Already exists: {url}")
            
            print(f"\n📊 Summary:")
            print(f"   URLs that would be added: {added_count}")
            print(f"   URLs already in database: {len(new_urls) - added_count}")
            
            if added_count > 0:
                print(f"\n✅ Link extraction logic is working correctly!")
                print(f"   The issue must be in the crawler integration")
            else:
                print(f"\n⚠️  All URLs already exist in database")
                print(f"   This might explain why nothing was added")
            
        except Exception as e:
            print(f"❌ Error in link extraction test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_link_extraction_method()