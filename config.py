import os
from datetime import timedelta

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Use environment variables or fallback to default values
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration for PythonAnywhere MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'your_username')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'your_password')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'your_username$personamap')
    
    # SQLAlchemy configuration - prefer MySQL, fallback to SQLite for local development
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        # Check if we have MySQL credentials
        if MYSQL_PASSWORD != 'your_password':
            DATABASE_URL = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4'
        else:
            DATABASE_URL = 'sqlite:///instance/personamap.db'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enhanced MySQL configuration for PythonAnywhere
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,          # Test connections before use
        'pool_recycle': 300,            # Recycle connections every 5 minutes
        'pool_timeout': 30,             # Timeout for getting connection
        'pool_size': 10,                # Connection pool size
        'max_overflow': 20,             # Additional connections beyond pool_size
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 60,
            'read_timeout': 600,        # 10 minutes for long queries
            'write_timeout': 600,       # 10 minutes for long writes
            'autocommit': False,
            'init_command': "SET SESSION wait_timeout=3600",  # 1 hour session timeout
        } if 'mysql' in DATABASE_URL else {}
    }
    
    # Security settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Crawler settings
    CRAWLER_USER_AGENT = os.environ.get('CRAWLER_USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    CRAWLER_DELAY = int(os.environ.get('CRAWLER_DELAY', '1'))  # Delay between requests in seconds
    CRAWLER_MAX_PAGES_DEFAULT = int(os.environ.get('CRAWLER_MAX_PAGES_DEFAULT', '100'))
    
    # Content analysis settings
    CONTENT_MIN_LENGTH = 100  # Minimum content length to analyze
    MAPPING_CONFIDENCE_THRESHOLD = 0.6
    
    # AI Analysis settings
    AI_ENABLED = os.environ.get('AI_ENABLED', 'false').lower() == 'true'
    AI_ANALYSIS_MODE = os.environ.get('AI_ANALYSIS_MODE', 'hybrid')  # keyword, ai, hybrid, validation
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', '1000'))
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', '0.3'))
    
    # AI Cost controls
    AI_DAILY_COST_LIMIT = float(os.environ.get('AI_DAILY_COST_LIMIT', '10.0'))  # USD
    AI_MONTHLY_COST_LIMIT = float(os.environ.get('AI_MONTHLY_COST_LIMIT', '100.0'))  # USD
    
    # Local AI settings (Sentence Transformers)
    LOCAL_AI_MODEL = os.environ.get('LOCAL_AI_MODEL', 'all-MiniLM-L6-v2')
    LOCAL_AI_SIMILARITY_THRESHOLD = float(os.environ.get('LOCAL_AI_SIMILARITY_THRESHOLD', '0.5'))
    
    # AI Analysis thresholds
    AI_CONFIDENCE_THRESHOLD = float(os.environ.get('AI_CONFIDENCE_THRESHOLD', '0.3'))
    AI_CONTENT_CHUNK_SIZE = int(os.environ.get('AI_CONTENT_CHUNK_SIZE', '2000'))  # Characters
