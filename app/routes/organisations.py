"""
Routes for organisation management.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Organisation, Website, User, UserOrganisationRole, UserWebsiteRole
from app.forms.organisation_forms import AIConfigForm
from app.auth.permissions import (
    super_admin_required, organisation_admin_required, 
    get_user_accessible_organisations
)

bp = Blueprint('organisations', __name__)

@bp.route('/')
@login_required
def list_organisations():
    """List all organisations accessible to the current user."""
    organisations = get_user_accessible_organisations()
    return render_template('organisations/list.html', organisations=organisations)

@bp.route('/<int:id>')
@login_required
def view_organisation(id):
    """View organisation details."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.has_organisation_access(id):
        flash('You do not have access to this organisation.', 'error')
        return redirect(url_for('organisations.list_organisations'))
    
    users = organisation.get_users()
    websites = organisation.get_websites()
    
    return render_template('organisations/view.html', 
                         organisation=organisation, 
                         users=users, 
                         websites=websites)

@bp.route('/create', methods=['GET', 'POST'])
@super_admin_required
def create_organisation():
    """Create a new organisation (super admin only)."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Organisation name is required.', 'error')
            return render_template('organisations/create.html')
        
        # Check if organisation already exists
        if Organisation.query.filter_by(name=name).first():
            flash('An organisation with this name already exists.', 'error')
            return render_template('organisations/create.html')
        
        organisation = Organisation(
            name=name,
            description=description,
            is_active=True
        )
        
        db.session.add(organisation)
        db.session.commit()
        
        flash(f'Organisation "{name}" created successfully!', 'success')
        return redirect(url_for('organisations.view_organisation', id=organisation.id))
    
    return render_template('organisations/create.html')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_organisation(id):
    """Edit organisation details."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to edit this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Organisation name is required.', 'error')
            return render_template('organisations/edit.html', organisation=organisation)
        
        # Check if name is taken by another organisation
        existing = Organisation.query.filter(
            Organisation.name == name,
            Organisation.id != id
        ).first()
        
        if existing:
            flash('An organisation with this name already exists.', 'error')
            return render_template('organisations/edit.html', organisation=organisation)
        
        organisation.name = name
        organisation.description = description
        
        db.session.commit()
        
        flash(f'Organisation "{name}" updated successfully!', 'success')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    return render_template('organisations/edit.html', organisation=organisation)

@bp.route('/<int:id>/ai-config', methods=['GET', 'POST'])
@login_required
def ai_config(id):
    """Configure AI settings for organisation."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to configure AI settings for this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    form = AIConfigForm()
    
    if form.validate_on_submit():
        try:
            # Prepare the configuration data
            config_data = {
                'ai_enabled': form.ai_enabled.data,
                'ai_analysis_mode': form.ai_analysis_mode.data,
                'openai_model': form.openai_model.data,
                'openai_max_tokens': form.openai_max_tokens.data,
                'openai_temperature': form.openai_temperature.data,
                'ai_daily_cost_limit': form.ai_daily_cost_limit.data,
                'ai_monthly_cost_limit': form.ai_monthly_cost_limit.data,
                'local_ai_model': form.local_ai_model.data,
                'local_ai_similarity_threshold': form.local_ai_similarity_threshold.data,
                'ai_confidence_threshold': form.ai_confidence_threshold.data,
                'ai_content_chunk_size': form.ai_content_chunk_size.data
            }
            
            # Only include API key if it was provided
            if form.openai_api_key.data:
                config_data['openai_api_key'] = form.openai_api_key.data
            
            # Update the organisation
            organisation.update_ai_config(config_data)
            db.session.commit()
            
            flash('AI configuration updated successfully!', 'success')
            return redirect(url_for('organisations.view_organisation', id=id))
            
        except Exception as e:
            flash(f'Error updating AI configuration: {str(e)}', 'error')
            db.session.rollback()
    
    elif request.method == 'GET':
        # Pre-populate form with current values
        ai_config = organisation.get_ai_config()
        form.ai_enabled.data = ai_config['ai_enabled']
        form.ai_analysis_mode.data = ai_config['ai_analysis_mode']
        form.openai_model.data = ai_config['openai_model']
        form.openai_max_tokens.data = ai_config['openai_max_tokens']
        form.openai_temperature.data = ai_config['openai_temperature']
        form.ai_daily_cost_limit.data = ai_config['ai_daily_cost_limit']
        form.ai_monthly_cost_limit.data = ai_config['ai_monthly_cost_limit']
        form.local_ai_model.data = ai_config['local_ai_model']
        form.local_ai_similarity_threshold.data = ai_config['local_ai_similarity_threshold']
        form.ai_confidence_threshold.data = ai_config['ai_confidence_threshold']
        form.ai_content_chunk_size.data = ai_config['ai_content_chunk_size']
    
    return render_template('organisations/ai_config.html', 
                         organisation=organisation, 
                         form=form,
                         current_config=organisation.get_ai_config())

@bp.route('/<int:id>/users')
@login_required
def manage_users(id):
    """Manage users in organisation."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to manage users in this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    # Get UserOrganisationRole objects to access both user and role information
    user_roles = UserOrganisationRole.query.filter_by(organisation_id=id).all()
    users = [ur.user for ur in user_roles]
    all_users = User.query.filter_by(is_active=True).all()
    available_users = [u for u in all_users if u not in users]
    
    return render_template('organisations/manage_users.html', 
                         organisation=organisation, 
                         organisation_users=user_roles, 
                         available_users=available_users)

