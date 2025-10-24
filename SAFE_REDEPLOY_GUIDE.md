# Safe Redeployment Guide - Preserve Your Data

## 🛡️ Data-Safe Redeployment for PythonAnywhere

Your MySQL database data will be **automatically preserved** during redeployment because the database lives separately from your application code.

### Pre-Deployment Checklist

1. **Verify you're using MySQL** (not SQLite):
   ```bash
   # In PythonAnywhere console, check your current .env
   cat ~/.env | grep DATABASE_URL
   # Should show: mysql+pymysql://...
   ```

2. **Optional: Create backup** (extra safety):
   ```bash
   # In PythonAnywhere console
   mysqldump -u yourusername -p -h yourusername.mysql.pythonanywhere-services.com yourusername\$personamap > backup_$(date +%Y%m%d).sql
   ```

### Safe Redeployment Steps

#### Method 1: Update Existing Installation (Recommended)
```bash
# 1. Backup current code (optional)
cd ~
cp -r personamapper personamapper_backup_$(date +%Y%m%d)

# 2. Upload and extract new optimized package
# Upload personamap-pythonanywhere-optimized.tar.gz via Files interface
tar -xzf personamap-pythonanywhere-optimized.tar.gz

# 3. Copy your existing .env file (preserves database config)
cp personamapper/.env personamap-pythonanywhere-optimized/.env

# 4. Update your installation
rm -rf personamapper_old  # Remove any old backup
mv personamapper personamapper_old  # Backup current
mv personamap-pythonanywhere-optimized personamapper  # Replace with new

# 5. Update dependencies
cd ~/personamapper
source venv/bin/activate  # Use existing venv
pip install --upgrade -r requirements-pythonanywhere.txt

# 6. Test database connection
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    result = db.engine.execute('SELECT COUNT(*) FROM user').scalar()
    print(f'✅ Database connected - {result} users found')
"

# 7. Reload web app
# Go to PythonAnywhere Web tab and click "Reload"
```

#### Method 2: Fresh Installation (If Method 1 has issues)
```bash
# 1. Save current database credentials
cd ~/personamapper
cp .env ~/.env_backup

# 2. Extract new package to different location
cd ~
tar -xzf personamap-pythonanywhere-optimized.tar.gz
cd personamap-pythonanywhere-optimized

# 3. Copy saved credentials
cp ~/.env_backup .env

# 4. Setup new environment
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements-pythonanywhere.txt

# 5. Test database connection (should show existing data)
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    result = db.engine.execute('SELECT COUNT(*) FROM user').scalar()
    print(f'✅ Database connected - {result} users found')
"

# 6. Update web app configuration
# In PythonAnywhere Web tab:
# - Update source code path to: /home/yourusername/personamap-pythonanywhere-optimized
# - Update working directory to: /home/yourusername/personamap-pythonanywhere-optimized  
# - Update virtualenv path to: /home/yourusername/personamap-pythonanywhere-optimized/venv
# - Reload web app
```

### What Gets Updated vs Preserved

#### ✅ **Preserved (Your Data is Safe)**
- All user accounts and passwords
- Organizations and their settings
- Websites and their configurations
- Personas and their mappings
- Crawl jobs and their results
- Crawled pages and content
- All user roles and permissions

#### 🔄 **Updated (Improved Code)**
- Enhanced web crawler with better MySQL handling
- Improved database connection management
- Better error handling and logging
- Optimized performance for PythonAnywhere
- Updated Flask application code

### Verification Steps After Deployment

1. **Test login** with your existing credentials
2. **Check data integrity**:
   ```bash
   # In PythonAnywhere console
   cd ~/personamapper
   source venv/bin/activate
   python -c "
   from app import create_app, db
   from app.models.user import User
   from app.models.organisation import Organisation
   from app.models.website import Website
   
   app = create_app()
   with app.app_context():
       print(f'Users: {User.query.count()}')
       print(f'Organizations: {Organisation.query.count()}')
       print(f'Websites: {Website.query.count()}')
   "
   ```

3. **Test crawler functionality** with a small test crawl
4. **Monitor logs** for any issues:
   ```bash
   tail -f ~/personamapper/crawler.log
   ```

### Emergency Recovery (If Something Goes Wrong)

If you encounter issues, you can quickly restore:

```bash
# Restore previous version
cd ~
rm -rf personamapper
mv personamapper_backup_YYYYMMDD personamapper  # Use your backup date

# Or restore from database backup
mysql -u yourusername -p -h yourusername.mysql.pythonanywhere-services.com yourusername\$personamap < backup_YYYYMMDD.sql
```

### Why Your Data is Safe

1. **Separate storage**: MySQL database runs on PythonAnywhere's database servers, not in your application directory
2. **Persistent connections**: Database credentials in `.env` file point to the same database
3. **No schema changes**: The optimized version doesn't change your database structure
4. **Code-only updates**: Redeployment only updates Python files, templates, and static assets

## 🚀 Ready to Deploy Safely?

Your data is safe with MySQL on PythonAnywhere. The optimized crawler will simply connect to your existing database and work with all your current data while providing much better performance!