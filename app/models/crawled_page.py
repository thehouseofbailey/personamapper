from datetime import datetime
from app import db

class CrawledPage(db.Model):
    __tablename__ = 'crawled_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1000), nullable=False, index=True)
    title = db.Column(db.String(500))
    content = db.Column(db.Text)
    raw_html = db.Column(db.Text)
    meta_description = db.Column(db.Text)
    meta_keywords = db.Column(db.Text)
    word_count = db.Column(db.Integer, default=0)
    status_code = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    crawl_job_id = db.Column(db.Integer, db.ForeignKey('crawl_jobs.id'), nullable=False)
    crawled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime)
    is_processed = db.Column(db.Boolean, default=False, nullable=False)
    processing_error = db.Column(db.Text)
    
    # Relationships
    content_mappings = db.relationship('ContentMapping', backref='crawled_page', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_content_preview(self, length=200):
        """Get a preview of the content."""
        if not self.content:
            return ""
        return self.content[:length] + "..." if len(self.content) > length else self.content
    
    def get_mapping_count(self):
        """Get the number of persona mappings for this page."""
        return self.content_mappings.count()
    
    def get_best_mapping(self):
        """Get the persona mapping with the highest confidence score."""
        return self.content_mappings.filter(
            ContentMapping.is_active == True
        ).order_by(ContentMapping.confidence_score.desc()).first()
    
    def get_all_mappings(self):
        """Get all active persona mappings for this page."""
        return self.content_mappings.filter(
            ContentMapping.is_active == True
        ).order_by(ContentMapping.confidence_score.desc()).all()
    
    def has_persona_mapping(self, persona_id):
        """Check if this page is mapped to a specific persona."""
        return self.content_mappings.filter(
            db.and_(
                ContentMapping.persona_id == persona_id,
                ContentMapping.is_active == True
            )
        ).first() is not None
    
    def mark_as_processed(self, error_message=None):
        """Mark the page as processed."""
        self.is_processed = True
        self.processed_at = datetime.utcnow()
        if error_message:
            self.processing_error = error_message
    
    def calculate_word_count(self):
        """Calculate and update the word count."""
        if self.content:
            self.word_count = len(self.content.split())
        else:
            self.word_count = 0
    
    def to_dict(self, include_content=False):
        """Convert crawled page to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'meta_description': self.meta_description,
            'word_count': self.word_count,
            'status_code': self.status_code,
            'content_type': self.content_type,
            'crawl_job_id': self.crawl_job_id,
            'crawled_at': self.crawled_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'is_processed': self.is_processed,
            'mapping_count': self.get_mapping_count(),
            'content_preview': self.get_content_preview()
        }
        
        if include_content:
            data['content'] = self.content
            data['raw_html'] = self.raw_html
            data['meta_keywords'] = self.meta_keywords
            data['processing_error'] = self.processing_error
        
        return data
    
    def __repr__(self):
        return f'<CrawledPage {self.url}>'

# Import here to avoid circular imports
from .content_mapping import ContentMapping
