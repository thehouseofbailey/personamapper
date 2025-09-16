#!/usr/bin/env python3
"""
PersonaMap Application Entry Point

This is the main entry point for the PersonaMap application.
Run this file to start the Flask development server.
"""

import os
from app import create_app, db
from app.models import (
    User, Persona, CrawlJob, CrawledPage, ContentMapping,
    Organisation, Website, UserOrganisationRole, UserWebsiteRole
)

from dotenv import load_dotenv
load_dotenv()

app = create_app()
print("Database URI:", app.config.get("SQLALCHEMY_DATABASE_URI"))

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        'db': db,
        'User': User,
        'Persona': Persona,
        'CrawlJob': CrawlJob,
        'CrawledPage': CrawledPage,
        'ContentMapping': ContentMapping,
        'Organisation': Organisation,
        'Website': Website,
        'UserOrganisationRole': UserOrganisationRole,
        'UserWebsiteRole': UserWebsiteRole
    }

@app.cli.command()
def init_db():
    """Initialize the database with sample data."""
    with app.app_context():
        print("Running init_db...")
        db.create_all()

        # Run migrations
        from migrations.migrate_user_roles import migrate_user_roles
        from migrations.add_crawl_timestamp_to_content_mappings import migrate_add_crawl_timestamp
        from migrations.add_failure_tracking_to_crawl_urls import migrate_add_failure_tracking
        from migrations.cleanup_duplicate_mappings import migrate_cleanup_duplicates
        from migrations.create_crawl_urls_table import migrate_create_crawl_urls_table
        from migrations.migrate_crawl_mode import migrate_crawl_mode

        migrate_user_roles()
        migrate_add_crawl_timestamp()
        migrate_add_failure_tracking()
        migrate_cleanup_duplicates()
        migrate_create_crawl_urls_table()
        migrate_crawl_mode()

        # Run RBAC migration
        from migrations.add_rbac_system import run_migration as rbac_migration
        try:
            rbac_migration()
        except Exception as e:
            print(f"RBAC migration completed with note: {e}")

        admin = User.query.filter_by(username='admin').first()
        print("Admin user found:", admin)
        if not admin:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@personamap.local',
                role='admin',
                is_super_admin=True  # Make default admin a super admin
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Admin user added to session.")
        else:
            # Ensure existing admin is super admin
            if not admin.is_super_admin:
                admin.is_super_admin = True
                print("Upgraded existing admin to super admin.")
        
        db.session.commit()
        print("Database initialized successfully!")

@app.cli.command()
def migrate_rbac():
    """Run only the RBAC migration."""
    with app.app_context():
        from migrations.add_rbac_system import run_migration
        run_migration()

@app.cli.command()
def create_super_admin():
    """Create a new super admin user."""
    username = input("Username: ")
    email = input("Email: ")
    password = input("Password: ")
    
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            return
        
        user = User(
            username=username,
            email=email,
            role='admin',
            is_super_admin=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Super admin user '{username}' created successfully!")

@app.cli.command()
def create_organisation():
    """Create a new organisation."""
    org_name = input("Organisation name: ")
    description = input("Description (optional): ")
    
    with app.app_context():
        existing_org = Organisation.query.filter_by(name=org_name).first()
        if existing_org:
            print(f"Organisation '{org_name}' already exists.")
            return
        
        org = Organisation(
            name=org_name,
            description=description,
            is_active=True
        )
        db.session.add(org)
        db.session.commit()
        print(f"Organisation '{org_name}' created successfully! ID: {org.id}")

@app.cli.command()
def create_website():
    """Create a new website."""
    website_name = input("Website name: ")
    domain = input("Domain: ")
    description = input("Description (optional): ")
    
    with app.app_context():
        existing_website = Website.query.filter_by(domain=domain).first()
        if existing_website:
            print(f"Website with domain '{domain}' already exists.")
            return
        
        website = Website(
            name=website_name,
            domain=domain,
            description=description,
            is_active=True
        )
        db.session.add(website)
        db.session.commit()
        print(f"Website '{website_name}' created successfully! ID: {website.id}")

@app.cli.command()
def add_user_to_org():
    """Add a user to an organisation."""
    username = input("Username: ")
    org_id = int(input("Organisation ID: "))
    role = input("Role (website_viewer/website_manager/org_admin) [website_viewer]: ") or 'website_viewer'
    
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found.")
            return
        
        org = Organisation.query.get(org_id)
        if not org:
            print(f"Organisation with ID {org_id} not found.")
            return
        
        org.add_user(user.id, role)
        print(f"User '{username}' added to organisation '{org.name}' with role '{role}'.")

@app.cli.command()
def list_users():
    """List all users with their roles."""
    with app.app_context():
        users = User.query.all()
        print("\nUsers and their roles:")
        print("-" * 80)
        for user in users:
            super_admin = " (SUPER ADMIN)" if user.is_super_admin else ""
            print(f"ID: {user.id:3d} | {user.username:20s} | {user.email:30s} | Legacy: {user.role}{super_admin}")
            
            # Show organisation roles
            for org_role in user.organisation_roles:
                org_name = org_role.organisation.name
                print(f"     └─ Org: {org_name:25s} | Role: {org_role.role}")
            
            # Show website roles
            for website_role in user.website_roles:
                website_name = website_role.website.name
                print(f"     └─ Website: {website_name:20s} | Role: {website_role.role}")
            
            print()

if __name__ == '__main__':
    import sys
    # Only start the server if no CLI command is given
    if len(sys.argv) == 1:
        os.environ.setdefault('FLASK_ENV', 'development')
        os.environ.setdefault('FLASK_DEBUG', '1')
        print("Starting PersonaMap Application...")
        print("Access the application at: http://localhost:5002")
        print("Default admin credentials: admin / admin123")
        app.run(host='0.0.0.0', port=5002, debug=True)

