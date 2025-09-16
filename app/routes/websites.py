"""
Routes for website management.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Website, Organisation, User, UserWebsiteRole, CrawlJob, Persona
from app.auth.permissions import (
    super_admin_required, website_manager_required, 
    get_user_accessible_websites
)

bp = Blueprint('websites', __name__)

@bp.route('/')
@login_required
def list_websites():
    """List all websites accessible to the current user."""
    websites = get_user_accessible_websites()
    return render_template('websites/list.html', websites=websites)

@bp.route('/<int:id>')
@login_required
def view_website(id):
    """View website details."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_view_website(id):
        flash('You do not have access to this website.', 'error')
        return redirect(url_for('websites.list_websites'))
    
    organisations = website.get_organisations()
    users = website.get_users()
    crawl_jobs = website.get_crawl_jobs()
    personas = website.get_personas()
    
    return render_template('websites/view.html', 
                         website=website, 
                         organisations=organisations,
                         users=users,
                         crawl_jobs=crawl_jobs,
                         personas=personas)

@bp.route('/<int:id>/crawls')
@login_required
def website_crawls(id):
    """View all crawl jobs for a website."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_view_website(id):
        flash('You do not have access to this website.', 'error')
        return redirect(url_for('websites.list_websites'))
    
    # Get all crawl jobs for this website
    crawl_jobs = website.get_crawl_jobs()
    organisations = website.get_organisations()
    
    return render_template('websites/crawls.html', 
                         website=website, 
                         crawl_jobs=crawl_jobs,
                         organisations=organisations)

@bp.route('/create', methods=['GET', 'POST'])
@super_admin_required
def create_website():
    """Create a new website (super admin only)."""
    if request.method == 'POST':
        name = request.form.get('name')
        domain = request.form.get('domain')
        description = request.form.get('description', '')
        organisation_ids = request.form.getlist('organisations')
        is_active = 'is_active' in request.form
        
        if not name or not domain:
            flash('Website name and domain are required.', 'error')
            organisations = Organisation.query.filter_by(is_active=True).all()
            return render_template('websites/create.html', organisations=organisations)
        
        # Check if domain already exists
        if Website.query.filter_by(domain=domain).first():
            flash('A website with this domain already exists.', 'error')
            organisations = Organisation.query.filter_by(is_active=True).all()
            return render_template('websites/create.html', organisations=organisations)
        
        website = Website(
            name=name,
            domain=domain,
            description=description,
            is_active=is_active
        )
        
        db.session.add(website)
        db.session.flush()  # Get the ID before commit
        
        # Add selected organisations
        from app.models.organisation import OrganisationWebsite
        for org_id in organisation_ids:
            if org_id:
                org_website = OrganisationWebsite(
                    organisation_id=int(org_id),
                    website_id=website.id
                )
                db.session.add(org_website)
        
        db.session.commit()
        
        flash(f'Website "{name}" created successfully!', 'success')
        return redirect(url_for('websites.view_website', id=website.id))
    
    organisations = Organisation.query.filter_by(is_active=True).all()
    return render_template('websites/create.html', organisations=organisations)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_website(id):
    """Edit website details."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_manage_website(id):
        flash('You do not have permission to edit this website.', 'error')
        return redirect(url_for('websites.view_website', id=id))
    
    if request.method == 'POST':
        name = request.form.get('name')
        domain = request.form.get('domain')
        description = request.form.get('description', '')
        
        if not name or not domain:
            flash('Website name and domain are required.', 'error')
            return render_template('websites/edit.html', website=website)
        
        # Check if domain is taken by another website
        existing = Website.query.filter(
            Website.domain == domain,
            Website.id != id
        ).first()
        
        if existing:
            flash('A website with this domain already exists.', 'error')
            return render_template('websites/edit.html', website=website)
        
        website.name = name
        website.domain = domain
        website.description = description
        
        db.session.commit()
        
        flash(f'Website "{name}" updated successfully!', 'success')
        return redirect(url_for('websites.view_website', id=id))
    
    return render_template('websites/edit.html', website=website)

@bp.route('/<int:id>/users')
@login_required
def manage_users(id):
    """Manage users for website."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_manage_website(id):
        flash('You do not have permission to manage users for this website.', 'error')
        return redirect(url_for('websites.view_website', id=id))
    
    users = website.get_users()
    
    # Get users from organisations that have access to this website
    available_users = []
    for org in website.get_organisations():
        for user in org.get_users():
            if user not in users and user not in available_users:
                available_users.append(user)
    
    return render_template('websites/manage_users.html', 
                         website=website, 
                         users=users, 
                         available_users=available_users)

@bp.route('/<int:id>/users/add', methods=['POST'])
@login_required
def add_user(id):
    """Add a user to website."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_manage_website(id):
        flash('You do not have permission to manage users for this website.', 'error')
        return redirect(url_for('websites.view_website', id=id))
    
    user_id = request.form.get('user_id')
    role = request.form.get('role', 'website_viewer')
    
    if not user_id:
        flash('Please select a user.', 'error')
        return redirect(url_for('websites.manage_users', id=id))
    
    user = User.query.get_or_404(user_id)
    
    # Check if user has access to website through an organisation
    has_org_access = False
    for org in website.get_organisations():
        if current_user.has_organisation_access(org.id):
            has_org_access = True
            break
    
    if not has_org_access and not current_user.is_super_admin:
        flash('User must be in an organisation that has access to this website.', 'error')
        return redirect(url_for('websites.manage_users', id=id))
    
    try:
        website.add_user(user_id, role)
        flash(f'User "{user.username}" added to website with role "{role}".', 'success')
    except Exception as e:
        flash(f'Error adding user: {str(e)}', 'error')
    
    return redirect(url_for('websites.manage_users', id=id))

