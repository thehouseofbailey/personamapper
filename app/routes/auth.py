from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from functools import wraps
from app import db
from app.models import User

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember_me)
            
            # Update last login time
            user.update_last_login()
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index')
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != password_confirm:
            errors.append('Passwords do not match.')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email address already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    """User logout."""
    username = current_user.username
    logout_user()
    flash(f'You have been logged out, {username}.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    from ..models.user_organisation_role import UserOrganisationRole
    from ..models.user_website_role import UserWebsiteRole
    from ..models.organisation import Organisation, OrganisationWebsite
    from ..models.website import Website
    
    # Get user's organizational roles
    org_roles = db.session.query(UserOrganisationRole, Organisation).join(
        Organisation, UserOrganisationRole.organisation_id == Organisation.id
    ).filter(UserOrganisationRole.user_id == current_user.id).all()
    
    # Get user's website roles with organization info
    website_roles = db.session.query(UserWebsiteRole, Website, Organisation).join(
        Website, UserWebsiteRole.website_id == Website.id
    ).join(
        OrganisationWebsite, Website.id == OrganisationWebsite.website_id
    ).join(
        Organisation, OrganisationWebsite.organisation_id == Organisation.id
    ).filter(UserWebsiteRole.user_id == current_user.id).all()
    
    # Get user's accessible organizations
    accessible_orgs = current_user.get_organisations()
    
    return render_template('auth/profile.html', 
                         org_roles=org_roles,
                         website_roles=website_roles,
                         accessible_orgs=accessible_orgs)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')

# Permission decorator
def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage_users():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# User Management Routes
@bp.route('/users')
@login_required
@admin_required
def manage_users():
    """User management page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('auth/manage_users.html', users=users)

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        is_active = bool(request.form.get('is_active'))
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if role not in [r[0] for r in User.get_roles()]:
            errors.append('Invalid role selected.')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email address already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/create_user.html', roles=User.get_roles())
        
        # Create new user
        user = User(username=username, email=email, role=role, is_active=is_active)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} created successfully!', 'success')
        return redirect(url_for('auth.manage_users'))
    
    return render_template('auth/create_user.html', roles=User.get_roles())

@bp.route('/users/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit user details."""
    user = User.query.get_or_404(id)
    
    # Prevent users from modifying their own super admin status
    if user.id == current_user.id and 'is_super_admin' in request.form:
        flash('You cannot modify your own super admin status.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    # Get form data
    email = request.form.get('email', '').strip()
    new_password = request.form.get('new_password', '').strip()
    is_super_admin = 'is_super_admin' in request.form and user.id != current_user.id
    
    # Validation
    errors = []
    
    if email and '@' not in email:
        errors.append('Please enter a valid email address.')
    
    # Check if email already exists (excluding current user)
    if email:
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            errors.append('Email address already registered.')
    
    # Check if we're removing the last super admin
    if user.is_super_admin and not is_super_admin:
        super_admin_count = User.query.filter_by(is_super_admin=True).count()
        if super_admin_count <= 1:
            errors.append('Cannot remove the last super admin.')
    
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('auth.manage_users'))
    
    # Update user
    user.email = email or user.email
    user.is_super_admin = is_super_admin
    
    if new_password:
        user.set_password(new_password)
        
    db.session.commit()
    
    flash(f'User {user.username} updated successfully!', 'success')
    return redirect(url_for('auth.manage_users'))

@bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Delete user."""
    user = User.query.get_or_404(id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    # Prevent deleting the last super admin
    if user.is_super_admin:
        super_admin_count = User.query.filter_by(is_super_admin=True).count()
        if super_admin_count <= 1:
            flash('Cannot delete the last super admin user.', 'error')
            return redirect(url_for('auth.manage_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} deleted successfully!', 'success')
    return redirect(url_for('auth.manage_users'))

@bp.route('/users/<int:id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(id):
    """Activate user."""
    user = User.query.get_or_404(id)
    
    user.is_active = True
    db.session.commit()
    
    flash(f'User {user.username} activated successfully!', 'success')
    return redirect(url_for('auth.manage_users'))

@bp.route('/users/<int:id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_user(id):
    """Deactivate user."""
    user = User.query.get_or_404(id)
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    user.is_active = False
    db.session.commit()
    
    flash(f'User {user.username} deactivated successfully!', 'success')
    return redirect(url_for('auth.manage_users'))

@bp.route('/users/<int:id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(id):
    """Admin reset user password."""
    user = User.query.get_or_404(id)
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'Password reset for user {user.username}!', 'success')
    return redirect(url_for('auth.manage_users'))

# Password Reset Routes
@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = user.generate_password_reset_token()
            
            # In a real application, you would send an email here
            # For now, we'll just show the reset link
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            flash(f'Password reset link (for demo): {reset_url}', 'info')
        else:
            # Don't reveal if email exists or not
            flash('If that email address is in our system, you will receive a password reset link.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Find user with this token
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.verify_password_reset_token(token):
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Reset password
        if user.reset_password_with_token(token, new_password):
            flash('Password reset successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Password reset failed. Please try again.', 'error')
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', token=token)
