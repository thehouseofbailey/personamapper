#!/usr/bin/env python3
"""
Migration: Assign existing personas to existing "Whole Site" crawl job
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
        # Get the "Whole Site" crawl job
        cursor.execute("SELECT id, name FROM crawl_jobs WHERE name = 'Whole Site'")
        crawl_job = cursor.fetchone()
        
        if not crawl_job:
            print("Could not find 'Whole Site' crawl job. Please check the database.")
            return
        
        crawl_job_id = crawl_job[0]
        print(f"Found crawl job: ID {crawl_job_id} - {crawl_job[1]}")
        
        # Get all active personas
        cursor.execute("SELECT id, title FROM personas WHERE is_active = 1")
        personas = cursor.fetchall()
        
        if not personas:
            print("No active personas found in the database.")
            return
        
        print(f"Found {len(personas)} active personas:")
        for persona in personas:
            print(f"  - ID {persona[0]}: {persona[1]}")
        
        # Check if any assignments already exist
        cursor.execute("SELECT COUNT(*) FROM crawl_job_personas WHERE crawl_job_id = ?", (crawl_job_id,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"Found {existing_count} existing persona assignments for this crawl job.")
            response = input("Do you want to proceed and add missing assignments? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return
        
        # Assign each persona to the crawl job
        assignments_made = 0
        for persona in personas:
            persona_id = persona[0]
            persona_title = persona[1]
            
            # Check if assignment already exists
            cursor.execute(
                "SELECT COUNT(*) FROM crawl_job_personas WHERE crawl_job_id = ? AND persona_id = ?", 
                (crawl_job_id, persona_id)
            )
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                # Insert the assignment
                cursor.execute(
                    "INSERT INTO crawl_job_personas (crawl_job_id, persona_id, created_at) VALUES (?, ?, ?)",
                    (crawl_job_id, persona_id, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
                )
                assignments_made += 1
                print(f"  ✓ Assigned persona '{persona_title}' to crawl job")
            else:
                print(f"  - Persona '{persona_title}' already assigned to crawl job")
        
        if assignments_made > 0:
            conn.commit()
            print(f"\nMigration completed successfully!")
            print(f"Made {assignments_made} new persona assignments.")
        else:
            print(f"\nNo new assignments needed. All personas already assigned.")
        
        # Verify the results
        cursor.execute("""
            SELECT p.id, p.title 
            FROM personas p
            JOIN crawl_job_personas cjp ON p.id = cjp.persona_id
            WHERE cjp.crawl_job_id = ?
        """, (crawl_job_id,))
        
        assigned_personas = cursor.fetchall()
        print(f"\nFinal verification: {len(assigned_personas)} personas assigned to 'Whole Site' crawl job:")
        for persona in assigned_personas:
            print(f"  - {persona[1]}")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
