#!/usr/bin/env python3
"""
Migration script to add crawl_mode column to existing crawl jobs.
Run this once to update the database schema.
"""

from app import create_app, db
from app.models import CrawlJob

def migrate_crawl_mode():
    """Add crawl_mode column to existing crawl jobs."""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to add the column if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE crawl_jobs ADD COLUMN crawl_mode VARCHAR(20) DEFAULT "incremental" NOT NULL'))
                conn.commit()
            print("✅ Added crawl_mode column to crawl_jobs table")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  crawl_mode column already exists")
            else:
                print(f"❌ Error adding crawl_mode column: {e}")
                return False
        
        try:
            # Update any existing jobs that might have NULL crawl_mode
            db.session.execute(
                db.text("UPDATE crawl_jobs SET crawl_mode = 'incremental' WHERE crawl_mode IS NULL")
            )
            db.session.commit()
            print("✅ Updated existing crawl jobs with default crawl_mode")
        except Exception as e:
            print(f"❌ Error updating existing crawl jobs: {e}")
            return False
        
        print("🎉 Migration completed successfully!")
        return True

if __name__ == '__main__':
    migrate_crawl_mode()
