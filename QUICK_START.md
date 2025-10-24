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

## 🌐 PythonAnywhere Deployment

### Requirements
- PythonAnywhere account (free tier available)
- MySQL database (included with PythonAnywhere)

### Deployment Steps

1. **Prepare your code:**
   ```bash
   # Create deployment zip (exclude .venv, __pycache__, instance)
   zip -r personamap-deploy.zip . -x ".venv/*" "__pycache__/*" "*.pyc" "instance/*" ".git/*"
   ```

2. **Upload to PythonAnywhere:**
   - Go to Files tab in PythonAnywhere dashboard
   - Upload `personamap-deploy.zip`
   - Extract to `/home/yourusername/personamapper`

3. **Set up MySQL database:**
   - Go to Databases tab in PythonAnywhere dashboard
   - Create new MySQL database named `yourusername$personamap`
   - Note your MySQL password

4. **Configure environment:**
   ```bash
   # In PythonAnywhere Bash console
   cd ~/personamapper
   
   # Copy and edit environment file
   cp .env.pythonanywhere .env
   
   # Edit .env with your actual details:
   # MYSQL_HOST=yourusername.mysql.pythonanywhere-services.com
   # MYSQL_USER=yourusername  
   # MYSQL_PASSWORD=your_actual_mysql_password
   # MYSQL_DB=yourusername$personamap
   ```

5. **Install dependencies:**
   ```bash
   # In PythonAnywhere Bash console
   cd ~/personamapper
   pip3.10 install --user -r requirements-pythonanywhere.txt
   ```

6. **Initialize database:**
   ```bash
   # In PythonAnywhere Bash console
   cd ~/personamapper
   python3.10 init_db_pythonanywhere.py
   ```

7. **Configure web app:**
   - Go to Web tab in PythonAnywhere dashboard
   - Create new web app → Manual configuration → Python 3.10
   - Set source code directory: `/home/yourusername/personamapper`
   - Set working directory: `/home/yourusername/personamapper`
   - Edit WSGI file: copy content from `wsgi_pythonanywhere.py` and update username
   - Add static file mapping: URL `/static/` → Directory `/home/yourusername/personamapper/app/static/`

8. **Reload and test:**
   - Click "Reload" button in Web tab
   - Visit `https://yourusername.pythonanywhere.com`
   - Login with admin/admin123

### Benefits of PythonAnywhere:
- ✅ **Persistent MySQL database** - Data never resets
- ✅ **Always-on hosting** - No container shutdowns
- ✅ **Free tier available** - Perfect for development/testing
- ✅ **Easy file management** - Web-based file editor
- ✅ **Automatic HTTPS** - Secure by default

## 🐳 Docker Deployment

### Local Docker
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

### Google Cloud Run
```bash
# Build and push to Artifact Registry
docker build --target production -t europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/personamap-repo/personamap:latest .
docker push europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/personamap-repo/personamap:latest

# Deploy to Cloud Run
gcloud run deploy personamap \
  --image=europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/personamap-repo/personamap:latest \
  --platform=managed \
  --region=europe-west1 \
  --allow-unauthenticated \
  --set-env-vars=FLASK_ENV=production,SECRET_KEY=your-secret-key,DATABASE_URL=sqlite:////app/instance/personamap.db

# Initialize database (one-time)
gcloud run jobs create personamap-initdb \
  --image=europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/personamap-repo/personamap:latest \
  --region=europe-west1 \
  --set-env-vars=FLASK_APP=run.py,FLASK_ENV=production,SECRET_KEY=your-secret-key,DATABASE_URL=sqlite:////app/instance/personamap.db \
  --command="flask" --args="init-db"

gcloud run jobs execute personamap-initdb --region=europe-west1
```

> **Note:** Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID.

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
