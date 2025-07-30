#!/usr/bin/env python3
"""
PersonaMap Application Entry Point

This is the main entry point for the PersonaMap application.
Run this file to start the Flask development server.
"""

import os
from app import create_app, db
from app.models import User, Persona, CrawlJob, CrawledPage, ContentMapping

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
        'ContentMapping': ContentMapping
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

        admin = User.query.filter_by(username='admin').first()
        print("Admin user found:", admin)
        if not admin:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@personamap.local',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Admin user added to session.")
        db.session.commit()
        print("Database initialized successfully!")

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

