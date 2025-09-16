from datetime import datetime
from app import db

class Organisation(db.Model):
    __tablename__ = 'organisations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # AI Configuration fields
    ai_enabled = db.Column(db.Boolean, default=False, nullable=False)
    ai_analysis_mode = db.Column(db.String(50), default='keyword', nullable=False)  # keyword, ai, hybrid, validation, local
    openai_api_key = db.Column(db.Text)
    openai_model = db.Column(db.String(100), default='gpt-3.5-turbo')
    openai_max_tokens = db.Column(db.Integer, default=1000)
    openai_temperature = db.Column(db.Float, default=0.3)
    ai_daily_cost_limit = db.Column(db.Float, default=10.0)
    ai_monthly_cost_limit = db.Column(db.Float, default=100.0)
    local_ai_model = db.Column(db.String(100), default='all-MiniLM-L6-v2')
    local_ai_similarity_threshold = db.Column(db.Float, default=0.5)
    ai_confidence_threshold = db.Column(db.Float, default=0.3)
    ai_content_chunk_size = db.Column(db.Integer, default=2000)
    
    # Relationships
    user_roles = db.relationship('UserOrganisationRole', back_populates='organisation', cascade='all, delete-orphan')
    organisation_websites = db.relationship('OrganisationWebsite', back_populates='organisation', cascade='all, delete-orphan')
    
    def get_users(self):
        """Get all users in this organisation."""
        from app.models.user import User
        from app.models.user_organisation_role import UserOrganisationRole
        return User.query.join(UserOrganisationRole).filter(
            UserOrganisationRole.organisation_id == self.id
        ).all()
    
    def get_websites(self):
        """Get all websites accessible to this organisation."""
        from app.models.website import Website
        return Website.query.join(OrganisationWebsite).filter(
            OrganisationWebsite.organisation_id == self.id
        ).all()
    
    def get_admins(self):
        """Get all organisation admins."""
        from app.models.user import User
        from app.models.user_organisation_role import UserOrganisationRole
        return User.query.join(UserOrganisationRole).filter(
            UserOrganisationRole.organisation_id == self.id,
            UserOrganisationRole.role == 'org_admin'
        ).all()
    
    def add_user(self, user_id, role='website_viewer'):
        """Add a user to this organisation with specified role."""
        from app.models.user_organisation_role import UserOrganisationRole
        existing_role = UserOrganisationRole.query.filter_by(
            user_id=user_id,
            organisation_id=self.id
        ).first()
        
        if existing_role:
            existing_role.role = role
            existing_role.updated_at = datetime.utcnow()
        else:
            user_role = UserOrganisationRole(
                user_id=user_id,
                organisation_id=self.id,
                role=role
            )
            db.session.add(user_role)
        
        db.session.commit()
    
    def remove_user(self, user_id):
        """Remove a user from this organisation."""
        from app.models.user_organisation_role import UserOrganisationRole
        user_role = UserOrganisationRole.query.filter_by(
            user_id=user_id,
            organisation_id=self.id
        ).first()
        
        if user_role:
            # Also remove all website roles for this user in this org
            from app.models.user_website_role import UserWebsiteRole
            from app.models.website import Website
            
            org_websites = self.get_websites()
            for website in org_websites:
                website_role = UserWebsiteRole.query.filter_by(
                    user_id=user_id,
                    website_id=website.id
                ).first()
                if website_role:
                    db.session.delete(website_role)
            
            db.session.delete(user_role)
            db.session.commit()
    
    def get_ai_config(self):
        """Get AI configuration for this organisation."""
        return {
            'ai_enabled': self.ai_enabled,
            'ai_analysis_mode': self.ai_analysis_mode,
            'openai_model': self.openai_model,
            'openai_max_tokens': self.openai_max_tokens,
            'openai_temperature': self.openai_temperature,
            'ai_daily_cost_limit': self.ai_daily_cost_limit,
            'ai_monthly_cost_limit': self.ai_monthly_cost_limit,
            'local_ai_model': self.local_ai_model,
            'local_ai_similarity_threshold': self.local_ai_similarity_threshold,
            'ai_confidence_threshold': self.ai_confidence_threshold,
            'ai_content_chunk_size': self.ai_content_chunk_size,
            'has_openai_key': bool(self.openai_api_key and self.openai_api_key.strip())
        }
    
    def update_ai_config(self, config_data):
        """Update AI configuration for this organisation."""
        ai_fields = [
            'ai_enabled', 'ai_analysis_mode', 'openai_model', 'openai_max_tokens',
            'openai_temperature', 'ai_daily_cost_limit', 'ai_monthly_cost_limit',
            'local_ai_model', 'local_ai_similarity_threshold', 'ai_confidence_threshold',
            'ai_content_chunk_size'
        ]
        
        for field in ai_fields:
            if field in config_data:
                setattr(self, field, config_data[field])
        
        # Handle API key separately (only update if provided)
        if 'openai_api_key' in config_data and config_data['openai_api_key']:
            self.openai_api_key = config_data['openai_api_key']
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert organisation to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_count': len(self.get_users()),
            'website_count': len(self.get_websites()),
            'ai_enabled': self.ai_enabled
        }
    
    def get_personas(self):
        """Get all personas for websites belonging to this organisation."""
        from app.models.persona import Persona
        websites = self.get_websites()
        website_ids = [w.id for w in websites]
        
        if not website_ids:
            return []
        
        return Persona.query.filter(
            Persona.website_id.in_(website_ids),
            Persona.is_active == True
        ).order_by(Persona.title).all()
    
    def __repr__(self):
        return f'<Organisation {self.name}>'


class OrganisationWebsite(db.Model):
    """Association table for many-to-many relationship between organisations and websites."""
    __tablename__ = 'organisation_websites'
    
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    organisation = db.relationship('Organisation', back_populates='organisation_websites')
    website = db.relationship('Website', back_populates='organisation_websites')
    
    # Ensure unique organisation-website pairs
    __table_args__ = (
        db.UniqueConstraint('organisation_id', 'website_id', name='unique_org_website'),
    )
    
    def __repr__(self):
        return f'<OrganisationWebsite org={self.organisation_id} website={self.website_id}>'


# UserOrganisationRole is defined in user_organisation_role.py to avoid circular imports
