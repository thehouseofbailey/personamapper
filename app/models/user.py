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
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='viewer', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_EDITOR = 'editor'
    ROLE_VIEWER = 'viewer'
    
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
    
    # Role checking methods
    def is_admin(self):
        """Check if the user has admin role."""
        return self.role == self.ROLE_ADMIN
    
    def is_editor(self):
        """Check if the user has editor role."""
        return self.role == self.ROLE_EDITOR
    
    def is_viewer(self):
        """Check if the user has viewer role."""
        return self.role == self.ROLE_VIEWER
    
    # Permission checking methods
    def can_manage_users(self):
        """Check if user can add, edit, or delete users."""
        return self.is_admin()
    
    def can_create_crawls(self):
        """Check if user can create and run crawls."""
        return self.is_admin() or self.is_editor()
    
    def can_edit_crawls(self):
        """Check if user can edit crawls."""
        return self.is_admin() or self.is_editor()
    
    def can_delete_crawls(self):
        """Check if user can delete crawls."""
        return self.is_admin()
    
    def can_create_personas(self):
        """Check if user can create personas."""
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
