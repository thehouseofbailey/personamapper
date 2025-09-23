"""
Access control decorators and helper functions for role-based permissions.
"""
from functools import wraps
from flask import abort, request, jsonify
from flask_login import current_user
from app import db
from app.models import Organisation, Website, CrawlJob, Persona

def super_admin_required(f):
    """Decorator to require super admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def organisation_access_required(organisation_id_param='organisation_id'):
    """Decorator to require access to a specific organisation."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get organisation_id from kwargs, args, or request
            organisation_id = None
            if organisation_id_param in kwargs:
                organisation_id = kwargs[organisation_id_param]
            elif organisation_id_param in request.view_args:
                organisation_id = request.view_args[organisation_id_param]
            elif hasattr(request, 'json') and request.json and organisation_id_param in request.json:
                organisation_id = request.json[organisation_id_param]
            
            if organisation_id is None:
                abort(400, "Organisation ID not provided")
            
            if not current_user.has_organisation_access(organisation_id):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def organisation_admin_required(organisation_id_param='organisation_id'):
    """Decorator to require organisation admin privileges."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get organisation_id from kwargs, args, or request
            organisation_id = None
            if organisation_id_param in kwargs:
                organisation_id = kwargs[organisation_id_param]
            elif organisation_id_param in request.view_args:
                organisation_id = request.view_args[organisation_id_param]
            elif hasattr(request, 'json') and request.json and organisation_id_param in request.json:
                organisation_id = request.json[organisation_id_param]
            
            if organisation_id is None:
                abort(400, "Organisation ID not provided")
            
            if not current_user.can_manage_organisation(organisation_id):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def website_access_required(website_id_param='website_id'):
    """Decorator to require access to a specific website."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get website_id from kwargs, args, or request
            website_id = None
            if website_id_param in kwargs:
                website_id = kwargs[website_id_param]
            elif website_id_param in request.view_args:
                website_id = request.view_args[website_id_param]
            elif hasattr(request, 'json') and request.json and website_id_param in request.json:
                website_id = request.json[website_id_param]
            
            if website_id is None:
                abort(400, "Website ID not provided")
            
            if not current_user.can_view_website(website_id):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def website_manager_required(website_id_param='website_id'):
    """Decorator to require website manager privileges."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get website_id from kwargs, args, or request
            website_id = None
            if website_id_param in kwargs:
                website_id = kwargs[website_id_param]
            elif website_id_param in request.view_args:
                website_id = request.view_args[website_id_param]
            elif hasattr(request, 'json') and request.json and website_id_param in request.json:
                website_id = request.json[website_id_param]
            
            if website_id is None:
                abort(400, "Website ID not provided")
            
            if not current_user.can_manage_website(website_id):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def crawl_job_access_required(crawl_job_id_param='id'):
    """Decorator to require access to a specific crawl job."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get crawl_job_id from kwargs, args, or request
            crawl_job_id = None
            if crawl_job_id_param in kwargs:
                crawl_job_id = kwargs[crawl_job_id_param]
            elif crawl_job_id_param in request.view_args:
                crawl_job_id = request.view_args[crawl_job_id_param]
            
            if crawl_job_id is None:
                abort(400, "Crawl job ID not provided")
            
            crawl_job = CrawlJob.query.get_or_404(crawl_job_id)
            
            if not current_user.can_view_crawl_job(crawl_job):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def crawl_job_manager_required(crawl_job_id_param='id'):
    """Decorator to require management access to a specific crawl job."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get crawl_job_id from kwargs, args, or request
            crawl_job_id = None
            if crawl_job_id_param in kwargs:
                crawl_job_id = kwargs[crawl_job_id_param]
            elif crawl_job_id_param in request.view_args:
                crawl_job_id = request.view_args[crawl_job_id_param]
            
            if crawl_job_id is None:
                abort(400, "Crawl job ID not provided")
            
            crawl_job = CrawlJob.query.get_or_404(crawl_job_id)
            
            if not current_user.can_manage_crawl_job(crawl_job):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def persona_access_required(persona_id_param='id'):
    """Decorator to require access to a specific persona."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get persona_id from kwargs, args, or request
            persona_id = None
            if persona_id_param in kwargs:
                persona_id = kwargs[persona_id_param]
            elif persona_id_param in request.view_args:
                persona_id = request.view_args[persona_id_param]
            
            if persona_id is None:
                abort(400, "Persona ID not provided")
            
            persona = Persona.query.get_or_404(persona_id)
            
            if not current_user.can_view_persona(persona):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def persona_manager_required(persona_id_param='id'):
    """Decorator to require management access to a specific persona."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get persona_id from kwargs, args, or request
            persona_id = None
            if persona_id_param in kwargs:
                persona_id = kwargs[persona_id_param]
            elif persona_id_param in request.view_args:
                persona_id = request.view_args[persona_id_param]
            
            if persona_id is None:
                abort(400, "Persona ID not provided")
            
            persona = Persona.query.get_or_404(persona_id)
            
            if not current_user.can_manage_persona(persona):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# HELPER FUNCTIONS FOR CONTEXT-AWARE ACCESS CONTROL
# ============================================================================

def get_user_accessible_organisations():
    """Get all organisations the current user has access to."""
    if not current_user.is_authenticated:
        return []
    
    if current_user.is_super_admin:
        return Organisation.query.filter_by(is_active=True).all()
    
    return current_user.get_organisations()

def get_user_accessible_websites():
    """Get all websites the current user has access to."""
    if not current_user.is_authenticated:
        return []
    
    if current_user.is_super_admin:
        return Website.query.filter_by(is_active=True).all()
    
    return current_user.get_accessible_websites()

def get_user_accessible_crawl_jobs():
    """Get all crawl jobs the current user has access to."""
    if not current_user.is_authenticated:
        return []
    
    if current_user.is_super_admin:
        return CrawlJob.query.all()
    
    # Get crawl jobs from accessible websites
    accessible_websites = get_user_accessible_websites()
    website_ids = [w.id for w in accessible_websites]
    
    crawl_jobs = CrawlJob.query.filter(
        db.or_(
            CrawlJob.website_id.in_(website_ids),
            CrawlJob.website_id.is_(None)  # Include legacy crawl jobs without website_id
        )
    ).all()
    
    # Filter legacy crawl jobs based on old permission system
    filtered_jobs = []
    for job in crawl_jobs:
        if job.website_id or current_user.can_view_crawl_job(job):
            filtered_jobs.append(job)
    
    return filtered_jobs

def get_user_accessible_personas():
    """Get all personas the current user has access to."""
    if not current_user.is_authenticated:
        return []
    
    if current_user.is_super_admin:
        return Persona.query.filter_by(is_active=True).all()
    
    # Get personas from accessible websites
    accessible_websites = get_user_accessible_websites()
    website_ids = [w.id for w in accessible_websites]
    
    personas = Persona.query.filter(
        db.or_(
            Persona.website_id.in_(website_ids),
            Persona.website_id.is_(None)  # Include legacy personas without website_id
        ),
        Persona.is_active == True
    ).all()
    
    # Filter legacy personas based on old permission system
    filtered_personas = []
    for persona in personas:
        if persona.website_id or current_user.can_view_persona(persona):
            filtered_personas.append(persona)
    
    return filtered_personas

def filter_crawl_jobs_by_access(crawl_jobs):
    """Filter a list of crawl jobs based on user access."""
    if not current_user.is_authenticated:
        return []
    
    if current_user.is_super_admin:
        return crawl_jobs
    
    return [job for job in crawl_jobs if current_user.can_view_crawl_job(job)]

def filter_personas_by_access(personas):
    """Filter a list of personas based on user access."""
    if not current_user.is_authenticated:
        return []
    
    if current_user.is_super_admin:
        return personas
    
    return [persona for persona in personas if current_user.can_view_persona(persona)]


# ============================================================================
# EXAMPLE ASSIGNMENT/REMOVAL FUNCTIONS
# ============================================================================

def assign_user_to_organisation(user_id, organisation_id, role='website_viewer'):
    """Assign a user to an organisation with a specific role."""
    if not current_user.is_authenticated or not current_user.is_super_admin:
        raise PermissionError("Only super admins can assign users to organisations")
    
    from app.models import User, Organisation
    from app import db
    
    user = User.query.get_or_404(user_id)
    organisation = Organisation.query.get_or_404(organisation_id)
    
    organisation.add_user(user_id, role)
    return True

def remove_user_from_organisation(user_id, organisation_id):
    """Remove a user from an organisation."""
    if not current_user.is_authenticated:
        raise PermissionError("Authentication required")
    
    from app.models import User, Organisation
    
    user = User.query.get_or_404(user_id)
    organisation = Organisation.query.get_or_404(organisation_id)
    
    # Super admins can remove anyone, org admins can remove users from their org
    if not (current_user.is_super_admin or 
            current_user.can_manage_organisation(organisation_id)):
        raise PermissionError("Insufficient permissions")
    
    organisation.remove_user(user_id)
    return True

def assign_user_to_website(user_id, website_id, role='website_viewer'):
    """Assign a user to a website with a specific role."""
    if not current_user.is_authenticated:
        raise PermissionError("Authentication required")
    
    from app.models import User, Website
    
    user = User.query.get_or_404(user_id)
    website = Website.query.get_or_404(website_id)
    
    # Super admins and website managers can assign users
    if not (current_user.is_super_admin or 
            current_user.can_manage_website(website_id)):
        raise PermissionError("Insufficient permissions")
    
    website.add_user(user_id, role)
    return True

def remove_user_from_website(user_id, website_id):
    """Remove a user from a website."""
    if not current_user.is_authenticated:
        raise PermissionError("Authentication required")
    
    from app.models import User, Website
    
    user = User.query.get_or_404(user_id)
    website = Website.query.get_or_404(website_id)
    
    # Super admins and website managers can remove users
    if not (current_user.is_super_admin or 
            current_user.can_manage_website(website_id)):
        raise PermissionError("Insufficient permissions")
    
    website.remove_user(user_id)
    return True
