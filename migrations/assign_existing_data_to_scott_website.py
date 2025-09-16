#!/usr/bin/env python3
"""
Migration: Assign existing crawl jobs and personas to Scott Andrew Bailey website
Created: 2025-09-15
"""

import sqlite3
import os

def migrate_assign_existing_data():
    """Assign existing unassigned crawl jobs and personas to Scott Andrew Bailey website"""
    
    # Get database path
    db_path = os.path.join('instance', 'personamap.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== Assigning Existing Data to Scott Andrew Bailey Website ===")
        
        # Find Scott Andrew Bailey website ID
        cursor.execute("SELECT id, name FROM websites WHERE name = 'Scott Andrew Bailey'")
        website = cursor.fetchone()
        
        if not website:
            print("ERROR: Scott Andrew Bailey website not found!")
            return False
            
        scott_website_id = website[0]
        print(f"Found website: {website[1]} (ID: {scott_website_id})")
        
        # Check and assign unassigned crawl jobs
        cursor.execute("SELECT id, name, base_url FROM crawl_jobs WHERE website_id IS NULL")
        unassigned_crawls = cursor.fetchall()
        
        if unassigned_crawls:
            print(f"\nAssigning {len(unassigned_crawls)} crawl jobs:")
            for crawl in unassigned_crawls:
                print(f"  - Crawl {crawl[0]}: {crawl[1]} ({crawl[2]})")
                cursor.execute("UPDATE crawl_jobs SET website_id = ? WHERE id = ?", 
                             (scott_website_id, crawl[0]))
        else:
            print("\nNo unassigned crawl jobs found.")
        
        # Check and assign unassigned personas
        cursor.execute("SELECT id, title FROM personas WHERE website_id IS NULL")
        unassigned_personas = cursor.fetchall()
        
        if unassigned_personas:
            print(f"\nAssigning {len(unassigned_personas)} personas:")
            for persona in unassigned_personas:
                print(f"  - Persona {persona[0]}: {persona[1]}")
                cursor.execute("UPDATE personas SET website_id = ? WHERE id = ?", 
                             (scott_website_id, persona[0]))
        else:
            print("\nNo unassigned personas found.")
        
        # Commit changes
        conn.commit()
        
        # Verify assignments
        print("\n=== Verification ===")
        cursor.execute("SELECT COUNT(*) FROM crawl_jobs WHERE website_id = ?", (scott_website_id,))
        crawl_count = cursor.fetchone()[0]
        print(f"Scott Andrew Bailey website now has {crawl_count} crawl jobs")
        
        cursor.execute("SELECT COUNT(*) FROM personas WHERE website_id = ?", (scott_website_id,))
        persona_count = cursor.fetchone()[0]
        print(f"Scott Andrew Bailey website now has {persona_count} personas")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Migration failed - {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_assign_existing_data()
