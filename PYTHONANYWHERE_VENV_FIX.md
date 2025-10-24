# PythonAnywhere Virtual Environment Setup Fix

## 🔍 **The Issue**
Your virtual environment isn't set up correctly on PythonAnywhere. Let's fix this step by step.

## 🛠️ **Quick Fix Steps**

### Step 1: Check Your Current Directory Structure
```bash
cd ~/personamapper
ls -la
```
Look for any existing virtual environment directories (might be named `.venv`, `venv`, `env`, or similar).

### Step 2: Create Virtual Environment (If Missing)
```bash
cd ~/personamapper
python3.10 -m venv venv
```

### Step 3: Activate and Install Dependencies
```bash
cd ~/personamapper
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-pythonanywhere.txt
```

### Step 4: Test the Installation
```bash
# While still in activated venv
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    result = db.engine.execute('SELECT 1').scalar()
    print('✅ Database connection successful')
"
```

## 🔄 **Alternative: Use System Python (Quick Fix)**
If virtual environment creation fails, you can use system Python temporarily:

```bash
cd ~/personamapper
pip3.10 install --user -r requirements-pythonanywhere.txt
```

Then test:
```bash
python3.10 -c "
from app import create_app, db
app = create_app()
with app.app_context():
    result = db.engine.execute('SELECT 1').scalar()
    print('✅ Database connection successful')
"
```

## 🎯 **After Installing Dependencies**

### Update Web App Configuration
1. Go to PythonAnywhere **Web** tab
2. If using virtual environment:
   - Set **Virtualenv** path to: `/home/yourusername/personamapper/venv`
3. If using system Python:
   - Leave **Virtualenv** path empty
4. Click **Reload** button

## 📋 **Complete Setup Commands (Copy-Paste Ready)**

```bash
# Navigate to directory
cd ~/personamapper

# Check what's there
ls -la

# Create virtual environment (if needed)
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements-pythonanywhere.txt

# Test database connection
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    try:
        result = db.engine.execute('SELECT 1').scalar()
        print('✅ Database connection successful')
        # Check if we have users
        from app.models.user import User
        user_count = User.query.count()
        print(f'✅ Found {user_count} users in database')
    except Exception as e:
        print(f'❌ Database error: {e}')
"
```

## 🚨 **If Virtual Environment Creation Fails**

Some PythonAnywhere accounts have restrictions. Use system Python instead:

```bash
cd ~/personamapper
pip3.10 install --user -r requirements-pythonanywhere.txt

# Test with system Python
python3.10 -c "
import sys
print(f'Python version: {sys.version}')
try:
    from app import create_app
    print('✅ App imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
"
```

## 🎯 **Expected Output After Success**

You should see:
```
✅ Database connection successful
✅ Found X users in database
```

Then reload your web app and test at `https://yourusername.pythonanywhere.com`