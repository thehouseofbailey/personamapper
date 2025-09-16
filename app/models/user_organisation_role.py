from datetime import datetime
from app import db

class UserOrganisationRole(db.Model):
    """User roles within organisations."""
    __tablename__ = 'user_organisation_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='website_viewer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Role constants
    ROLE_ORG_ADMIN = 'org_admin'
    ROLE_WEBSITE_MANAGER = 'website_manager'
    ROLE_WEBSITE_VIEWER = 'website_viewer'
    
    # Relationships
    user = db.relationship('User', back_populates='organisation_roles')
    organisation = db.relationship('Organisation', back_populates='user_roles')
    
    # Ensure unique user-organisation pairs
    __table_args__ = (
        db.UniqueConstraint('user_id', 'organisation_id', name='unique_user_org'),
        db.Index('idx_user_org_role', 'user_id', 'organisation_id', 'role'),
    )
    
    @classmethod
    def get_roles(cls):
        """Get all available organisation roles."""
        return [
            (cls.ROLE_ORG_ADMIN, 'Organisation Admin'),
            (cls.ROLE_WEBSITE_MANAGER, 'Website Manager'),
            (cls.ROLE_WEBSITE_VIEWER, 'Website Viewer')
        ]
    
    def get_role_display(self):
        """Get the display name for the role."""
        role_map = dict(self.get_roles())
        return role_map.get(self.role, 'Unknown')
    
    def __repr__(self):
        return f'<UserOrganisationRole user={self.user_id} org={self.organisation_id} role={self.role}>'
