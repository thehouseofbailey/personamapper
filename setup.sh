#!/bin/bash

# PersonaMap Setup Script
# This script helps users set up PersonaMap with minimal effort

echo "🚀 PersonaMap Setup Script"
echo "=========================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Set up database
echo "🗄️  Setting up database..."
python -c "
import sqlite3
from app import create_app, db
from app.models import Organisation, Website, OrganisationWebsite, User

# Add missing columns
conn = sqlite3.connect('instance/personamap.db')
cursor = conn.cursor()

# Check and add columns
cursor.execute('PRAGMA table_info(users)')
columns = [row[1] for row in cursor.fetchall()]

if 'is_super_admin' not in columns:
    cursor.execute('ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT 0')
    print('Added is_super_admin column to users')

cursor.execute('PRAGMA table_info(crawl_jobs)')
crawl_cols = [row[1] for row in cursor.fetchall()]
if 'website_id' not in crawl_cols:
    cursor.execute('ALTER TABLE crawl_jobs ADD COLUMN website_id INTEGER')
    print('Added website_id column to crawl_jobs')

cursor.execute('PRAGMA table_info(personas)')
persona_cols = [row[1] for row in cursor.fetchall()]
if 'website_id' not in persona_cols:
    cursor.execute('ALTER TABLE personas ADD COLUMN website_id INTEGER')
    print('Added website_id column to personas')

conn.commit()
conn.close()

# Create tables and default data
app = create_app()
with app.app_context():
    db.create_all()
    
    # Create default organisation and website
    if not Organisation.query.filter_by(name='Default Organisation').first():
        default_org = Organisation(
            name='Default Organisation',
            description='Default organisation for existing data',
            is_active=True
        )
        db.session.add(default_org)
        print('Created default organisation')
    
    if not Website.query.filter_by(name='Default Website').first():
        default_website = Website(
            name='Default Website', 
            domain='legacy.local',
            description='Default website for existing data',
            is_active=True
        )
        db.session.add(default_website)
        print('Created default website')
    
    db.session.commit()
    
    # Link them
    default_org = Organisation.query.filter_by(name='Default Organisation').first()
    default_website = Website.query.filter_by(name='Default Website').first()
    
    if not OrganisationWebsite.query.filter_by(
        organisation_id=default_org.id,
        website_id=default_website.id
    ).first():
        org_website = OrganisationWebsite(
            organisation_id=default_org.id,
            website_id=default_website.id
        )
        db.session.add(org_website)
        db.session.commit()
        print('Linked default organisation to default website')

print('Database setup completed!')
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the application:"
echo "  source .venv/bin/activate"
echo "  python run.py"
echo ""
echo "The app will be available at: http://localhost:5002"
echo "Default admin credentials: admin / admin123"
echo ""
echo "📚 Documentation:"
echo "  - API Documentation: API_DOCUMENTATION.md"
echo "  - RBAC Guide: RBAC_GUIDE.md" 
echo "  - README: README.md"
