#!/usr/bin/env python3
"""
Migration: Create crawl_job_personas association table
"""

import sqlite3
import os
from datetime import datetime

def run_migration():
    # Get the database path
    db_path = os.path.join('instance', 'personamap.db')
    
    if not os.path.exists(db_path):
        print("Database not found. Please run the application first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crawl_job_personas'")
        if cursor.fetchone():
            print("Table 'crawl_job_personas' already exists. Skipping migration.")
            return
        
        print("Creating crawl_job_personas table...")
        
        # Create the crawl_job_personas table
        cursor.execute('''
            CREATE TABLE crawl_job_personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_job_id INTEGER NOT NULL,
                persona_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs (id) ON DELETE CASCADE,
                FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE,
                CONSTRAINT unique_crawl_job_persona UNIQUE (crawl_job_id, persona_id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX idx_crawl_job_personas_crawl_job_id ON crawl_job_personas (crawl_job_id)')
        cursor.execute('CREATE INDEX idx_crawl_job_personas_persona_id ON crawl_job_personas (persona_id)')
        
        conn.commit()
        print("Migration completed successfully!")
        print("Created table: crawl_job_personas")
        print("Created indexes for foreign key columns")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
