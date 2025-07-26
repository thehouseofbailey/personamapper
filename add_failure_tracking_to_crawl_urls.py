"""
Database migration script to add failure tracking fields to crawl_urls table.
Run this script to update the database schema.
"""

import sqlite3
import os

def migrate_database():
    """Add failure tracking fields to crawl_urls table."""
    
    # Get database path
    db_path = os.path.join('instance', 'personamap.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(crawl_urls)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'failed_attempts' not in columns:
            print("Adding failed_attempts column...")
            cursor.execute("ALTER TABLE crawl_urls ADD COLUMN failed_attempts INTEGER DEFAULT 0 NOT NULL")
        
        if 'is_failed' not in columns:
            print("Adding is_failed column...")
            cursor.execute("ALTER TABLE crawl_urls ADD COLUMN is_failed BOOLEAN DEFAULT 0 NOT NULL")
        
        if 'last_error' not in columns:
            print("Adding last_error column...")
            cursor.execute("ALTER TABLE crawl_urls ADD COLUMN last_error TEXT")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show updated table structure
        cursor.execute("PRAGMA table_info(crawl_urls)")
        columns = cursor.fetchall()
        print("\nUpdated table structure:")
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
        
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    success = migrate_database()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("The crawl_urls table now includes failure tracking fields.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")
