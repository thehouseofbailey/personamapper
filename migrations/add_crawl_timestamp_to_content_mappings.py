"""
Database migration script to add crawl_timestamp field to content_mappings table.
Run this script to update the database schema for historical tracking.
"""

import sqlite3
import os

def migrate_add_crawl_timestamp():
    """Add crawl_timestamp field to content_mappings table."""
    
    # Get database path
    db_path = os.path.join('instance', 'personamap.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(content_mappings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new column if it doesn't exist
        if 'crawl_timestamp' not in columns:
            print("Adding crawl_timestamp column...")
            cursor.execute("ALTER TABLE content_mappings ADD COLUMN crawl_timestamp DATETIME")
            
            # Set crawl_timestamp to created_at for existing records
            print("Setting crawl_timestamp for existing records...")
            cursor.execute("UPDATE content_mappings SET crawl_timestamp = created_at WHERE crawl_timestamp IS NULL")
        else:
            print("crawl_timestamp column already exists")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show updated table structure
        cursor.execute("PRAGMA table_info(content_mappings)")
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
        print("The content_mappings table now includes crawl_timestamp for historical tracking.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")
