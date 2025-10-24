#!/usr/bin/env python3
"""
Database initialization script for PythonAnywhere MySQL
Run this script once after uploading your code to PythonAnywhere
"""

import os
import sys
from dotenv import load_dotenv

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models.user import User
from app.models.organisation import Organisation

def init_database():
    """Initialize the database with tables and default data"""
    print("Initializing PersonaMap database...")
    
    app = create_app()
    
    with app.app_context():
        print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Check if admin user already exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Creating admin user...")
                admin_user = User(
                    username='admin',
                    email='admin@personamap.com',
                    role='super_admin',
                    is_super_admin=True,
                    is_active=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✓ Admin user created (username: admin, password: admin123)")
            else:
                print("✓ Admin user already exists")
            
            # Check if default organisation exists
            default_org = Organisation.query.filter_by(name='Default Organisation').first()
            if not default_org:
                print("Creating default organisation...")
                default_org = Organisation(
                    name='Default Organisation',
                    description='Default organisation for PersonaMap'
                )
                db.session.add(default_org)
                db.session.commit()
                
                # Add admin to the organisation
                from app.models.user_organisation_role import UserOrganisationRole
                user_org_role = UserOrganisationRole(
                    user_id=admin_user.id,
                    organisation_id=default_org.id,
                    role='org_admin'
                )
                db.session.add(user_org_role)
                db.session.commit()
                print("✓ Default organisation created and admin user added")
            else:
                print("✓ Default organisation already exists")
            
            print("\n" + "="*50)
            print("🎉 Database initialization complete!")
            print("="*50)
            print("\nYou can now access PersonaMap at your PythonAnywhere URL")
            print("Default admin credentials:")
            print("  Username: admin")
            print("  Password: admin123")
            print("\n" + "="*50)
            
        except Exception as e:
            print(f"❌ Error during database initialization: {e}")
            print("Please check your database configuration and try again.")
            sys.exit(1)

if __name__ == '__main__':
    init_database()