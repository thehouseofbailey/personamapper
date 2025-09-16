"""
Migration script to add RBAC tables and update existing models.
Run this after the new models are in place.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    User, Organisation, Website, UserOrganisationRole, UserWebsiteRole, 
    OrganisationWebsite, CrawlJob, Persona
)
from datetime import datetime

def run_migration():
    """Run the RBAC migration."""
    app = create_app()
    
    with app.app_context():
        print("Starting RBAC migration...")
        
        # Create new tables
        print("Creating new tables...")
        db.create_all()
        
        # Add new columns to existing tables (SQLite doesn't support ALTER COLUMN)
        try:
            # Check if website_id column exists in crawl_jobs
            result = db.engine.execute("PRAGMA table_info(crawl_jobs)")
            columns = [row[1] for row in result]
            
            if 'website_id' not in columns:
                print("Adding website_id column to crawl_jobs...")
                db.engine.execute("ALTER TABLE crawl_jobs ADD COLUMN website_id INTEGER")
                db.engine.execute("CREATE INDEX IF NOT EXISTS idx_crawl_jobs_website ON crawl_jobs(website_id)")
            
            # Check if website_id column exists in personas
            result = db.engine.execute("PRAGMA table_info(personas)")
            columns = [row[1] for row in result]
            
            if 'website_id' not in columns:
                print("Adding website_id column to personas...")
                db.engine.execute("ALTER TABLE personas ADD COLUMN website_id INTEGER")
                db.engine.execute("CREATE INDEX IF NOT EXISTS idx_personas_website ON personas(website_id)")
            
            # Check if is_super_admin column exists in users
            result = db.engine.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in result]
            
            if 'is_super_admin' not in columns:
                print("Adding is_super_admin column to users...")
                db.engine.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT 0")
                
                # Make existing admin users super admins
                admin_users = User.query.filter_by(role='admin').all()
                for user in admin_users:
                    user.is_super_admin = True
                print(f"Upgraded {len(admin_users)} admin users to super admin status")
            
        except Exception as e:
            print(f"Error adding columns: {e}")
            print("This is normal if columns already exist")
        
        # Create default organisation and website for existing data
        print("Creating default organisation and website...")
        
        default_org = Organisation.query.filter_by(name='Default Organisation').first()
        if not default_org:
            default_org = Organisation(
                name='Default Organisation',
                description='Default organisation created during RBAC migration',
                is_active=True
            )
            db.session.add(default_org)
            db.session.commit()
            print("Created default organisation")
        
        default_website = Website.query.filter_by(name='Default Website').first()
        if not default_website:
            default_website = Website(
                name='Default Website',
                domain='legacy.local',
                description='Default website created during RBAC migration for legacy data',
                is_active=True
            )
            db.session.add(default_website)
            db.session.commit()
            print("Created default website")
        
        # Link default organisation to default website
        org_website = OrganisationWebsite.query.filter_by(
            organisation_id=default_org.id,
            website_id=default_website.id
        ).first()
        
        if not org_website:
            org_website = OrganisationWebsite(
                organisation_id=default_org.id,
                website_id=default_website.id
            )
            db.session.add(org_website)
            db.session.commit()
            print("Linked default organisation to default website")
        
        # Migrate existing users to default organisation
        print("Migrating existing users...")
        users = User.query.all()
        migrated_users = 0
        
        for user in users:
            # Check if user already has organisation roles
            existing_role = UserOrganisationRole.query.filter_by(
                user_id=user.id,
                organisation_id=default_org.id
            ).first()
            
            if not existing_role:
                # Determine role based on legacy role
                if user.is_super_admin or user.role == 'admin':
                    role = 'org_admin'
                elif user.role == 'editor':
                    role = 'website_manager'
                else:
                    role = 'website_viewer'
                
                # Add to organisation
                user_org_role = UserOrganisationRole(
                    user_id=user.id,
                    organisation_id=default_org.id,
                    role=role
                )
                db.session.add(user_org_role)
                
                # Add website access based on role
                if role in ['org_admin', 'website_manager', 'website_viewer']:
                    existing_website_role = UserWebsiteRole.query.filter_by(
                        user_id=user.id,
                        website_id=default_website.id
                    ).first()
                    
                    if not existing_website_role:
                        website_role = 'website_manager' if role in ['org_admin', 'website_manager'] else 'website_viewer'
                        user_website_role = UserWebsiteRole(
                            user_id=user.id,
                            website_id=default_website.id,
                            role=website_role
                        )
                        db.session.add(user_website_role)
                
                migrated_users += 1
        
        db.session.commit()
        print(f"Migrated {migrated_users} users to RBAC system")
        
        # Update existing crawl jobs to use default website
        print("Updating existing crawl jobs...")
        crawl_jobs = CrawlJob.query.filter_by(website_id=None).all()
        updated_jobs = 0
        
        for job in crawl_jobs:
            job.website_id = default_website.id
            updated_jobs += 1
        
        db.session.commit()
        print(f"Updated {updated_jobs} crawl jobs to use default website")
        
        # Update existing personas to use default website
        print("Updating existing personas...")
        personas = Persona.query.filter_by(website_id=None).all()
        updated_personas = 0
        
        for persona in personas:
            persona.website_id = default_website.id
            updated_personas += 1
        
        db.session.commit()
        print(f"Updated {updated_personas} personas to use default website")
        
        print("RBAC migration completed successfully!")
        print("\nSummary:")
        print(f"- Created {1 if not Organisation.query.filter_by(name='Default Organisation').first() else 0} organisation")
        print(f"- Created {1 if not Website.query.filter_by(name='Default Website').first() else 0} website")
        print(f"- Migrated {migrated_users} users")
        print(f"- Updated {updated_jobs} crawl jobs")
        print(f"- Updated {updated_personas} personas")
        
        # Show current state
        print(f"\nCurrent state:")
        print(f"- Total organisations: {Organisation.query.count()}")
        print(f"- Total websites: {Website.query.count()}")
        print(f"- Total users: {User.query.count()}")
        print(f"- Super admins: {User.query.filter_by(is_super_admin=True).count()}")
        print(f"- Organisation roles: {UserOrganisationRole.query.count()}")
        print(f"- Website roles: {UserWebsiteRole.query.count()}")

if __name__ == '__main__':
    run_migration()
