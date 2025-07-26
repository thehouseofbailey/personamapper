#!/usr/bin/env python3
"""
Migration script to create the crawl_urls table.
"""

from app import create_app, db
from app.models import CrawlUrl

def create_crawl_urls_table():
    """Create the crawl_urls table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ Successfully created crawl_urls table")
            
            # Verify the table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'crawl_urls' in tables:
                print("✅ crawl_urls table verified in database")
                
                # Show table structure
                columns = inspector.get_columns('crawl_urls')
                print("\n📋 Table structure:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
                
                # Show indexes
                indexes = inspector.get_indexes('crawl_urls')
                if indexes:
                    print("\n🔍 Indexes:")
                    for index in indexes:
                        print(f"  - {index['name']}: {index['column_names']}")
            else:
                print("❌ crawl_urls table not found")
                
        except Exception as e:
            print(f"❌ Error creating table: {e}")

if __name__ == '__main__':
    create_crawl_urls_table()
