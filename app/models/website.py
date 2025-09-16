from datetime import datetime
from app import db

class Website(db.Model):
    __tablename__ = 'websites'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(500), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organisation_websites = db.relationship('OrganisationWebsite', back_populates='website', cascade='all, delete-orphan')
    user_website_roles = db.relationship('UserWebsiteRole', back_populates='website', cascade='all, delete-orphan')
    crawl_jobs = db.relationship('CrawlJob', back_populates='website', cascade='all, delete-orphan')
    personas = db.relationship('Persona', back_populates='website', cascade='all, delete-orphan')
    
    def get_organisations(self):
        """Get all organisations that have access to this website."""
        from app.models.organisation import Organisation, OrganisationWebsite
        return Organisation.query.join(OrganisationWebsite).filter(
            OrganisationWebsite.website_id == self.id
        ).all()
    
    def get_users(self):
        """Get all users who have access to this website."""
        from app.models.user import User
        from app.models.user_website_role import UserWebsiteRole
        return User.query.join(UserWebsiteRole).filter(
            UserWebsiteRole.website_id == self.id
        ).all()
    
    def get_managers(self):
        """Get all website managers."""
        from app.models.user import User
        from app.models.user_website_role import UserWebsiteRole
        return User.query.join(UserWebsiteRole).filter(
            UserWebsiteRole.website_id == self.id,
            UserWebsiteRole.role.in_(['website_manager', 'org_admin'])
        ).all()
    
    def add_organisation(self, organisation_id):
        """Add an organisation to this website."""
        from app.models.organisation import OrganisationWebsite
        
        existing = OrganisationWebsite.query.filter_by(
            organisation_id=organisation_id,
            website_id=self.id
        ).first()
        
        if not existing:
            org_website = OrganisationWebsite(
                organisation_id=organisation_id,
                website_id=self.id
            )
            db.session.add(org_website)
            db.session.commit()
    
    def remove_organisation(self, organisation_id):
        """Remove an organisation from this website."""
        from app.models.organisation import OrganisationWebsite
        from app.models.user_website_role import UserWebsiteRole
        from app.models.user import User
        
        org_website = OrganisationWebsite.query.filter_by(
            organisation_id=organisation_id,
            website_id=self.id
        ).first()
        
        if org_website:
            # Remove all website roles for users from this organisation
            from app.models.user_organisation_role import UserOrganisationRole
            org_users = User.query.join(UserOrganisationRole).filter(
                UserOrganisationRole.organisation_id == organisation_id
            ).all()
            
            for user in org_users:
                website_role = UserWebsiteRole.query.filter_by(
                    user_id=user.id,
                    website_id=self.id
                ).first()
                if website_role:
                    db.session.delete(website_role)
            
            db.session.delete(org_website)
            db.session.commit()
    
    def add_user(self, user_id, role='website_viewer'):
        """Add a user to this website with specified role."""
        from app.models.user_website_role import UserWebsiteRole
        
        existing_role = UserWebsiteRole.query.filter_by(
            user_id=user_id,
            website_id=self.id
        ).first()
        
        if existing_role:
            existing_role.role = role
            existing_role.updated_at = datetime.utcnow()
        else:
            user_role = UserWebsiteRole(
                user_id=user_id,
                website_id=self.id,
                role=role
            )
            db.session.add(user_role)
        
        db.session.commit()
    
    def remove_user(self, user_id):
        """Remove a user from this website."""
        from app.models.user_website_role import UserWebsiteRole
        
        user_role = UserWebsiteRole.query.filter_by(
            user_id=user_id,
            website_id=self.id
        ).first()
        
        if user_role:
            db.session.delete(user_role)
            db.session.commit()
    
    def get_crawl_jobs(self):
        """Get all crawl jobs for this website."""
        from app.models.crawl_job import CrawlJob
        return CrawlJob.query.filter_by(website_id=self.id).all()
    
    def get_personas(self):
        """Get all personas for this website."""
        from app.models.persona import Persona
        return Persona.query.filter_by(website_id=self.id, is_active=True).all()
    
    def get_content_mappings(self):
        """Get all content mappings for this website."""
        from app.models.content_mapping import ContentMapping
        from app.models.crawled_page import CrawledPage
        from app.models.crawl_job import CrawlJob
        
        return ContentMapping.query.join(CrawledPage).join(CrawlJob).filter(
            CrawlJob.website_id == self.id,
            ContentMapping.is_active == True
        ).all()
    
    def to_dict(self):
        """Convert website to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'organisation_count': len(self.get_organisations()),
            'user_count': len(self.get_users()),
            'crawl_job_count': len(self.get_crawl_jobs()),
            'persona_count': len(self.get_personas())
        }
    
    def __repr__(self):
        return f'<Website {self.name} ({self.domain})>'


# Avoid circular imports by using string references in relationships
