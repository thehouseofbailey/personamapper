from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='viewer', nullable=False)  # Legacy role for backward compatibility
    is_super_admin = db.Column(db.Boolean, default=False, nullable=False)  # Global super admin flag
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    # Legacy role constants (for backward compatibility)
    ROLE_ADMIN = 'admin'
    ROLE_EDITOR = 'editor'
    ROLE_VIEWER = 'viewer'
    
    # New relationships for RBAC
    organisation_roles = db.relationship('UserOrganisationRole', back_populates='user', cascade='all, delete-orphan')
    website_roles = db.relationship('UserWebsiteRole', back_populates='user', cascade='all, delete-orphan')
    
    @classmethod
    def get_roles(cls):
        """Get all available roles."""
        return [
            (cls.ROLE_ADMIN, 'Admin'),
            (cls.ROLE_EDITOR, 'Editor'),
            (cls.ROLE_VIEWER, 'Viewer')
        ]
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    # ============================================================================
    # NEW RBAC PERMISSION METHODS
    # ============================================================================
    
    def get_organisations(self):
        """Get all organisations this user belongs to."""
        from app.models.organisation import Organisation
        from app.models.user_organisation_role import UserOrganisationRole
        return Organisation.query.join(UserOrganisationRole).filter(
            UserOrganisationRole.user_id == self.id
        ).all()
    
    def get_websites(self):
        """Get all websites this user has direct website access to."""
        from app.models.website import Website
        from app.models.user_website_role import UserWebsiteRole
        return Website.query.join(UserWebsiteRole).filter(
            UserWebsiteRole.user_id == self.id
        ).all()
    
    def get_accessible_websites(self):
        """Get all websites this user has access to (direct or via organization)."""
        if self.is_super_admin:
            from app.models.website import Website
            return Website.query.all()
        
        from app.models.website import Website
        accessible_websites = []
        
        # Get all websites
        all_websites = Website.query.all()
        
        # Check each website for access
        for website in all_websites:
            if self.has_website_access(website.id):
                accessible_websites.append(website)
        
        return accessible_websites
    
    def get_organisation_role(self, organisation_id):
        """Get user's role in a specific organisation."""
        from app.models.user_organisation_role import UserOrganisationRole
        role = UserOrganisationRole.query.filter_by(
            user_id=self.id,
            organisation_id=organisation_id
        ).first()
        return role.role if role else None
    
    def get_website_role(self, website_id):
        """Get user's role for a specific website."""
        from app.models.user_website_role import UserWebsiteRole
        role = UserWebsiteRole.query.filter_by(
            user_id=self.id,
            website_id=website_id
        ).first()
        return role.role if role else None
    
    def get_effective_website_role(self, website_id):
        """Get user's effective role for a website (direct or through organisation)."""
        # Check for direct website role first
        direct_role = self.get_website_role(website_id)
        if direct_role:
            return direct_role
        
        # Check for role through organisation membership
        from app.models.website import Website
        from app.models.organisation import OrganisationWebsite
        website = Website.query.get(website_id)
        if website:
            org_ids = [ow.organisation_id for ow in website.organisation_websites]
            for org_id in org_ids:
                org_role = self.get_organisation_role(org_id)
                if org_role:
                    return org_role
        
        return None
    
    def get_effective_website_role_display(self, website_id):
        """Get user's effective website role in a user-friendly format."""
        role = self.get_effective_website_role(website_id)
        if not role:
            return 'No Access'
        
        role_display_map = {
            'org_admin': 'Organisation Admin',
            'website_manager': 'Website Manager', 
            'website_viewer': 'Website Viewer'
        }
        
        return role_display_map.get(role, role.replace('_', ' ').title())
    
    def has_organisation_access(self, organisation_id):
        """Check if user has access to a specific organisation."""
        return self.is_super_admin or self.get_organisation_role(organisation_id) is not None
    
    def has_website_access(self, website_id):
        """Check if user has access to a specific website."""
        if self.is_super_admin:
            return True
        
        # Check direct website access
        if self.get_website_role(website_id) is not None:
            return True
        
        # Check via organisation access
        from app.models.website import Website
        from app.models.organisation import OrganisationWebsite
        website = Website.query.get(website_id)
        if website:
            org_ids = [ow.organisation_id for ow in website.organisation_websites]
            for org_id in org_ids:
                if self.has_organisation_access(org_id):
                    return True
        
        return False
    
    def is_organisation_admin(self, organisation_id=None):
        """Check if user is an organisation admin."""
        if self.is_super_admin:
            return True
        
        if organisation_id:
            role = self.get_organisation_role(organisation_id)
            return role == 'org_admin'
        else:
            # Check if user is org admin in any organisation
            from app.models.user_organisation_role import UserOrganisationRole
            return UserOrganisationRole.query.filter_by(
                user_id=self.id,
                role='org_admin'
            ).first() is not None
    
    def is_website_manager(self, website_id=None):
        """Check if user is a website manager."""
        if self.is_super_admin:
            return True
        
        if website_id:
            # Check direct website role
            website_role = self.get_website_role(website_id)
            if website_role == 'website_manager':
                return True
            
            # Check if user has website management role for any organisation that has access to this website
            from app.models.website import Website
            website = Website.query.get(website_id)
            if website:
                for org_website in website.organisation_websites:
                    org_role = self.get_organisation_role(org_website.organisation_id)
                    if org_role in ['org_admin', 'website_manager']:
                        return True
            
            return False
        else:
            # Check if user is website manager for any website or has website management org role
            from app.models.user_website_role import UserWebsiteRole
            from app.models.user_organisation_role import UserOrganisationRole
            
            # Check direct website roles
            if UserWebsiteRole.query.filter_by(user_id=self.id, role='website_manager').first():
                return True
            
            # Check organisation roles for website management
            org_roles = UserOrganisationRole.query.filter_by(user_id=self.id).all()
            for org_role in org_roles:
                if org_role.role in ['org_admin', 'website_manager']:
                    return True
            
            return False
    
    def can_manage_organisation(self, organisation_id):
        """Check if user can manage a specific organisation."""
        return self.is_super_admin or self.is_organisation_admin(organisation_id)
    
    def can_manage_website(self, website_id):
        """Check if user can manage a specific website."""
        return self.is_super_admin or self.is_website_manager(website_id)
    
    def can_view_website(self, website_id):
        """Check if user can view a specific website."""
        return self.has_website_access(website_id)
    
    def can_manage_crawl_job(self, crawl_job):
        """Check if user can manage a specific crawl job."""
        if self.is_super_admin:
            return True
        
        if hasattr(crawl_job, 'website_id') and crawl_job.website_id:
            return self.can_manage_website(crawl_job.website_id)
        
        # Fallback to legacy permissions for jobs without website_id
        return self.is_admin() or self.is_editor()
    
    def can_view_crawl_job(self, crawl_job):
        """Check if user can view a specific crawl job."""
        if self.is_super_admin:
            return True
        
        if hasattr(crawl_job, 'website_id') and crawl_job.website_id:
            return self.can_view_website(crawl_job.website_id)
        
        # Fallback to legacy permissions
        return True
    
    def can_manage_persona(self, persona):
        """Check if user can manage a specific persona."""
        if self.is_super_admin:
            return True
        
        if hasattr(persona, 'website_id') and persona.website_id:
            return self.can_manage_website(persona.website_id)
        
        # Fallback to legacy permissions
        return self.is_admin() or self.is_editor()
    
    def can_view_persona(self, persona):
        """Check if user can view a specific persona."""
        if self.is_super_admin:
            return True
        
        if hasattr(persona, 'website_id') and persona.website_id:
            return self.can_view_website(persona.website_id)
        
        # Fallback to legacy permissions
        return True
    
    # ============================================================================
    # LEGACY ROLE CHECKING METHODS (for backward compatibility)
    # ============================================================================
    
    def is_admin(self):
        """Check if the user has admin role."""
        return self.is_super_admin or self.role == self.ROLE_ADMIN
    
    def is_editor(self):
        """Check if the user has editor role."""
        return self.role == self.ROLE_EDITOR
    
    def is_viewer(self):
        """Check if the user has viewer role."""
        return self.role == self.ROLE_VIEWER
    
    # Permission checking methods
    def can_manage_users(self):
        """Check if user can add, edit, or delete users globally (super admin only)."""
        return self.is_super_admin
    
    def can_manage_organisation_users(self, organisation_id=None):
        """Check if user can manage users within a specific organisation."""
        if self.is_super_admin:
            return True
        if organisation_id and self.is_organisation_admin(organisation_id):
            return True
        return False
    
    def can_create_crawls(self):
        """Check if user can create and run crawls."""
        if self.is_super_admin:
            return True
        
        # Check if user has website management role in any organisation
        from app.models.user_organisation_role import UserOrganisationRole
        org_roles = UserOrganisationRole.query.filter_by(user_id=self.id).all()
        for org_role in org_roles:
            if org_role.role in ['org_admin', 'website_manager']:
                return True
        
        # Check direct website roles
        from app.models.user_website_role import UserWebsiteRole
        if UserWebsiteRole.query.filter_by(user_id=self.id, role='website_manager').first():
            return True
            
        # Fallback to legacy permissions
        return self.is_admin() or self.is_editor()
    
    def can_edit_crawls(self):
        """Check if user can edit crawls."""
        return self.is_admin() or self.is_editor()
    
    def can_delete_crawls(self):
        """Check if user can delete crawls."""
        return self.is_admin()
    
    def can_create_personas(self):
        """Check if user can create personas."""
        if self.is_super_admin:
            return True
        
        # Check if user has website management role in any organisation
        from app.models.user_organisation_role import UserOrganisationRole
        org_roles = UserOrganisationRole.query.filter_by(user_id=self.id).all()
        for org_role in org_roles:
            if org_role.role in ['org_admin', 'website_manager']:
                return True
        
        # Check direct website roles
        from app.models.user_website_role import UserWebsiteRole
        if UserWebsiteRole.query.filter_by(user_id=self.id, role='website_manager').first():
            return True
            
        # Fallback to legacy permissions
        return self.is_admin() or self.is_editor()
    
    def can_edit_personas(self):
        """Check if user can edit personas."""
        return self.is_admin() or self.is_editor()
    
    def can_delete_personas(self):
        """Check if user can delete personas."""
        return self.is_admin()
    
    def can_view_reports(self):
        """Check if user can view reports."""
        return True  # All users can view reports
    
    def can_export_data(self):
        """Check if user can export data."""
        return True  # All users can export data
    
    def get_role_display(self):
        """Get the display name for the user's role."""
        role_map = dict(self.get_roles())
        return role_map.get(self.role, 'Unknown')
    
    def generate_password_reset_token(self):
        """Generate a password reset token."""
        import secrets
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        db.session.commit()
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verify a password reset token."""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if datetime.utcnow() > self.password_reset_expires:
            return False
        return self.password_reset_token == token
    
    def reset_password_with_token(self, token, new_password):
        """Reset password using a valid token."""
        if self.verify_password_reset_token(token):
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_expires = None
            db.session.commit()
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))
