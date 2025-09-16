from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app import db
from app.models import CrawlJob, CrawledPage, ContentMapping, CrawlUrl
from app.services.web_crawler import crawler_manager
from datetime import datetime

bp = Blueprint('crawler', __name__)

@bp.route('/')
@login_required
def list_crawl_jobs():
    """List all crawl jobs."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    crawl_jobs = CrawlJob.query.order_by(
        CrawlJob.created_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crawler/list.html', crawl_jobs=crawl_jobs)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_crawl_job():
    """Create a new crawl job."""
    from flask_login import current_user
    from app.models import Website, Persona
    
    # Get website_id from query parameter (for pre-selection)
    website_id = request.args.get('website_id', type=int)
    
    # Get user's accessible websites (filtered by organization)
    accessible_websites = []
    user_orgs = current_user.get_organisations()
    for org in user_orgs:
        accessible_websites.extend(org.get_websites())
    
    # Remove duplicates
    accessible_websites = list({w.id: w for w in accessible_websites}.values())
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        base_url = request.form.get('base_url', '').strip()
        include_patterns = request.form.get('include_patterns', '').strip()
        exclude_patterns = request.form.get('exclude_patterns', '').strip()
        max_pages = request.form.get('max_pages', type=int)
        crawl_mode = request.form.get('crawl_mode', 'incremental').strip()
        schedule = request.form.get('schedule', '').strip()
        selected_website_id = request.form.get('website_id', type=int)
        selected_persona_ids = request.form.getlist('persona_ids')
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Job name is required.')
        elif len(name) > 200:
            errors.append('Job name must be less than 200 characters.')
        
        if not base_url:
            errors.append('Base URL is required.')
        elif not (base_url.startswith('http://') or base_url.startswith('https://')):
            errors.append('Base URL must start with http:// or https://')
        
        if not selected_website_id:
            errors.append('Website selection is required.')
        elif selected_website_id not in [w.id for w in accessible_websites]:
            errors.append('You do not have access to the selected website.')
        
        if not max_pages or max_pages < 1:
            errors.append('Max pages must be at least 1.')
        elif max_pages > 10000:
            errors.append('Max pages cannot exceed 10,000.')
        
        # Check if name already exists
        if CrawlJob.query.filter_by(name=name).first():
            errors.append('A crawl job with this name already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            
            # Get personas for error case
            available_personas = []
            if selected_website_id and selected_website_id in [w.id for w in accessible_websites]:
                selected_website = next((w for w in accessible_websites if w.id == selected_website_id), None)
                if selected_website:
                    available_personas = selected_website.get_personas()
            else:
                for org in user_orgs:
                    available_personas.extend(org.get_personas())
                available_personas = list({p.id: p for p in available_personas}.values())
            
            return render_template('crawler/create.html',
                                 name=name,
                                 base_url=base_url,
                                 include_patterns=include_patterns,
                                 exclude_patterns=exclude_patterns,
                                 max_pages=max_pages,
                                 schedule=schedule,
                                 accessible_websites=accessible_websites,
                                 available_personas=available_personas,
                                 selected_website_id=selected_website_id,
                                 selected_persona_ids=selected_persona_ids)
        
        # Create new crawl job
        crawl_job = CrawlJob(
            name=name,
            base_url=base_url,
            website_id=selected_website_id,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_pages=max_pages,
            crawl_mode=crawl_mode,
            schedule=schedule if schedule else None
        )
        
        db.session.add(crawl_job)
        db.session.flush()  # Get the ID before committing
        
        # Add persona assignments
        for persona_id in selected_persona_ids:
            if persona_id:  # Skip empty values
                crawl_job.add_persona(int(persona_id))
        
        db.session.commit()
        
        flash(f'Crawl job "{name}" created successfully!', 'success')
        return redirect(url_for('crawler.view_crawl_job', id=crawl_job.id))
    
    # Get personas for selected website (if any) for the GET request
    available_personas = []
    if website_id and website_id in [w.id for w in accessible_websites]:
        selected_website = next((w for w in accessible_websites if w.id == website_id), None)
        if selected_website:
            available_personas = selected_website.get_personas()
    else:
        # If no specific website, get all personas from user's organizations
        for org in user_orgs:
            available_personas.extend(org.get_personas())
        # Remove duplicates
        available_personas = list({p.id: p for p in available_personas}.values())
    
    return render_template('crawler/create.html',
                         accessible_websites=accessible_websites,
                         available_personas=available_personas,
                         selected_website_id=website_id)

@bp.route('/<int:id>')
@login_required
def view_crawl_job(id):
    """View a specific crawl job and its results."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    # Get recent crawled pages
    recent_pages = crawl_job.crawled_pages.order_by(
        CrawledPage.crawled_at.desc()
    ).limit(10).all()
    
    # Get crawl statistics
    total_pages = crawl_job.crawled_pages.count()
    processed_pages = crawl_job.crawled_pages.filter_by(is_processed=True).count()
    discovered_urls = crawl_job.crawl_urls.count()
    pages_with_mappings = db.session.query(CrawledPage).join(
        ContentMapping, CrawledPage.id == ContentMapping.page_id
    ).filter(
        db.and_(
            CrawledPage.crawl_job_id == id,
            ContentMapping.is_active == True
        )
    ).distinct().count()
    
    stats = {
        'total_pages': total_pages,
        'processed_pages': processed_pages,
        'discovered_urls': discovered_urls,
        'pages_with_mappings': pages_with_mappings,
        'processing_rate': (processed_pages / total_pages * 100) if total_pages > 0 else 0,
        'mapping_rate': (pages_with_mappings / total_pages * 100) if total_pages > 0 else 0
    }
    
    return render_template('crawler/view.html',
                         crawl_job=crawl_job,
                         recent_pages=recent_pages,
                         stats=stats)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_crawl_job(id):
    """Edit an existing crawl job."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    if crawl_job.is_running():
        flash('Cannot edit a crawl job that is currently running.', 'error')
        return redirect(url_for('crawler.view_crawl_job', id=id))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        base_url = request.form.get('base_url', '').strip()
        include_patterns = request.form.get('include_patterns', '').strip()
        exclude_patterns = request.form.get('exclude_patterns', '').strip()
        max_pages = request.form.get('max_pages', type=int)
        schedule = request.form.get('schedule', '').strip()
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Job name is required.')
        elif len(name) > 200:
            errors.append('Job name must be less than 200 characters.')
        
        if not base_url:
            errors.append('Base URL is required.')
        elif not (base_url.startswith('http://') or base_url.startswith('https://')):
            errors.append('Base URL must start with http:// or https://')
        
        if not max_pages or max_pages < 1:
            errors.append('Max pages must be at least 1.')
        elif max_pages > 10000:
            errors.append('Max pages cannot exceed 10,000.')
        
        # Check if name already exists (excluding current job)
        existing_job = CrawlJob.query.filter(
            db.and_(
                CrawlJob.name == name,
                CrawlJob.id != id
            )
        ).first()
        
        if existing_job:
            errors.append('A crawl job with this name already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('crawler/edit.html',
                                 crawl_job=crawl_job,
                                 name=name,
                                 base_url=base_url,
                                 include_patterns=include_patterns,
                                 exclude_patterns=exclude_patterns,
                                 max_pages=max_pages,
                                 schedule=schedule)
        
        # Update crawl job
        crawl_job.name = name
        crawl_job.base_url = base_url
        crawl_job.include_patterns = include_patterns
        crawl_job.exclude_patterns = exclude_patterns
        crawl_job.max_pages = max_pages
        crawl_job.schedule = schedule if schedule else None
        
        db.session.commit()
        
        flash(f'Crawl job "{name}" updated successfully!', 'success')
        return redirect(url_for('crawler.view_crawl_job', id=crawl_job.id))
    
    return render_template('crawler/edit.html', crawl_job=crawl_job)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_crawl_job(id):
    """Delete a crawl job and all its data."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    if crawl_job.is_running():
        flash('Cannot delete a crawl job that is currently running.', 'error')
        return redirect(url_for('crawler.view_crawl_job', id=id))
    
    job_name = crawl_job.name
    
    # Delete all related data (cascading delete should handle this)
    db.session.delete(crawl_job)
    db.session.commit()
    
    flash(f'Crawl job "{job_name}" and all its data have been deleted.', 'success')
    return redirect(url_for('crawler.list_crawl_jobs'))

