# PersonaMap - Quick Setup Guide

PersonaMap is a Flask web application with role-based access control (RBAC) for managing website personas, crawling, and content analysis.

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd personamapper

# Run the setup script (handles everything automatically)
./setup.sh
```

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Set up the database with all necessary tables
- Run all essential migrations (RBAC, crawl jobs, etc.)
- Create default organisation, website, and admin user
- Configure the system for immediate use

### Option 2: Manual Setup
```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up database (run each migration)
python migrations/add_rbac_system.py
python migrations/create_crawl_job_personas_table.py
python migrations/create_crawl_urls_table.py
python migrations/add_crawl_timestamp_to_content_mappings.py
python migrations/add_failure_tracking_to_crawl_urls.py
python migrations/migrate_user_roles.py
python migrations/add_ai_config_to_organisations.py

# 4. Run the application
python run.py
```

## 📋 System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space

## 🌐 Accessing the Application

Once started, the application will be available at:
- **URL**: http://localhost:5002
- **Default Admin**: `admin` / `admin123`

## 🔑 RBAC System

PersonaMap includes a comprehensive role-based access control system:

### User Roles
- **Super Admin**: Global access to everything
- **Organisation Admin**: Full control within their organisation(s)  
- **Website Manager**: Manage specific websites
- **Website Viewer**: Read-only access to assigned websites

### Key Features
- Multi-organisation support
- Website-based access control
- Granular permissions for crawl jobs and personas
- Backward compatibility with existing data

## 📚 Documentation

- **RBAC Guide**: `RBAC_GUIDE.md` - Complete RBAC system documentation
- **API Documentation**: `API_DOCUMENTATION.md` - REST API reference
- **Deployment Guide**: `DEPLOYMENT.md` - Production deployment instructions

## 🛠️ Development

### Project Structure
```
personamapper/
├── app/                    # Flask application
│   ├── models/            # Database models
│   ├── routes/            # Route handlers
│   ├── services/          # Business logic
│   ├── templates/         # HTML templates
│   └── auth/             # Authentication & permissions
├── migrations/            # Database migrations
├── instance/             # Database files
└── setup.sh             # Automated setup script
```

### Common Commands
```bash
# Start development server
source .venv/bin/activate
python run.py

# Access Python shell with app context
source .venv/bin/activate
python -c "from app import create_app; app = create_app(); app.app_context().push()"
```

## 🔧 Troubleshooting

### Database Issues
If you encounter database errors:
```bash
# Re-run database setup
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
"
```

### Permission Issues
- Ensure you're logged in with appropriate user role
- Check if user has access to the specific organisation/website
- Super admin users can access everything

### Port Conflicts
If port 5002 is in use, modify `run.py`:
```python
app.run(host='0.0.0.0', port=5003, debug=True)  # Change port
```

## 🤝 Support

For issues and questions:
1. Check the documentation files in this repository
2. Review the troubleshooting section above
3. Check application logs for specific error messages

## 📄 License

[Add your license information here]
