import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///personamap.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
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
