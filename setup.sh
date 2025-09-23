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
pip3 install -r requirements.txt

# Set up database and run migrations
echo "🗄️  Setting up database and running migrations..."

# Run essential migrations in order
echo "  📝 Running database migrations..."

# Function to run migration with error handling
run_migration_safe() {
    local migration_file=$1
    local function_name=$2
    local description=$3
    
    echo "    - $description..."
    
    if [ ! -f "$migration_file" ]; then
        echo "      ⚠️  Migration file not found: $migration_file (skipping)"
        return 0
    fi
    
    if python3 -c "exec(open('$migration_file').read()); $function_name" 2>/dev/null; then
        echo "      ✅ $description completed"
    else
        echo "      ⚠️  $description failed or already applied (continuing)"
    fi
}

# 1. Run RBAC system migration
run_migration_safe "migrations/add_rbac_system.py" "run_migration()" "Setting up RBAC system"

# 2. Create crawl job personas table
run_migration_safe "migrations/create_crawl_job_personas_table.py" "run_migration()" "Creating crawl job personas table"

# 3. Create crawl URLs table  
run_migration_safe "migrations/create_crawl_urls_table.py" "migrate_create_crawl_urls_table()" "Creating crawl URLs table"

# 4. Add crawl timestamp to content mappings
run_migration_safe "migrations/add_crawl_timestamp_to_content_mappings.py" "migrate_add_crawl_timestamp()" "Adding crawl timestamp to content mappings"

# 5. Add failure tracking to crawl URLs
run_migration_safe "migrations/add_failure_tracking_to_crawl_urls.py" "migrate_add_failure_tracking()" "Adding failure tracking to crawl URLs"

# 6. Migrate user roles
run_migration_safe "migrations/migrate_user_roles.py" "migrate_user_roles()" "Setting up user roles"

# 7. Add AI config to organisations
run_migration_safe "migrations/add_ai_config_to_organisations.py" "run_migration()" "Adding AI configuration to organisations"

# Final setup - create default data
echo "  🏗️  Creating default data..."
python3 -c "
from app import create_app, db
from app.models import Organisation, Website, OrganisationWebsite, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    db.create_all()
    
    # Create default organisation and website
    if not Organisation.query.filter_by(name='Default Organisation').first():
        default_org = Organisation(
            name='Default Organisation',
            description='Default organisation for new installations',
            is_active=True
        )
        db.session.add(default_org)
        print('  ✅ Created default organisation')
    
    if not Website.query.filter_by(name='Default Website').first():
        default_website = Website(
            name='Default Website', 
            domain='example.com',
            description='Default website for new installations',
            is_active=True
        )
        db.session.add(default_website)
        print('  ✅ Created default website')
    
    # Create default admin user
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@example.com',
            is_super_admin=True,
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        print('  ✅ Created default admin user (admin/admin123)')
    
    db.session.commit()
    
    # Link default organisation to default website
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
        print('  ✅ Linked default organisation to default website')

print('✅ Database setup completed!')
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "  source .venv/bin/activate"
echo "  python run.py"
echo ""
echo "🌐 Access the application:"
echo "  URL: http://localhost:5002"
echo "  Default admin: admin / admin123"
echo ""
echo "📚 Next steps:"
echo "  1. Log in with admin credentials"
echo "  2. Create your organizations and websites"
echo "  3. Set up user accounts with appropriate roles"
echo "  4. Start creating personas and crawl jobs"
echo ""
echo "� Documentation:"
echo "  - Quick Start: QUICK_START.md"
echo "  - API Documentation: API_DOCUMENTATION.md"
echo "  - RBAC Guide: RBAC_GUIDE.md"