@bp.route('/<int:id>/users/add', methods=['POST'])
@login_required
def add_user(id):
    """Add a user to organisation."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to manage users in this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    user_id = request.form.get('user_id')
    role = request.form.get('role', 'website_viewer')
    
    if not user_id:
        flash('Please select a user.', 'error')
        return redirect(url_for('organisations.manage_users', id=id))
    
    user = User.query.get_or_404(user_id)
    
    try:
        organisation.add_user(user_id, role)
        flash(f'User "{user.username}" added to organisation with role "{role}".', 'success')
    except Exception as e:
        flash(f'Error adding user: {str(e)}', 'error')
    
    return redirect(url_for('organisations.manage_users', id=id))

@bp.route('/<int:id>/users/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_user(id, user_id):
    """Remove a user from organisation."""
    organisation = Organisation.query.get_or_404(id)
    user = User.query.get_or_404(user_id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to manage users in this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    # Prevent removing self if it's the last org admin
    if user_id == current_user.id:
        admins = organisation.get_admins()
        if len(admins) <= 1:
            flash('Cannot remove yourself as you are the only admin of this organisation.', 'error')
            return redirect(url_for('organisations.manage_users', id=id))
    
    try:
        organisation.remove_user(user_id)
        flash(f'User "{user.username}" removed from organisation.', 'success')
    except Exception as e:
        flash(f'Error removing user: {str(e)}', 'error')
    
    return redirect(url_for('organisations.manage_users', id=id))

@bp.route('/<int:id>/websites')
@login_required
def manage_websites(id):
    """Manage websites for organisation."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to manage websites for this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    from ..models.organisation import OrganisationWebsite
    organisation_websites = OrganisationWebsite.query.filter_by(organisation_id=id).all()
    websites = organisation.get_websites()
    all_websites = Website.query.filter_by(is_active=True).all()
    available_websites = [w for w in all_websites if w not in websites]
    
    return render_template('organisations/manage_websites.html', 
                         organisation=organisation, 
                         organisation_websites=organisation_websites,
                         websites=websites, 
                         available_websites=available_websites)

