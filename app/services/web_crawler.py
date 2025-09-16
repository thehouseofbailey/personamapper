import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser
import time
import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
import threading
from queue import Queue, Empty
from app.models import CrawlJob, CrawledPage, Persona, ContentMapping, CrawlUrl
from app.services.unified_analyzer import UnifiedContentAnalyzer
from app.services.sitemap_service import SitemapService
from flask import current_app
from app import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebCrawler:
    """
    A comprehensive web crawler that respects robots.txt, handles rate limiting,
    and extracts content for persona mapping.
    """
    
    def __init__(self, crawl_job_id: int):
        self.crawl_job_id = crawl_job_id
        self.crawl_job = None
        self.session = requests.Session()
        # Use configurable user agent from environment, with fallback to current working default
        user_agent = current_app.config.get(
            'CRAWLER_USER_AGENT', 
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.session.headers.update({
            'User-Agent': user_agent
        })
        
        # Crawler settings
        self.delay = 1.0  # Delay between requests (seconds)
        self.timeout = 30  # Request timeout
        self.max_retries = 3
        self.respect_robots = False  # Disable robots.txt checking for testing
        
        # URL tracking
        self.visited_urls: Set[str] = set()
        self.url_queue: Queue = Queue()
        self.failed_urls: Set[str] = set()
        
        # Content analyzer (will be initialized after crawl job is loaded)
        self.content_analyzer = None
        
        # Robots.txt cache
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_processed': 0,
            'pages_mapped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Control flags
        self.should_stop = False
        self.is_running = False
    
    def load_crawl_job(self) -> bool:
        """Load the crawl job from database."""
        try:
            self.crawl_job = CrawlJob.query.get(self.crawl_job_id)
            if not self.crawl_job:
                logger.error(f"Crawl job {self.crawl_job_id} not found")
                return False
            
            # Initialize content analyzer with website-specific AI config
            website_id = self.crawl_job.website_id if self.crawl_job else None
            self.content_analyzer = UnifiedContentAnalyzer(website_id=website_id)
            logger.info(f"Content analyzer initialized for website {website_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error loading crawl job: {e}")
            return False
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if base_url not in self.robots_cache:
                robots_url = urljoin(base_url, '/robots.txt')
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self.robots_cache[base_url] = rp
                except:
                    # If robots.txt can't be read, assume we can crawl
                    self.robots_cache[base_url] = None
            
            robots = self.robots_cache[base_url]
            if robots:
                return robots.can_fetch(self.session.headers['User-Agent'], url)
            return True
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and unnecessary parameters."""
        parsed = urlparse(url)
        # Remove fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip('/')
    
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
                logger.debug(f"Skipping binary file: {url}")
                return False
        
        # Check for common patterns that indicate non-HTML content
        if any(pattern in path for pattern in ['/api/', '/feed/', '/rss/', '/sitemap']):
            if not path.endswith('.html') and not path.endswith('.htm'):
                logger.debug(f"Skipping API/feed URL: {url}")
                return False
        
        return True
    
    def should_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled based on patterns and rules."""
        if not url or url in self.visited_urls:
            return False

        # Check if URL matches base domain
        base_domain = urlparse(self.crawl_job.base_url).netloc
        url_domain = urlparse(url).netloc
        if url_domain != base_domain:
            return False

        # Check if URL already exists in database for this crawl job (for incremental mode)
        if self.crawl_job.crawl_mode == 'incremental':
            existing_page = CrawledPage.query.filter_by(
                url=url, 
                crawl_job_id=self.crawl_job.id
            ).first()
            if existing_page:
                logger.info(f"Skipping already crawled URL in incremental mode for this crawl job: {url}")
                return False

        # Check include patterns
        if self.crawl_job.include_patterns:
            patterns = [p.strip() for p in self.crawl_job.include_patterns.split('\n') if p.strip()]
            if patterns:
                matches = any(self.match_pattern(url, pattern) for pattern in patterns)
                if not matches:
                    return False

        # Check exclude patterns (now checks both path and query string)
        if self.crawl_job.exclude_patterns:
            patterns = [p.strip() for p in self.crawl_job.exclude_patterns.split('\n') if p.strip()]
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            for pattern in patterns:
                # Check path
                if self.match_pattern(parsed.path, pattern):
                    return False
                # Check query string (raw)
                if self.match_pattern(parsed.query, pattern):
                    return False
                # Check query parameters individually for patterns like 'share=*'
                if '=' in pattern:
                    key, value = pattern.split('=', 1)
                    for param_key, param_values in query_params.items():
                        if self.match_pattern(param_key, key):
                            for param_value in param_values:
                                if self.match_pattern(param_value, value):
                                    return False
        return True
    
    def match_pattern(self, url: str, pattern: str) -> bool:
        """Check if URL matches a pattern (supports wildcards)."""
        # Convert pattern to regex
        pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.search(pattern, url))
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from a page."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            normalized_url = self.normalize_url(absolute_url)
            
            # Filter out binary files and non-HTML content
            if not self.is_html_content_url(normalized_url):
                continue
            
            # Basic filtering - domain check and patterns, but not existence check
            if self.is_valid_url_for_crawling(normalized_url):
                links.append(normalized_url)
        
        return links
    
    def is_valid_url_for_crawling(self, url: str) -> bool:
        """Check if URL is valid for crawling (domain and patterns only, not existence)."""
        if not url:
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
        
        # Check exclude patterns (now checks both path and query string)
        if self.crawl_job.exclude_patterns:
            patterns = [p.strip() for p in self.crawl_job.exclude_patterns.split('\n') if p.strip()]
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            for pattern in patterns:
                if self.match_pattern(parsed.path, pattern):
                    return False
                if self.match_pattern(parsed.query, pattern):
                    return False
                if '=' in pattern:
                    key, value = pattern.split('=', 1)
                    for param_key, param_values in query_params.items():
                        if self.match_pattern(param_key, key):
                            for param_value in param_values:
                                if self.match_pattern(param_value, value):
                                    return False
        return True
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract content from a page."""
        try:
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ''
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '').strip() if meta_desc else ''
            
            # Extract main content (remove script, style, nav, footer, etc.)
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|body'))
            if not main_content:
                main_content = soup.find('body') or soup
            
            # Extract text content
            text_content = main_content.get_text(separator=' ', strip=True)
            
            # Clean up text
            text_content = re.sub(r'\s+', ' ', text_content)
            text_content = text_content.strip()
            
            # Extract headings
            headings = []
            for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                headings.append(h.get_text().strip())
            
            # Calculate word count
            word_count = len(text_content.split()) if text_content else 0
            
            return {
                'title': title,
                'description': description,
                'content': text_content,
                'headings': headings,
                'word_count': word_count
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                'title': '',
                'description': '',
                'content': '',
                'headings': [],
                'word_count': 0
            }
    
    def fetch_page(self, url: str) -> Optional[Tuple[requests.Response, BeautifulSoup]]:
        """Fetch a single page and return response and parsed content."""
        for attempt in range(self.max_retries):
            try:
                # Check robots.txt (only if respect_robots is True)
                if self.respect_robots and not self.can_fetch(url):
                    logger.info(f"Robots.txt disallows crawling {url}")
                    return None
                
                # Make request
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Parse content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                return response, soup
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    self.stats['errors'] += 1
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                self.stats['errors'] += 1
                return None
    
    def save_page(self, url: str, content_data: Dict, response: requests.Response) -> Optional[CrawledPage]:
        """Save crawled page to database."""
        try:
            # Check if page already exists
            existing_page = CrawledPage.query.filter_by(
                crawl_job_id=self.crawl_job_id,
                url=url
            ).first()
            
            if existing_page:
                # Update existing page
                existing_page.title = content_data['title']
                existing_page.content = content_data['content']
                existing_page.word_count = content_data['word_count']
                existing_page.crawled_at = datetime.utcnow()
                existing_page.status_code = response.status_code
                existing_page.is_processed = True
                page = existing_page
            else:
                # Create new page
                page = CrawledPage(
                    crawl_job_id=self.crawl_job_id,
                    url=url,
                    title=content_data['title'],
                    content=content_data['content'],
                    word_count=content_data['word_count'],
                    crawled_at=datetime.utcnow(),
                    status_code=response.status_code,
                    is_processed=True
                )
                db.session.add(page)
            
            db.session.commit()
            self.stats['pages_processed'] += 1
            
            return page
            
        except Exception as e:
            logger.error(f"Error saving page {url}: {e}")
            db.session.rollback()
            return None
    
    def analyze_and_map_content(self, page: CrawledPage) -> None:
        """Analyze page content and create persona mappings with historical tracking."""
        try:
            # Get all active personas
            personas = Persona.query.filter_by(is_active=True).all()
            crawl_timestamp = datetime.utcnow()
            
            # For historical tracking, we always create new mappings
            # First, deactivate previous mappings for this page (keep for history)
            previous_mappings = ContentMapping.query.filter_by(
                page_id=page.id,
                is_active=True
            ).all()
            
            for prev_mapping in previous_mappings:
                prev_mapping.is_active = False
                prev_mapping.updated_at = crawl_timestamp
            
            logger.info(f"Deactivated {len(previous_mappings)} previous mappings for page {page.url} (historical tracking)")
            
            # Create new mappings for this crawl
            new_mappings_count = 0
            
            # Ensure content analyzer is available
            if not self.content_analyzer:
                logger.error("Content analyzer not initialized. Cannot create mappings.")
                return 0
            
            for persona in personas:
                # Analyze content for this persona
                mapping_result = self.content_analyzer.analyze_content_for_persona(
                    page.content, persona
                )
                
                if mapping_result['should_map']:
                    # Create new content mapping with crawl timestamp
                    mapping = ContentMapping(
                        persona_id=persona.id,
                        page_id=page.id,
                        confidence_score=mapping_result['confidence'],
                        mapping_reason=mapping_result['reason'],
                        mapping_method='automated_crawl',
                        crawl_timestamp=crawl_timestamp,
                        is_active=True
                    )
                    
                    db.session.add(mapping)
                    new_mappings_count += 1
                    self.stats['pages_mapped'] += 1
                    logger.info(f"Created new mapping for page {page.url} -> persona {persona.title} (confidence: {mapping_result['confidence']:.2f})")
            
            logger.info(f"Created {new_mappings_count} new mappings for page {page.url}")
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error analyzing content for page {page.url}: {e}")
            db.session.rollback()
    
    def crawl_page(self, url: str) -> bool:
        """Crawl a single page and process it. Returns True if page was actually crawled (not skipped)."""
        try:
            logger.info(f"Crawling: {url}")
            
            # Fetch page
            result = self.fetch_page(url)
            if not result:
                return False
            
            response, soup = result
            
            # Extract content
            content_data = self.extract_content(soup, url)
            
            # Save page to database
            page = self.save_page(url, content_data, response)
            if not page:
                return False
            
            # Analyze content and create mappings
            self.analyze_and_map_content(page)
            
            # Extract and queue new links
            links = self.extract_links(soup, url)
            for link in links:
                if link not in self.visited_urls and self.stats['pages_crawled'] < self.crawl_job.max_pages:
                    self.url_queue.put(link)
            
            # Only increment counter for actually crawled pages
            self.stats['pages_crawled'] += 1
            logger.info(f"Successfully crawled {url} ({self.stats['pages_crawled']}/{self.crawl_job.max_pages})")
            return True
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            self.stats['errors'] += 1
            return False
    
    def update_job_status(self, status: str) -> None:
        """Update crawl job status in database."""
        try:
            self.crawl_job.update_status(status)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
    
    def start_crawl(self) -> None:
        """Start the sitemap-based crawling process."""
        # Get the Flask app context
        from app import create_app
        app = create_app()
        
        with app.app_context():
            try:
                # Load crawl job
                if not self.load_crawl_job():
                    return
                
                logger.info(f"Starting sitemap-based crawl job: {self.crawl_job.name}")
                
                # Initialize
                self.is_running = True
                self.should_stop = False
                self.stats['start_time'] = datetime.utcnow()
                
                # Update job status
                self.update_job_status('running')
                
                # Step 1: Discover URLs from sitemaps (if not already done)
                sitemap_service = SitemapService(self.crawl_job_id)
                
                # Check if we need to discover URLs
                existing_urls_count = CrawlUrl.query.filter_by(crawl_job_id=self.crawl_job_id).count()
                if existing_urls_count == 0:
                    logger.info("No URLs found in database, discovering from sitemaps...")
                    discovered_count = sitemap_service.discover_and_store_urls()
                    logger.info(f"Discovered {discovered_count} URLs from sitemaps")
                else:
                    logger.info(f"Found {existing_urls_count} existing URLs in database")
                
                # Step 2: Handle overwrite mode - reset crawl status
                if self.crawl_job.crawl_mode == 'overwrite':
                    reset_count = sitemap_service.reset_crawl_status_for_overwrite()
                    logger.info(f"Reset crawl status for {reset_count} URLs (overwrite mode)")
                
                # Step 3: Get URLs to crawl (not yet crawled and not failed, up to max_pages limit)
                urls_to_crawl = CrawlUrl.query.filter_by(
                    crawl_job_id=self.crawl_job_id,
                    is_crawled=False,
                    is_failed=False
                ).limit(self.crawl_job.max_pages).all()
                
                logger.info(f"Found {len(urls_to_crawl)} URLs to crawl")
                
                if not urls_to_crawl:
                    logger.info("No URLs to crawl - all URLs have been processed")
                    self.update_job_status('completed')
                    return
                
                # Step 4: Crawl the URLs
                for i, crawl_url in enumerate(urls_to_crawl):
                    if self.should_stop:
                        break

                    url = crawl_url.url

                    # Skip and DELETE URLs matching exclude patterns
                    if not self.should_crawl_url(url):
                        logger.info(f"Deleting excluded URL from crawl queue: {url}")
                        try:
                            db.session.delete(crawl_url)
                            db.session.commit()
                        except Exception as e:
                            logger.error(f"Error deleting excluded URL {url}: {e}")
                            db.session.rollback()
                        continue

                    logger.info(f"Crawling URL {i+1}/{len(urls_to_crawl)}: {url}")

                    # Crawl the page
                    success, error_message = self.crawl_page_from_sitemap(url)
                    
                    if success:
                        # Mark URL as crawled
                        crawl_url.mark_as_crawled()
                        self.stats['pages_crawled'] += 1
                        logger.info(f"Successfully crawled {url} ({self.stats['pages_crawled']}/{len(urls_to_crawl)})")
                    else:
                        # Mark URL as failed
                        crawl_url.mark_as_failed(error_message or "Unknown error")
                        logger.warning(f"Failed to crawl {url} (attempt {crawl_url.failed_attempts}/3): {error_message}")
                        
                        if crawl_url.is_failed:
                            logger.error(f"URL permanently failed after 3 attempts: {url}")
                    
                    # Rate limiting
                    time.sleep(self.delay)
                
                # Finish crawling
                self.stats['end_time'] = datetime.utcnow()
                
                # Update final status
                if self.should_stop:
                    self.update_job_status('inactive')
                    logger.info("Crawl job stopped by user")
                else:
                    # Check if there are more URLs to crawl
                    remaining_urls = CrawlUrl.query.filter_by(
                        crawl_job_id=self.crawl_job_id,
                        is_crawled=False
                    ).count()
                    
                    if remaining_urls > 0:
                        self.update_job_status('completed')
                        logger.info(f"Crawl batch completed - {remaining_urls} URLs remaining for next run")
                    else:
                        self.update_job_status('completed')
                        logger.info("Crawl job completed - all URLs processed")
                
                # Log final statistics
                duration = self.stats['end_time'] - self.stats['start_time']
                logger.info(f"Crawl completed in {duration}")
                logger.info(f"Pages crawled: {self.stats['pages_crawled']}")
                logger.info(f"Pages processed: {self.stats['pages_processed']}")
                logger.info(f"Pages mapped: {self.stats['pages_mapped']}")
                logger.info(f"Errors: {self.stats['errors']}")
                
            except Exception as e:
                logger.error(f"Error in crawl process: {e}")
                self.update_job_status('failed')
            finally:
                self.is_running = False
                self.session.close()
                
                # Clean up from crawler manager
                try:
                    if self.crawl_job_id in crawler_manager.active_crawlers:
                        del crawler_manager.active_crawlers[self.crawl_job_id]
                    if self.crawl_job_id in crawler_manager.crawler_threads:
                        del crawler_manager.crawler_threads[self.crawl_job_id]
                    logger.info(f"Cleaned up crawler manager for job {self.crawl_job_id}")
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up crawler manager: {cleanup_error}")
    
    def crawl_page_from_sitemap(self, url: str) -> Tuple[bool, Optional[str]]:
        """Crawl a single page from sitemap and discover new URLs from internal links."""
        try:
            # Fetch page
            result = self.fetch_page(url)
            if not result:
                return False, "Failed to fetch page"
            
            response, soup = result
            
            # Extract content
            content_data = self.extract_content(soup, url)
            
            # Save page to database
            page = self.save_page(url, content_data, response)
            if not page:
                return False, "Failed to save page to database"
            
            # Analyze content and create mappings
            self.analyze_and_map_content(page)
            
            # Extract and store new URLs found on this page
            self.discover_and_store_new_urls(soup, url)
            
            return True, None
            
        except Exception as e:
            error_message = f"Error crawling {url}: {str(e)}"
            logger.error(error_message)
            self.stats['errors'] += 1
            return False, str(e)
    
    def discover_and_store_new_urls(self, soup: BeautifulSoup, base_url: str) -> int:
        """Extract links from page and store any new URLs not already in crawl_urls table."""
        try:
            # Extract all links from the page
            links = self.extract_links(soup, base_url)
            
            new_urls_count = 0
            for link in links:
                # Check if URL already exists in crawl_urls table
                existing_url = CrawlUrl.query.filter_by(
                    crawl_job_id=self.crawl_job_id,
                    url=link
                ).first()
                
                if not existing_url:
                    # Create new crawl URL entry
                    crawl_url = CrawlUrl(
                        crawl_job_id=self.crawl_job_id,
                        url=link,
                        is_crawled=False,
                        priority=1  # Lower priority than sitemap URLs
                    )
                    db.session.add(crawl_url)
                    new_urls_count += 1
            
            if new_urls_count > 0:
                db.session.commit()
                logger.info(f"Discovered {new_urls_count} new URLs from page {base_url}")
            
            return new_urls_count
            
        except Exception as e:
            logger.error(f"Error discovering URLs from {base_url}: {e}")
            db.session.rollback()
            return 0
    
    def stop_crawl(self) -> None:
        """Stop the crawling process."""
        logger.info("Stopping crawl job...")
        self.should_stop = True


# Crawler manager for handling background crawling
class CrawlerManager:
    """Manages crawler instances and background processing."""
    
    def __init__(self):
        self.active_crawlers: Dict[int, WebCrawler] = {}
        self.crawler_threads: Dict[int, threading.Thread] = {}
    
    def start_crawl_job(self, crawl_job_id: int) -> bool:
        """Start a crawl job in the background."""
        try:
            if crawl_job_id in self.active_crawlers:
                logger.warning(f"Crawl job {crawl_job_id} is already running")
                return False
            
            # Create crawler instance
            crawler = WebCrawler(crawl_job_id)
            
            # Create and start thread
            thread = threading.Thread(target=crawler.start_crawl, daemon=True)
            thread.start()
            
            # Store references
            self.active_crawlers[crawl_job_id] = crawler
            self.crawler_threads[crawl_job_id] = thread
            
            logger.info(f"Started crawl job {crawl_job_id} in background")
            return True
            
        except Exception as e:
            logger.error(f"Error starting crawl job {crawl_job_id}: {e}")
            return False
    
    def stop_crawl_job(self, crawl_job_id: int) -> bool:
        """Stop a running crawl job."""
        try:
            if crawl_job_id not in self.active_crawlers:
                logger.warning(f"Crawl job {crawl_job_id} is not running")
                return False
            
            # Stop the crawler
            crawler = self.active_crawlers[crawl_job_id]
            crawler.stop_crawl()
            
            # Wait for thread to finish (with timeout)
            thread = self.crawler_threads[crawl_job_id]
            thread.join(timeout=10)
            
            # Clean up
            del self.active_crawlers[crawl_job_id]
            del self.crawler_threads[crawl_job_id]
            
            logger.info(f"Stopped crawl job {crawl_job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping crawl job {crawl_job_id}: {e}")
            return False
    
    def is_crawl_running(self, crawl_job_id: int) -> bool:
        """Check if a crawl job is currently running."""
        return crawl_job_id in self.active_crawlers
    
    def get_crawl_stats(self, crawl_job_id: int) -> Optional[Dict]:
        """Get statistics for a running crawl job."""
        if crawl_job_id in self.active_crawlers:
            return self.active_crawlers[crawl_job_id].stats
        return None


# Global crawler manager instance
crawler_manager = CrawlerManager()
