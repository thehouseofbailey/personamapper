from datetime import datetime
from app import db

class CrawlJob(db.Model):
    __tablename__ = 'crawl_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    include_patterns = db.Column(db.Text)  # JSON string or newline-separated patterns
    exclude_patterns = db.Column(db.Text)  # JSON string or newline-separated patterns
    max_pages = db.Column(db.Integer, default=100, nullable=False)
    crawl_mode = db.Column(db.String(20), default='incremental', nullable=False)  # incremental, overwrite
    schedule = db.Column(db.String(100))  # Cron-like schedule string
    status = db.Column(db.String(20), default='inactive', nullable=False)  # inactive, active, running, completed, failed
    last_run_at = db.Column(db.DateTime)
    next_run_at = db.Column(db.DateTime)
    pages_crawled = db.Column(db.Integer, default=0, nullable=False)
    pages_mapped = db.Column(db.Integer, default=0, nullable=False)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    crawled_pages = db.relationship('CrawledPage', backref='crawl_job', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_include_patterns_list(self):
        """Return include patterns as a list."""
        if not self.include_patterns:
            return []
        return [pattern.strip() for pattern in self.include_patterns.split('\n') if pattern.strip()]
    
    def set_include_patterns_from_list(self, patterns_list):
        """Set include patterns from a list."""
        self.include_patterns = '\n'.join(patterns_list) if patterns_list else ''
    
    def get_exclude_patterns_list(self):
        """Return exclude patterns as a list."""
        if not self.exclude_patterns:
            return []
        return [pattern.strip() for pattern in self.exclude_patterns.split('\n') if pattern.strip()]
    
    def set_exclude_patterns_from_list(self, patterns_list):
        """Set exclude patterns from a list."""
        self.exclude_patterns = '\n'.join(patterns_list) if patterns_list else ''
    
    def is_running(self):
        """Check if the crawl job is currently running."""
        return self.status == 'running'
    
    def is_active(self):
        """Check if the crawl job is active (scheduled)."""
        return self.status == 'active'
    
    def get_success_rate(self):
        """Calculate the success rate of crawled pages."""
        if self.pages_crawled == 0:
            return 0
        return (self.pages_mapped / self.pages_crawled) * 100
    
    def update_status(self, status, error_message=None):
        """Update the job status and error message."""
        self.status = status
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
        if status == 'running':
            self.last_run_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert crawl job to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'base_url': self.base_url,
            'include_patterns': self.get_include_patterns_list(),
            'exclude_patterns': self.get_exclude_patterns_list(),
            'max_pages': self.max_pages,
            'schedule': self.schedule,
            'status': self.status,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'pages_crawled': self.pages_crawled,
            'pages_mapped': self.pages_mapped,
            'success_rate': self.get_success_rate(),
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<CrawlJob {self.name}>'

# Import here to avoid circular imports
from .crawled_page import CrawledPage