@bp.route('/<int:id>/users/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_user(id, user_id):
    """Remove a user from website."""
    website = Website.query.get_or_404(id)
    user = User.query.get_or_404(user_id)
    
    if not current_user.can_manage_website(id):
        flash('You do not have permission to manage users for this website.', 'error')
        return redirect(url_for('websites.view_website', id=id))
    
    try:
        website.remove_user(user_id)
        flash(f'User "{user.username}" removed from website.', 'success')
    except Exception as e:
        flash(f'Error removing user: {str(e)}', 'error')
    
    return redirect(url_for('websites.manage_users', id=id))

@bp.route('/<int:id>/crawl-jobs')
@login_required
def view_crawl_jobs(id):
    """View crawl jobs for website."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_view_website(id):
        flash('You do not have access to this website.', 'error')
        return redirect(url_for('websites.list_websites'))
    
    crawl_jobs = website.get_crawl_jobs()
    
    return render_template('websites/crawl_jobs.html', 
                         website=website, 
                         crawl_jobs=crawl_jobs)

@bp.route('/<int:id>/personas')
@login_required
def view_personas(id):
    """View personas for website."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_view_website(id):
        flash('You do not have access to this website.', 'error')
        return redirect(url_for('websites.list_websites'))
    
    personas = website.get_personas()
    
    return render_template('websites/personas.html', 
                         website=website, 
                         personas=personas)

# API endpoints
@bp.route('/api/websites')
@login_required
def api_list_websites():
    """API endpoint to list accessible websites."""
    websites = get_user_accessible_websites()
    return jsonify([website.to_dict() for website in websites])

@bp.route('/api/websites/<int:id>')
@login_required
def api_get_website(id):
    """API endpoint to get website details."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_view_website(id):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(website.to_dict())

@bp.route('/api/websites/<int:id>/crawl-jobs')
@login_required
def api_get_website_crawl_jobs(id):
    """API endpoint to get crawl jobs for website."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_view_website(id):
        return jsonify({'error': 'Access denied'}), 403
    
    crawl_jobs = website.get_crawl_jobs()
    return jsonify([job.to_dict() for job in crawl_jobs if hasattr(job, 'to_dict')])

@bp.route('/api/websites/<int:id>/personas')
@login_required
def api_get_website_personas(id):
    """API endpoint to get personas for website."""
    website = Website.query.get_or_404(id)
    
    if not current_user.can_view_website(id):
        return jsonify({'error': 'Access denied'}), 403
    
    personas = website.get_personas()
    return jsonify([persona.to_dict() for persona in personas])

@bp.route('/<int:id>/manage-organisations', methods=['GET', 'POST'])
@super_admin_required
def manage_organisations(id):
    """Manage organisations for a website (super admin only)."""
    website = Website.query.get_or_404(id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        org_id = request.form.get('organisation_id')
        
        if action == 'add' and org_id:
            from app.models.organisation import OrganisationWebsite
            # Check if already exists
            existing = OrganisationWebsite.query.filter_by(
                organisation_id=org_id,
                website_id=id
            ).first()
            
            if not existing:
                org_website = OrganisationWebsite(
                    organisation_id=org_id,
                    website_id=id
                )
                db.session.add(org_website)
                db.session.commit()
                flash('Organisation added successfully!', 'success')
            else:
                flash('Organisation is already assigned to this website.', 'warning')
        
        elif action == 'remove' and org_id:
            from app.models.organisation import OrganisationWebsite
            org_website = OrganisationWebsite.query.filter_by(
                organisation_id=org_id,
                website_id=id
            ).first()
            
            if org_website:
                db.session.delete(org_website)
                db.session.commit()
                flash('Organisation removed successfully!', 'success')
        
        return redirect(url_for('websites.manage_organisations', id=id))
    
    assigned_orgs = website.get_organisations()
    all_orgs = Organisation.query.filter_by(is_active=True).all()
    available_orgs = [org for org in all_orgs if org not in assigned_orgs]
    
    return render_template('websites/manage_organisations.html', 
                         website=website, 
                         assigned_organisations=assigned_orgs,
                         available_organisations=available_orgs)

@bp.route('/<int:id>/manage-users', methods=['GET', 'POST'])
@super_admin_required  
def manage_website_users(id):
    """Manage users for a website (super admin only)."""
    website = Website.query.get_or_404(id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        role = request.form.get('role', 'website_viewer')
        
        if action == 'add' and user_id:
            existing_role = UserWebsiteRole.query.filter_by(
                user_id=user_id,
                website_id=id
            ).first()
            
            if not existing_role:
                user_role = UserWebsiteRole(
                    user_id=user_id,
                    website_id=id,
                    role=role
                )
                db.session.add(user_role)
                db.session.commit()
                flash('User added successfully!', 'success')
            else:
                # Update existing role
                existing_role.role = role
                db.session.commit()
                flash('User role updated successfully!', 'success')
        
        elif action == 'remove' and user_id:
            user_role = UserWebsiteRole.query.filter_by(
                user_id=user_id,
                website_id=id
            ).first()
            
            if user_role:
                db.session.delete(user_role)
                db.session.commit()
                flash('User removed successfully!', 'success')
        
        return redirect(url_for('websites.manage_website_users', id=id))
    
    assigned_users = website.get_users()
    all_users = User.query.filter_by(is_active=True).all()
    available_users = [user for user in all_users if user not in assigned_users]
    
    return render_template('websites/manage_users.html', 
                         website=website, 
                         assigned_users=assigned_users,
                         available_users=available_users)
