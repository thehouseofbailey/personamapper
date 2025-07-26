from datetime import datetime
from app import db

class CrawlUrl(db.Model):
    """Model for storing URLs discovered from sitemaps for crawl jobs."""
    
    __tablename__ = 'crawl_urls'
    
    id = db.Column(db.Integer, primary_key=True)
    crawl_job_id = db.Column(db.Integer, db.ForeignKey('crawl_jobs.id'), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    is_crawled = db.Column(db.Boolean, default=False, nullable=False)
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow)
    crawled_at = db.Column(db.DateTime)
    priority = db.Column(db.Integer, default=0)  # For prioritizing certain URLs
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)  # Number of failed crawl attempts
    is_failed = db.Column(db.Boolean, default=False, nullable=False)  # Mark as permanently failed
    last_error = db.Column(db.Text)  # Store last error message
    
    # Relationships
    crawl_job = db.relationship('CrawlJob', backref=db.backref('crawl_urls', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_crawl_job_url', 'crawl_job_id', 'url'),
        db.Index('idx_crawl_job_crawled', 'crawl_job_id', 'is_crawled'),
    )
    
    def __repr__(self):
        return f'<CrawlUrl {self.url}>'
    
    def mark_as_crawled(self):
        """Mark this URL as crawled."""
        self.is_crawled = True
        self.crawled_at = datetime.utcnow()
        # Reset failure tracking on successful crawl
        self.failed_attempts = 0
        self.is_failed = False
        self.last_error = None
        db.session.commit()
    
    def mark_as_failed(self, error_message: str, max_attempts: int = 3):
        """Mark this URL as failed and increment failure count."""
        self.failed_attempts += 1
        self.last_error = error_message
        
        if self.failed_attempts >= max_attempts:
            self.is_failed = True
        
        db.session.commit()
    
    def reset_crawl_status(self):
        """Reset crawl status (for overwrite mode)."""
        self.is_crawled = False
        self.crawled_at = None
        self.failed_attempts = 0
        self.is_failed = False
        self.last_error = None
