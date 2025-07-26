import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Set
from app.models import CrawlUrl, CrawlJob
from app import db

logger = logging.getLogger(__name__)

class SitemapService:
    """Service for discovering and parsing sitemaps to extract URLs."""
    
    def __init__(self, crawl_job_id: int):
        self.crawl_job_id = crawl_job_id
        self.crawl_job = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.discovered_urls: Set[str] = set()
    
    def load_crawl_job(self) -> bool:
        """Load the crawl job from database."""
        try:
            self.crawl_job = CrawlJob.query.get(self.crawl_job_id)
            if not self.crawl_job:
                logger.error(f"Crawl job {self.crawl_job_id} not found")
                return False
            return True
        except Exception as e:
            logger.error(f"Error loading crawl job: {e}")
            return False
    
    def discover_and_store_urls(self) -> int:
        """Discover URLs from sitemaps and store them in the database."""
        if not self.load_crawl_job():
            return 0
        
        logger.info(f"Starting sitemap discovery for {self.crawl_job.base_url}")
        
        # Get sitemap URLs to check
        sitemap_urls = self.get_sitemap_urls()
        
        total_urls = 0
        for sitemap_url in sitemap_urls:
            try:
                urls = self.parse_sitemap(sitemap_url)
                total_urls += len(urls)
                logger.info(f"Found {len(urls)} URLs in {sitemap_url}")
            except Exception as e:
                logger.warning(f"Error parsing sitemap {sitemap_url}: {e}")
        
        # Store discovered URLs in database
        stored_count = self.store_urls()
        logger.info(f"Discovered {total_urls} total URLs, stored {stored_count} new URLs")
        
        return stored_count
    
    def get_sitemap_urls(self) -> List[str]:
        """Get list of sitemap URLs to check."""
        base_url = self.crawl_job.base_url.rstrip('/')
        sitemap_urls = []
        
        # Common sitemap locations
        common_paths = [
            '/sitemap_index.xml',
            '/sitemap.xml',
            '/sitemaps.xml',
            '/sitemap/sitemap.xml',
            '/sitemap/index.xml'
        ]
        
        for path in common_paths:
            sitemap_urls.append(base_url + path)
        
        # Check robots.txt for sitemap declarations
        try:
            robots_url = base_url + '/robots.txt'
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        if sitemap_url not in sitemap_urls:
                            sitemap_urls.append(sitemap_url)
                            logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
        except Exception as e:
            logger.warning(f"Error checking robots.txt: {e}")
        
        return sitemap_urls
    
    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Parse a sitemap XML file and extract URLs."""
        try:
            response = self.session.get(sitemap_url, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle different sitemap formats
            urls = []
            
            # Check if this is a sitemap index (contains other sitemaps)
            if self.is_sitemap_index(root):
                logger.info(f"Found sitemap index: {sitemap_url}")
                sitemap_urls = self.extract_sitemap_urls(root)
                for sub_sitemap_url in sitemap_urls:
                    try:
                        sub_urls = self.parse_sitemap(sub_sitemap_url)
                        urls.extend(sub_urls)
                    except Exception as e:
                        logger.warning(f"Error parsing sub-sitemap {sub_sitemap_url}: {e}")
            else:
                # Regular sitemap with URLs
                urls = self.extract_urls_from_sitemap(root)
            
            # Filter URLs based on crawl job patterns
            filtered_urls = []
            for url in urls:
                if self.should_include_url(url):
                    filtered_urls.append(url)
                    self.discovered_urls.add(url)
            
            return filtered_urls
            
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []
    
    def is_sitemap_index(self, root: ET.Element) -> bool:
        """Check if the XML root is a sitemap index."""
        # Check for sitemapindex tag or sitemap children
        return (root.tag.endswith('sitemapindex') or 
                any(child.tag.endswith('sitemap') for child in root))
    
    def extract_sitemap_urls(self, root: ET.Element) -> List[str]:
        """Extract sitemap URLs from a sitemap index."""
        sitemap_urls = []
        
        # Handle different XML namespaces
        for sitemap in root.iter():
            if sitemap.tag.endswith('sitemap'):
                for child in sitemap:
                    if child.tag.endswith('loc'):
                        sitemap_urls.append(child.text.strip())
        
        return sitemap_urls
    
    def extract_urls_from_sitemap(self, root: ET.Element) -> List[str]:
        """Extract URLs from a regular sitemap."""
        urls = []
        
        # Handle different XML namespaces
        for url_elem in root.iter():
            if url_elem.tag.endswith('url'):
                for child in url_elem:
                    if child.tag.endswith('loc'):
                        urls.append(child.text.strip())
        
        return urls
    
    def is_html_content_url(self, url: str) -> bool:
        """Check if URL likely points to HTML content (not binary files)."""
        # Define file extensions to ignore
        binary_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.tif',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
            # Archives
            '.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz',
            # Media
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.ogg', '.wav', '.m4a',
            # Code/Data files
            '.js', '.css', '.json', '.xml', '.csv', '.txt', '.log',
            # Executables
            '.exe', '.dmg', '.pkg', '.deb', '.rpm', '.msi',
            # Fonts
            '.ttf', '.otf', '.woff', '.woff2', '.eot',
            # Other
            '.rss', '.atom', '.feed'
        }
        
        # Parse URL to get path
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check if path ends with a binary extension
        for ext in binary_extensions:
            if path.endswith(ext):
                logger.debug(f"Skipping binary file from sitemap: {url}")
                return False
        
        # Check for common patterns that indicate non-HTML content
        if any(pattern in path for pattern in ['/api/', '/feed/', '/rss/', '/sitemap']):
            if not path.endswith('.html') and not path.endswith('.htm'):
                logger.debug(f"Skipping API/feed URL from sitemap: {url}")
                return False
        
        return True

    def should_include_url(self, url: str) -> bool:
        """Check if URL should be included based on crawl job patterns."""
        if not url:
            return False
        
        # Filter out binary files and non-HTML content
        if not self.is_html_content_url(url):
            return False
        
        # Check if URL matches base domain
        base_domain = urlparse(self.crawl_job.base_url).netloc
        url_domain = urlparse(url).netloc
        if url_domain != base_domain:
            return False
        
        # Check include patterns
        if self.crawl_job.include_patterns:
            patterns = [p.strip() for p in self.crawl_job.include_patterns.split('\n') if p.strip()]
            if patterns:
                matches = any(self.match_pattern(url, pattern) for pattern in patterns)
                if not matches:
                    return False
        
        # Check exclude patterns
        if self.crawl_job.exclude_patterns:
            patterns = [p.strip() for p in self.crawl_job.exclude_patterns.split('\n') if p.strip()]
            for pattern in patterns:
                if self.match_pattern(url, pattern):
                    return False
        
        return True
    
    def match_pattern(self, url: str, pattern: str) -> bool:
        """Check if URL matches a pattern (supports wildcards)."""
        import re
        # Convert pattern to regex
        pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.search(pattern, url))
    
    def store_urls(self) -> int:
        """Store discovered URLs in the database."""
        stored_count = 0
        
        for url in self.discovered_urls:
            # Check if URL already exists for this crawl job
            existing = CrawlUrl.query.filter_by(
                crawl_job_id=self.crawl_job_id,
                url=url
            ).first()
            
            if not existing:
                # Create new crawl URL entry
                crawl_url = CrawlUrl(
                    crawl_job_id=self.crawl_job_id,
                    url=url,
                    is_crawled=False
                )
                db.session.add(crawl_url)
                stored_count += 1
        
        try:
            db.session.commit()
            logger.info(f"Stored {stored_count} new URLs for crawl job {self.crawl_job_id}")
        except Exception as e:
            logger.error(f"Error storing URLs: {e}")
            db.session.rollback()
            stored_count = 0
        
        return stored_count
    
    def reset_crawl_status_for_overwrite(self) -> int:
        """Reset crawl status for all URLs (for overwrite mode)."""
        try:
            updated_count = CrawlUrl.query.filter_by(
                crawl_job_id=self.crawl_job_id,
                is_crawled=True
            ).update({
                'is_crawled': False,
                'crawled_at': None
            })
            db.session.commit()
            logger.info(f"Reset crawl status for {updated_count} URLs")
            return updated_count
        except Exception as e:
            logger.error(f"Error resetting crawl status: {e}")
            db.session.rollback()
            return 0