@bp.route('/<int:id>/websites/add', methods=['POST'])
@login_required
def add_website(id):
    """Add a website to organisation."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to manage websites for this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    website_id = request.form.get('website_id')
    
    if not website_id:
        flash('Please select a website.', 'error')
        return redirect(url_for('organisations.manage_websites', id=id))
    
    website = Website.query.get_or_404(website_id)
    
    try:
        organisation.add_website(website_id)
        flash(f'Website "{website.name}" added to organisation.', 'success')
    except Exception as e:
        flash(f'Error adding website: {str(e)}', 'error')
    
    return redirect(url_for('organisations.manage_websites', id=id))

@bp.route('/<int:id>/websites/<int:website_id>/remove', methods=['POST'])
@login_required
def remove_website(id, website_id):
    """Remove a website from organisation."""
    organisation = Organisation.query.get_or_404(id)
    website = Website.query.get_or_404(website_id)
    
    if not current_user.can_manage_organisation(id):
        flash('You do not have permission to manage websites for this organisation.', 'error')
        return redirect(url_for('organisations.view_organisation', id=id))
    
    try:
        organisation.remove_website(website_id)
        flash(f'Website "{website.name}" removed from organisation.', 'success')
    except Exception as e:
        flash(f'Error removing website: {str(e)}', 'error')
    
    return redirect(url_for('organisations.manage_websites', id=id))

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Create a new user (accessible from organisation user management)."""
    if not current_user.can_manage_users():
        flash('You do not have permission to create users.', 'error')
        return redirect(url_for('organisations.list_organisations'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email address already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('organisations/create_user.html')
        
        # Create new user (as regular user by default)
        user = User(username=username, email=email, is_active=True)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} created successfully!', 'success')
        return redirect(url_for('organisations.list_organisations'))
    
    return render_template('organisations/create_user.html')

@bp.route('/<int:id>/dashboard')
@login_required
def organisation_dashboard(id):
    """Organisation-specific dashboard showing statistics for this organisation."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.has_organisation_access(id):
        flash('You do not have access to this organisation.', 'error')
        return redirect(url_for('organisations.list_organisations'))
    
    # Get organisation's websites and their data
    websites = organisation.get_websites()
    website_ids = [w.id for w in websites]
    
    # Get crawl jobs and personas for this organisation
    from app.models import CrawlJob, Persona, CrawledPage, ContentMapping
    crawl_jobs = CrawlJob.query.filter(CrawlJob.website_id.in_(website_ids)).all() if website_ids else []
    personas = Persona.query.filter(
        Persona.website_id.in_(website_ids),
        Persona.is_active == True
    ).all() if website_ids else []
    
    crawl_job_ids = [j.id for j in crawl_jobs]
    persona_ids = [p.id for p in personas]
    
    # Calculate organisation-specific statistics
    stats = {
        'total_websites': len(websites),
        'total_personas': len(personas),
        'total_crawl_jobs': len(crawl_jobs),
        'active_crawl_jobs': len([j for j in crawl_jobs if j.status == 'active']),
        'running_crawl_jobs': len([j for j in crawl_jobs if j.status == 'running']),
        'total_pages_crawled': CrawledPage.query.filter(
            CrawledPage.crawl_job_id.in_(crawl_job_ids) if crawl_job_ids else False
        ).count(),
        'total_mappings': ContentMapping.query.filter(
            ContentMapping.persona_id.in_(persona_ids) if persona_ids else False,
            ContentMapping.is_active == True
        ).count(),
        'high_confidence_mappings': ContentMapping.query.filter(
            ContentMapping.persona_id.in_(persona_ids) if persona_ids else False,
            ContentMapping.confidence_score >= 0.8,
            ContentMapping.is_active == True
        ).count()
    }
    
    # Get recent activity for this organisation
    recent_pages = CrawledPage.query.filter(
        CrawledPage.crawl_job_id.in_(crawl_job_ids) if crawl_job_ids else False
    ).order_by(CrawledPage.crawled_at.desc()).limit(5).all()
    
    recent_mappings = ContentMapping.query.filter(
        ContentMapping.persona_id.in_(persona_ids) if persona_ids else False,
        ContentMapping.is_active == True
    ).order_by(ContentMapping.created_at.desc()).limit(5).all()
    
    # Get top personas for this organisation
    from sqlalchemy import func
    top_personas = db.session.query(
        Persona,
        func.count(ContentMapping.id).label('mapping_count')
    ).join(
        ContentMapping, Persona.id == ContentMapping.persona_id
    ).filter(
        Persona.id.in_(persona_ids) if persona_ids else False,
        Persona.is_active == True,
        ContentMapping.is_active == True
    ).group_by(Persona.id).order_by(
        func.count(ContentMapping.id).desc()
    ).limit(5).all()
    
    return render_template('organisations/dashboard.html',
                         organisation=organisation,
                         stats=stats,
                         websites=websites,
                         crawl_jobs=crawl_jobs[:5],  # Show only first 5
                         personas=personas[:5],  # Show only first 5
                         recent_pages=recent_pages,
                         recent_mappings=recent_mappings,
                         top_personas=top_personas)

@bp.route('/<int:id>/personas')
@login_required
def organisation_personas(id):
    """List personas for a specific organisation."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.has_organisation_access(id):
        flash('You do not have access to this organisation.', 'error')
        return redirect(url_for('organisations.list_organisations'))
    
    # Get organisation's websites and their personas
    websites = organisation.get_websites()
    website_ids = [w.id for w in websites]
    
    from app.models import Persona
    personas = Persona.query.filter(
        Persona.website_id.in_(website_ids) if website_ids else False,
        Persona.is_active == True
    ).order_by(Persona.title).all()
    
    return render_template('organisations/personas.html',
                         organisation=organisation,
                         personas=personas,
                         websites=websites)

# API endpoints
@bp.route('/api/organisations')
@login_required
def api_list_organisations():
    """API endpoint to list accessible organisations."""
    organisations = get_user_accessible_organisations()
    return jsonify([org.to_dict() for org in organisations])

@bp.route('/api/organisations/<int:id>')
@login_required
def api_get_organisation(id):
    """API endpoint to get organisation details."""
    organisation = Organisation.query.get_or_404(id)
    
    if not current_user.has_organisation_access(id):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(organisation.to_dict())
