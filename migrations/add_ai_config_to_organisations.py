#!/usr/bin/env python3
"""
Migration: Add AI configuration fields to organisations table
This moves AI settings from global .env configuration to per-organisation settings
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_db_path():
    """Get the database path from the instance directory."""
    if os.path.exists('instance/personamap.db'):
        return 'instance/personamap.db'
    elif os.path.exists('personamap.db'):
        return 'personamap.db'
    else:
        print("Database file not found!")
        sys.exit(1)

def run_migration():
    """Add AI configuration fields to organisations table."""
    db_path = get_db_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Adding AI configuration fields to organisations table...")
        
        # Add AI configuration fields
        ai_fields = [
            ("ai_enabled", "BOOLEAN DEFAULT 0"),
            ("ai_analysis_mode", "TEXT DEFAULT 'keyword'"),
            ("openai_api_key", "TEXT"),
            ("openai_model", "TEXT DEFAULT 'gpt-3.5-turbo'"),
            ("openai_max_tokens", "INTEGER DEFAULT 1000"),
            ("openai_temperature", "REAL DEFAULT 0.3"),
            ("ai_daily_cost_limit", "REAL DEFAULT 10.0"),
            ("ai_monthly_cost_limit", "REAL DEFAULT 100.0"),
            ("local_ai_model", "TEXT DEFAULT 'all-MiniLM-L6-v2'"),
            ("local_ai_similarity_threshold", "REAL DEFAULT 0.5"),
            ("ai_confidence_threshold", "REAL DEFAULT 0.3"),
            ("ai_content_chunk_size", "INTEGER DEFAULT 2000"),
        ]
        
        for field_name, field_type in ai_fields:
            try:
                cursor.execute(f"ALTER TABLE organisations ADD COLUMN {field_name} {field_type}")
                print(f"✓ Added {field_name} field")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"⚠ Field {field_name} already exists, skipping")
                else:
                    print(f"✗ Error adding {field_name}: {e}")
                    raise
        
        # Update the updated_at timestamp for existing organisations
        cursor.execute("UPDATE organisations SET updated_at = ? WHERE id IS NOT NULL", 
                      (datetime.utcnow(),))
        
        conn.commit()
        print("✓ Migration completed successfully!")
        
        # Show current organisations
        cursor.execute("SELECT id, name FROM organisations")
        orgs = cursor.fetchall()
        if orgs:
            print(f"\nFound {len(orgs)} organisations that can now be configured with AI settings:")
            for org_id, org_name in orgs:
                print(f"  - {org_name} (ID: {org_id})")
        else:
            print("\nNo organisations found in database.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("PersonaMap Migration: Add AI Configuration to Organisations")
    print("=" * 60)
    run_migration()
