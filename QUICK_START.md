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

### 3. Initialize the Database (One-Time Step)
```bash
export FLASK_APP=run.py
flask init-db
```

> **Note:** Only run `flask init-db` once to set up the database. Do **not** call `db.create_all()` on every app start.

### 4. Run the application
python run.py

Or with Docker:
```bash
# Build the image
docker build --target production -t personamap:latest .

# Initialize the database (one-time)
docker run --rm \
    -e FLASK_APP=run.py \
    -e FLASK_ENV=production \
    -e DATABASE_URL=sqlite:////app/instance/personamap.db \
    -e SECRET_KEY=your-secret-key \
    personamap:latest \
    flask init-db

# Start the app
docker run -d --name personamap-test \
    -e FLASK_ENV=production \
    -e DATABASE_URL=sqlite:////app/instance/personamap.db \
    -e SECRET_KEY=your-secret-key \
    -p 8080:8080 \
    personamap:latest
```
```

## 📋 System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space

## 🌐 Accessing the Application

Once started, the application will be available at:
- **URL**: http://localhost:8080
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
If port 8080 is in use, modify `run.py`:
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