@bp.route('/<int:id>/start', methods=['POST'])
@login_required
def start_crawl_job(id):
    """Start a crawl job manually."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    if crawl_job.is_running() or crawler_manager.is_crawl_running(id):
        flash('This crawl job is already running.', 'warning')
        return redirect(url_for('crawler.view_crawl_job', id=id))
    
    # Start the actual crawling process
    success = crawler_manager.start_crawl_job(id)
    
    if success:
        flash(f'Crawl job "{crawl_job.name}" has been started. Check the logs for progress.', 'success')
    else:
        flash(f'Failed to start crawl job "{crawl_job.name}". Check the logs for details.', 'error')
    
    return redirect(url_for('crawler.view_crawl_job', id=id))

@bp.route('/<int:id>/stop', methods=['POST'])
@login_required
def stop_crawl_job(id):
    """Stop a running crawl job."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    if not crawl_job.is_running() and not crawler_manager.is_crawl_running(id):
        flash('This crawl job is not currently running.', 'warning')
        return redirect(url_for('crawler.view_crawl_job', id=id))
    
    # Stop the actual crawling process
    success = crawler_manager.stop_crawl_job(id)
    
    if success:
        flash(f'Crawl job "{crawl_job.name}" has been stopped.', 'info')
    else:
        # Fallback: update status manually
        crawl_job.update_status('inactive')
        db.session.commit()
        flash(f'Crawl job "{crawl_job.name}" has been stopped.', 'info')
    
    return redirect(url_for('crawler.view_crawl_job', id=id))

