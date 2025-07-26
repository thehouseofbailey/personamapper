from datetime import datetime
from app import db

class ContentMapping(db.Model):
    __tablename__ = 'content_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('crawled_pages.id'), nullable=False)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    mapping_reason = db.Column(db.Text)  # Explanation of why this mapping was made
    mapping_method = db.Column(db.String(50), default='keyword', nullable=False)  # keyword, ai, manual
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)  # Manual verification
    crawl_timestamp = db.Column(db.DateTime, nullable=True)  # When this mapping was created during crawling
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    page = db.relationship('CrawledPage', lazy=True, overlaps="content_mappings")
    
    # Composite index for efficient queries
    __table_args__ = (
        db.Index('idx_page_persona', 'page_id', 'persona_id'),
        db.Index('idx_confidence_active', 'confidence_score', 'is_active'),
    )
    
    def get_confidence_level(self):
        """Get a human-readable confidence level."""
        if self.confidence_score >= 0.9:
            return 'Very High'
        elif self.confidence_score >= 0.7:
            return 'High'
        elif self.confidence_score >= 0.5:
            return 'Medium'
        elif self.confidence_score >= 0.3:
            return 'Low'
        else:
            return 'Very Low'
    
    def get_confidence_color(self):
        """Get a color class for UI display based on confidence."""
        if self.confidence_score >= 0.8:
            return 'success'
        elif self.confidence_score >= 0.6:
            return 'warning'
        else:
            return 'danger'
    
    def verify_mapping(self, verified=True):
        """Mark this mapping as manually verified."""
        self.is_verified = verified
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate this mapping."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_confidence(self, new_score, reason=None):
        """Update the confidence score and reason."""
        self.confidence_score = max(0.0, min(1.0, new_score))  # Clamp between 0 and 1
        if reason:
            self.mapping_reason = reason
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_relations=False):
        """Convert content mapping to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'page_id': self.page_id,
            'persona_id': self.persona_id,
            'confidence_score': round(self.confidence_score, 3),
            'confidence_level': self.get_confidence_level(),
            'confidence_color': self.get_confidence_color(),
            'mapping_reason': self.mapping_reason,
            'mapping_method': self.mapping_method,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_relations:
            data['page_url'] = self.crawled_page.url if self.crawled_page else None
            data['page_title'] = self.crawled_page.title if self.crawled_page else None
            data['persona_title'] = self.persona.title if self.persona else None
        
        return data
    
    @staticmethod
    def get_top_mappings_for_persona(persona_id, limit=10):
        """Get the top content mappings for a specific persona."""
        return ContentMapping.query.filter(
            db.and_(
                ContentMapping.persona_id == persona_id,
                ContentMapping.is_active == True
            )
        ).order_by(ContentMapping.confidence_score.desc()).limit(limit).all()
    
    @staticmethod
    def get_mappings_by_confidence_range(min_confidence, max_confidence=1.0):
        """Get mappings within a specific confidence range."""
        return ContentMapping.query.filter(
            db.and_(
                ContentMapping.confidence_score >= min_confidence,
                ContentMapping.confidence_score <= max_confidence,
                ContentMapping.is_active == True
            )
        ).order_by(ContentMapping.confidence_score.desc()).all()
    
    def __repr__(self):
        return f'<ContentMapping Page:{self.page_id} -> Persona:{self.persona_id} ({self.confidence_score:.2f})>'
