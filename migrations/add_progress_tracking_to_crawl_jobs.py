"""
Add progress tracking fields to crawl_jobs table.
This migration adds fields for real-time progress monitoring.
"""

from app import create_app, db
from app.models import CrawlJob
import sys

def add_progress_tracking_fields():
    """Add new fields for progress tracking to crawl_jobs table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the columns already exist by trying to access them
            test_job = CrawlJob.query.first()
            if test_job:
                # Try to access the new columns
                _ = test_job.total_discovered_urls
                _ = test_job.last_activity_at
                _ = test_job.progress_percentage
                print("Progress tracking fields already exist.")
                return
        except Exception:
            # Columns don't exist, proceed with adding them
            pass
        
        try:
            # Add the new columns using raw SQL
            db.engine.execute("""
                ALTER TABLE crawl_jobs 
                ADD COLUMN total_discovered_urls INTEGER DEFAULT 0 NOT NULL
            """)
            print("Added total_discovered_urls column")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                print(f"Error adding total_discovered_urls: {e}")
        
        try:
            db.engine.execute("""
                ALTER TABLE crawl_jobs 
                ADD COLUMN last_activity_at DATETIME
            """)
            print("Added last_activity_at column")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                print(f"Error adding last_activity_at: {e}")
        
        try:
            db.engine.execute("""
                ALTER TABLE crawl_jobs 
                ADD COLUMN progress_percentage FLOAT DEFAULT 0.0 NOT NULL
            """)
            print("Added progress_percentage column")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                print(f"Error adding progress_percentage: {e}")
        
        # Commit the changes
        db.session.commit()
        print("Progress tracking fields migration completed successfully!")

if __name__ == '__main__':
    add_progress_tracking_fields()