@bp.route('/<int:id>/reset', methods=['POST'])
@login_required
def reset_crawl_job(id):
    """Reset a stuck crawl job that appears to be running but isn't."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    # Force reset the status
    crawl_job.update_status('inactive')
    db.session.commit()
    
    # Clean up any stale crawler manager entries
    if crawler_manager.is_crawl_running(id):
        crawler_manager.stop_crawl_job(id)
    
    flash(f'Crawl job "{crawl_job.name}" has been reset and is now available to run.', 'success')
    return redirect(url_for('crawler.view_crawl_job', id=id))

@bp.route('/<int:id>/clear-data', methods=['POST'])
@login_required
def clear_crawl_data(id):
    """Clear all crawled pages and mappings for a crawl job, keeping the job configuration."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    if crawl_job.is_running():
        flash('Cannot clear data for a crawl job that is currently running. Stop the crawl first.', 'error')
        return redirect(url_for('crawler.view_crawl_job', id=id))
    
    try:
        # Get counts before deletion for reporting
        pages_count = crawl_job.crawled_pages.count()
        urls_count = crawl_job.crawl_urls.count()
        
        # Count mappings associated with this crawl's pages
        mappings_count = db.session.query(ContentMapping).join(
            CrawledPage, ContentMapping.page_id == CrawledPage.id
        ).filter(CrawledPage.crawl_job_id == id).count()
        
        # Delete all content mappings for pages in this crawl
        # This needs to be done first due to foreign key constraints
        db.session.query(ContentMapping).filter(
            ContentMapping.page_id.in_(
                db.session.query(CrawledPage.id).filter(CrawledPage.crawl_job_id == id)
            )
        ).delete(synchronize_session=False)
        
        # Delete all crawled pages for this job
        CrawledPage.query.filter_by(crawl_job_id=id).delete()
        
        # Delete all discovered URLs for this job
        CrawlUrl.query.filter_by(crawl_job_id=id).delete()
        
        # Reset crawl job statistics
        crawl_job.pages_crawled = 0
        crawl_job.pages_processed = 0
        crawl_job.last_run_at = None
        crawl_job.update_status('inactive')
        
        db.session.commit()
        
        flash(f'Cleared {pages_count} pages, {mappings_count} persona mappings, and {urls_count} discovered URLs from crawl job "{crawl_job.name}". The job configuration has been preserved and can be run again.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing crawl data: {str(e)}', 'error')
    
    return redirect(url_for('crawler.view_crawl_job', id=id))

