from datetime import datetime
from app import db

class CrawlJobPersona(db.Model):
    """Association table for many-to-many relationship between crawl jobs and personas."""
    __tablename__ = 'crawl_job_personas'
    
    id = db.Column(db.Integer, primary_key=True)
    crawl_job_id = db.Column(db.Integer, db.ForeignKey('crawl_jobs.id'), nullable=False)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    crawl_job = db.relationship('CrawlJob', back_populates='crawl_job_personas')
    persona = db.relationship('Persona', back_populates='crawl_job_personas')
    
    # Ensure unique crawl_job-persona pairs
    __table_args__ = (
        db.UniqueConstraint('crawl_job_id', 'persona_id', name='unique_crawl_job_persona'),
    )
    
    def __repr__(self):
        return f'<CrawlJobPersona crawl_job={self.crawl_job_id} persona={self.persona_id}>'
