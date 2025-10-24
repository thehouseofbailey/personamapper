#!/usr/bin/env python3
"""
Standalone crawler script for running crawl jobs as subprocess on PythonAnywhere.
This script is designed to run independently of the web application.
"""

import sys
import os
import logging
from datetime import datetime

# Add the app directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """Setup logging for the standalone crawler."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def run_crawl_job(crawl_job_id):
    """Run a specific crawl job."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Import Flask app and models
        from app import create_app, db
        from app.models import CrawlJob
        from app.services.web_crawler_pythonanywhere import PythonAnywhereWebCrawler
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Get the crawl job
            crawl_job = CrawlJob.query.get(crawl_job_id)
            if not crawl_job:
                logger.error(f"Crawl job {crawl_job_id} not found")
                return False
            
            logger.info(f"SUBPROCESS: Starting crawl job {crawl_job_id} - {crawl_job.name} (status: {crawl_job.status})")
            
            # Create and run crawler
            crawler = PythonAnywhereWebCrawler(crawl_job_id)
            
            try:
                logger.info(f"SUBPROCESS: Starting crawler.start_crawl() for job {crawl_job_id}")
                crawler.start_crawl()
                logger.info(f"SUBPROCESS: Completed crawl job {crawl_job_id} successfully")
                
                # Update final status
                crawl_job = CrawlJob.query.get(crawl_job_id)  # Refresh from DB
                if crawl_job:
                    crawl_job.update_status('completed')
                    db.session.commit()
                    
                return True
                
            except Exception as e:
                logger.error(f"SUBPROCESS: Crawler failed for job {crawl_job_id}: {e}")
                
                # Update job status to failed
                crawl_job = CrawlJob.query.get(crawl_job_id)  # Refresh from DB
                if crawl_job:
                    crawl_job.update_status('failed', str(e))
                    db.session.commit()
                    
                return False
                
    except Exception as e:
        logger.error(f"SUBPROCESS: Critical error running crawl job {crawl_job_id}: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python standalone_crawler.py <crawl_job_id>")
        sys.exit(1)
    
    try:
        crawl_job_id = int(sys.argv[1])
    except ValueError:
        print("Error: crawl_job_id must be an integer")
        sys.exit(1)
    
    success = run_crawl_job(crawl_job_id)
    sys.exit(0 if success else 1)