@bp.route('/<int:id>/pages')
@login_required
def crawl_job_pages(id):
    """View all crawled pages for a specific job."""
    crawl_job = CrawlJob.query.get_or_404(id)
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    pages = crawl_job.crawled_pages.order_by(
        CrawledPage.crawled_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('crawler/pages.html', 
                         crawl_job=crawl_job, 
                         pages=pages)

@bp.route('/pages/<int:id>')
@login_required
def view_crawled_page(id):
    """View details of a specific crawled page."""
    page = CrawledPage.query.get_or_404(id)
    
    # Get current active mappings for this page
    current_mappings = page.content_mappings.filter_by(is_active=True).order_by(
        ContentMapping.confidence_score.desc()
    ).all()
    
    # Get historical data for chart - all mappings for this page ordered by crawl timestamp
    historical_mappings = ContentMapping.query.filter_by(page_id=page.id).order_by(
        ContentMapping.crawl_timestamp.asc()
    ).all()
    
    # Prepare chart data - group by persona and crawl timestamp
    chart_data = {}
    crawl_timestamps = set()
    
    for mapping in historical_mappings:
        if mapping.crawl_timestamp:
            persona_title = mapping.persona.title
            timestamp = mapping.crawl_timestamp.isoformat()
            
            if persona_title not in chart_data:
                chart_data[persona_title] = []
            
            chart_data[persona_title].append({
                'x': timestamp,
                'y': round(mapping.confidence_score * 100, 1),
                'is_active': mapping.is_active
            })
            
            crawl_timestamps.add(timestamp)
    
    # Sort timestamps for consistent chart display
    sorted_timestamps = sorted(list(crawl_timestamps))
    
    return render_template('crawler/page_detail.html', 
                         page=page, 
                         mappings=current_mappings,
                         chart_data=chart_data,
                         crawl_timestamps=sorted_timestamps,
                         has_historical_data=len(historical_mappings) > 0 and len(chart_data) > 0)

@bp.route('/pages/<int:id>/recrawl', methods=['POST'])
@login_required
def recrawl_page(id):
    """Re-crawl a specific page to update its content and mappings."""
    page = CrawledPage.query.get_or_404(id)
    
    try:
        # Import here to avoid circular imports
        from app.services.web_crawler import WebCrawler
        from app.services.content_analyzer import ContentAnalyzer
        from app.models import Persona
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        
        # Create a temporary crawler instance for this single page
        crawler = WebCrawler(page.crawl_job_id)
        crawler.load_crawl_job()
        
        # Fetch the page
        result = crawler.fetch_page(page.url)
        if not result:
            flash(f'Failed to fetch page: {page.url}', 'error')
            return redirect(url_for('crawler.view_crawled_page', id=id))
        
        response, soup = result
        
        # Extract new content
        content_data = crawler.extract_content(soup, page.url)
        
        # Update the page with new content
        page.title = content_data['title']
        page.content = content_data['content']
        page.word_count = content_data['word_count']
        page.crawled_at = datetime.utcnow()
        page.status_code = response.status_code
        page.is_processed = True
        
        # Remove existing mappings for this page
        existing_mappings = ContentMapping.query.filter_by(page_id=page.id).all()
        for mapping in existing_mappings:
            db.session.delete(mapping)
        
        # Re-analyze content and create new mappings
        content_analyzer = ContentAnalyzer()
        personas = Persona.query.filter_by(is_active=True).all()
        new_mappings_count = 0
        
        for persona in personas:
            mapping_result = content_analyzer.analyze_content_for_persona(
                page.content, persona
            )
            
            if mapping_result['should_map']:
                mapping = ContentMapping(
                    persona_id=persona.id,
                    page_id=page.id,
                    confidence_score=mapping_result['confidence'],
                    mapping_reason=mapping_result['reason'],
                    mapping_method='manual_recrawl'
                )
                db.session.add(mapping)
                new_mappings_count += 1
        
        db.session.commit()
        
        flash(f'Page re-crawled successfully! Created {new_mappings_count} new persona mappings.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error re-crawling page: {str(e)}', 'error')
    
    return redirect(url_for('crawler.view_crawled_page', id=id))

@bp.route('/api/jobs')
@login_required
def api_list_crawl_jobs():
    """API endpoint to get all crawl jobs as JSON."""
    jobs = CrawlJob.query.order_by(CrawlJob.created_at.desc()).all()
    return jsonify([job.to_dict() for job in jobs])

@bp.route('/api/jobs/<int:id>')
@login_required
def api_get_crawl_job(id):
    """API endpoint to get crawl job data as JSON."""
    job = CrawlJob.query.get_or_404(id)
    return jsonify(job.to_dict())
