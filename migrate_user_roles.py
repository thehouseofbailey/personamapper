#!/usr/bin/env python3
"""
Migration script to add role-based user management columns to the users table.
"""

from app import create_app, db
from app.models import User
from sqlalchemy import text

def migrate_user_roles():
    """Add new columns for role-based user management."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Add missing columns
            if 'last_login' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE users ADD COLUMN last_login DATETIME'))
                    conn.commit()
                print("✅ Added last_login column")
            
            if 'password_reset_token' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(100)'))
                    conn.commit()
                print("✅ Added password_reset_token column")
            
            if 'password_reset_expires' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE users ADD COLUMN password_reset_expires DATETIME'))
                    conn.commit()
                print("✅ Added password_reset_expires column")
            
            # Update existing users to have proper roles
            # Check if admin user exists and update role
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                admin_user.role = User.ROLE_ADMIN
                db.session.commit()
                print(f"✅ Updated admin user role to: {admin_user.role}")
            
            # Update any users with 'user' role to 'viewer'
            users_with_old_role = User.query.filter_by(role='user').all()
            for user in users_with_old_role:
                user.role = User.ROLE_VIEWER
                print(f"✅ Updated user {user.username} role from 'user' to 'viewer'")
            
            if users_with_old_role:
                db.session.commit()
            
            print("\n📋 Current user roles:")
            for user in User.query.all():
                print(f"  - {user.username}: {user.get_role_display()} ({user.role})")
            
            print("\n🎉 User role migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_user_roles()
