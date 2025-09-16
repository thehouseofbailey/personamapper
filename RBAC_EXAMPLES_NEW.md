# RBAC Implementation Examples

Example of how to update existing routes to use the new RBAC system.

This shows the before/after of updating the crawler routes to support the new role-based access control with organisations and websites.

**NOTE**: This is a documentation file with example code. It is not meant to be executed. The variables and imports shown are for illustration purposes only.

## Required Imports

```python
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import CrawlJob, Website

bp = Blueprint('crawler', __name__)
```

## BEFORE: Simple role-based checks

### Example Route - List Crawl Jobs (Old)

```python
@bp.route('/')
@login_required
def list_crawl_jobs():
    """List all crawl jobs."""
    # OLD: Show all crawl jobs to any authenticated user
    crawl_jobs = CrawlJob.query.order_by(CrawlJob.created_at.desc()).all()
    return render_template('crawler/list.html', crawl_jobs=crawl_jobs)
```

### Example Route - Create Crawl Job (Old)

```python
@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_crawl_job():
    """Create a new crawl job."""
    # OLD: Check if user can create crawls (admin/editor only)
    if not current_user.can_create_crawls():
        flash('You do not have permission to create crawl jobs.', 'error')
        return redirect(url_for('crawler.list_crawl_jobs'))
    
    # ... rest of create logic
```

### Example Route - View Crawl Job (Old)

```python
@bp.route('/<int:id>')
@login_required
def view_crawl_job(id):
    """View crawl job details."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    # OLD: No additional permission check - all users can view
    return render_template('crawler/view.html', crawl_job=crawl_job)
```

## AFTER: RBAC with organisations and websites

### Updated Imports

```python
from flask_login import login_required, current_user
from app.auth.permissions import (
    get_user_accessible_crawl_jobs, 
    crawl_job_access_required,
    website_access_required
)
```

### Example Route - List Crawl Jobs (New)

```python
@bp.route('/')
@login_required
def list_crawl_jobs():
    """List crawl jobs the user has access to."""
    # NEW: Only show crawl jobs from websites the user can access
    if current_user.is_super_admin:
        crawl_jobs = CrawlJob.query.order_by(CrawlJob.created_at.desc()).all()
    else:
        # Get crawl jobs from accessible websites only
        accessible_websites = current_user.get_accessible_websites()
        website_ids = [w.id for w in accessible_websites]
        crawl_jobs = CrawlJob.query.filter(
            CrawlJob.website_id.in_(website_ids)
        ).order_by(CrawlJob.created_at.desc()).all()
    
    return render_template('crawler/list.html', crawl_jobs=crawl_jobs)
```

### Example Route - Create Crawl Job (New)

```python
@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_crawl_job():
    """Create a new crawl job."""
    website_id = request.args.get('website_id', type=int)
    
    # NEW: Check website-specific permissions
    if not website_id:
        flash('Please select a website for this crawl job.', 'error')
        return redirect(url_for('websites.list_websites'))
    
    if not current_user.can_manage_website(website_id):
        flash('You do not have permission to create crawl jobs for this website.', 'error')
        return redirect(url_for('websites.view_website', id=website_id))
    
    if request.method == 'POST':
        # Form validation and processing
        errors = []
        if not errors:
            crawl_job = CrawlJob(
                name=name,
                base_url=base_url,
                website_id=website_id,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                max_pages=max_pages or 100,
                crawl_mode=crawl_mode,
                schedule=schedule if schedule else None
            )
            
            db.session.add(crawl_job)
            db.session.commit()
            
            flash(f'Crawl job "{name}" created successfully!', 'success')
            return redirect(url_for('crawler.view_crawl_job', id=crawl_job.id))
    
    return render_template('crawler/create.html', website_id=website_id)
```

### Example Route - View Crawl Job (New)

```python
@bp.route('/<int:id>')
@login_required
def view_crawl_job(id):
    """View crawl job details."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    # NEW: Check if user can view this specific crawl job
    if not current_user.can_view_crawl_job(crawl_job):
        flash('You do not have permission to view this crawl job.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('crawler/view.html', crawl_job=crawl_job)
```

## Key Changes Summary

### 1. Data Filtering
- **Before**: Showed all data to authenticated users
- **After**: Filter data based on user's website/organization access

### 2. Permission Checks
- **Before**: Simple role-based checks (`can_create_crawls()`)
- **After**: Granular permissions (`can_manage_website()`, `can_view_crawl_job()`)

### 3. Context Awareness
- **Before**: Global operations without context
- **After**: Website-specific operations with proper context

### 4. Access Control Methods

#### User Model Extensions
```python
def get_accessible_websites(self):
    """Get all websites this user has access to (direct or via organization)."""
    if self.is_super_admin:
        return Website.query.all()
    
    accessible_websites = []
    all_websites = Website.query.all()
    
    for website in all_websites:
        if self.has_website_access(website.id):
            accessible_websites.append(website)
    
    return accessible_websites

def can_view_crawl_job(self, crawl_job):
    """Check if user can view a specific crawl job."""
    if self.is_super_admin:
        return True
    
    if hasattr(crawl_job, 'website_id') and crawl_job.website_id:
        return self.can_view_website(crawl_job.website_id)
    
    return False

def can_manage_website(self, website_id):
    """Check if user can manage a specific website."""
    return self.is_super_admin or self.is_website_manager(website_id)
```

## Template Updates

### Navigation Updates
```html
<!-- Before: Show crawler in main navigation -->
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('crawler.list_crawl_jobs') }}">
        <i class="bi bi-search"></i> Crawler
    </a>
</li>

<!-- After: Show crawler contextually within websites -->
<!-- Removed from main navigation, now accessible via website management -->
```

### Website-Specific Context
```html
<!-- In website view template -->
<div class="card">
    <div class="card-header">
        <h5>Crawl Jobs</h5>
        {% if current_user.can_manage_website(website.id) %}
        <a href="{{ url_for('crawler.create_crawl_job', website_id=website.id) }}" 
           class="btn btn-sm btn-success">
            <i class="bi bi-plus"></i> New Crawl Job
        </a>
        {% endif %}
    </div>
    <div class="card-body">
        {% for job in website.crawl_jobs %}
            <!-- Display crawl jobs for this website -->
        {% endfor %}
    </div>
</div>
```

This approach ensures proper data isolation and maintains security boundaries while providing a better user experience through contextual access controls.
