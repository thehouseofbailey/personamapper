# This file contains the WSGI configuration required to serve up your
# web application at http://<yourusername>.pythonanywhere.com/

import sys
import os

# Add your project directory to the sys.path
# Replace 'yourusername' with your actual PythonAnywhere username
project_home = '/home/yourusername/personamapper'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import your Flask application
from run import app as application

if __name__ == "__main__":
    application.run()