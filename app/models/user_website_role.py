from datetime import datetime
from app import db

class UserWebsiteRole(db.Model):
    """User roles for specific websites."""
    __tablename__ = 'user_website_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='website_viewer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Role constants
    ROLE_WEBSITE_MANAGER = 'website_manager'
    ROLE_WEBSITE_VIEWER = 'website_viewer'
    
    # Relationships
    user = db.relationship('User', back_populates='website_roles')
    website = db.relationship('Website', back_populates='user_website_roles')
    
    # Ensure unique user-website pairs
    __table_args__ = (
        db.UniqueConstraint('user_id', 'website_id', name='unique_user_website'),
        db.Index('idx_user_website_role', 'user_id', 'website_id', 'role'),
    )
    
    @classmethod
    def get_roles(cls):
        """Get all available website roles."""
        return [
            (cls.ROLE_WEBSITE_MANAGER, 'Website Manager'),
            (cls.ROLE_WEBSITE_VIEWER, 'Website Viewer')
        ]
    
    def get_role_display(self):
        """Get the display name for the role."""
        role_map = dict(self.get_roles())
        return role_map.get(self.role, 'Unknown')
    
    def __repr__(self):
        return f'<UserWebsiteRole user={self.user_id} website={self.website_id} role={self.role}>'
