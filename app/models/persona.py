from datetime import datetime
from app import db

class Persona(db.Model):
    __tablename__ = 'personas'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text)  # JSON string or comma-separated keywords
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    content_mappings = db.relationship('ContentMapping', backref='persona', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_keywords_list(self):
        """Return keywords as a list."""
        if not self.keywords:
            return []
        return [keyword.strip() for keyword in self.keywords.split(',') if keyword.strip()]
    
    def set_keywords_from_list(self, keywords_list):
        """Set keywords from a list."""
        self.keywords = ', '.join(keywords_list) if keywords_list else ''
    
    def get_mapping_count(self):
        """Get the number of content mappings for this persona."""
        return self.content_mappings.count()
    
    def get_high_confidence_mappings(self, threshold=0.8):
        """Get content mappings with high confidence scores."""
        return self.content_mappings.filter(
            db.and_(
                ContentMapping.confidence_score >= threshold,
                ContentMapping.is_active == True
            )
        ).all()
    
    def to_dict(self):
        """Convert persona to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'keywords': self.get_keywords_list(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'mapping_count': self.get_mapping_count()
        }
    
    def __repr__(self):
        return f'<Persona {self.title}>'

# Import here to avoid circular imports
from .content_mapping import ContentMapping
