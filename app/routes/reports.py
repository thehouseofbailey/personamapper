from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Persona, CrawlJob, CrawledPage, ContentMapping, Website, CrawlJobPersona
from datetime import datetime, timedelta
import csv
import io

bp = Blueprint('reports', __name__)

@bp.route('/')
@login_required
def dashboard():
    """Reports dashboard with overview charts and statistics."""
    # Get date range and crawl job filter from query parameters
    days = request.args.get('days', 30, type=int)
    selected_crawl_job_id = request.args.get('crawl_job_id', type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get accessible website IDs for the current user (including via organization access)
    accessible_websites = current_user.get_accessible_websites()
    accessible_website_ids = [w.id for w in accessible_websites]
    
    # Get available crawl jobs for filter dropdown
    if accessible_website_ids:
        available_crawl_jobs = CrawlJob.query.filter(
            CrawlJob.website_id.in_(accessible_website_ids)
        ).order_by(CrawlJob.name).all()
    else:
        available_crawl_jobs = []
    
    # Apply crawl job filter if selected
    crawl_job_filter = None
    if selected_crawl_job_id and accessible_website_ids:
        crawl_job_filter = CrawlJob.query.filter(
            db.and_(
                CrawlJob.id == selected_crawl_job_id,
                CrawlJob.website_id.in_(accessible_website_ids)
            )
        ).first()
    
    # If user has no website access, return empty stats
    if not accessible_website_ids:
        stats = {
            'total_personas': 0,
            'total_crawl_jobs': 0,
            'total_pages_crawled': 0,
            'total_mappings': 0,
            'high_confidence_mappings': 0
        }
    else:
        # Build base queries with website filtering
        if crawl_job_filter:
            # Filter by specific crawl job
            crawl_job_ids = [crawl_job_filter.id]
            stats = {
                'total_personas': db.session.query(Persona).join(CrawlJobPersona).filter(
                    db.and_(
                        Persona.is_active == True,
                        CrawlJobPersona.crawl_job_id == crawl_job_filter.id
                    )
                ).count(),
                'total_crawl_jobs': 1,  # Only the selected crawl job
                'total_pages_crawled': CrawledPage.query.filter(
                    CrawledPage.crawl_job_id == crawl_job_filter.id
                ).count(),
                'total_mappings': ContentMapping.query.join(CrawledPage).filter(
                    db.and_(
                        ContentMapping.is_active == True,
                        CrawledPage.crawl_job_id == crawl_job_filter.id
                    )
                ).count(),
                'high_confidence_mappings': ContentMapping.query.join(CrawledPage).filter(
                    db.and_(
                        ContentMapping.confidence_score >= 0.8,
                        ContentMapping.is_active == True,
                        CrawledPage.crawl_job_id == crawl_job_filter.id
                    )
                ).count()
            }
        else:
            # Overall statistics filtered by accessible websites
            stats = {
                'total_personas': Persona.query.filter(
                    db.and_(
                        Persona.is_active == True,
                        Persona.website_id.in_(accessible_website_ids)
                    )
                ).count(),
                'total_crawl_jobs': CrawlJob.query.filter(
                    CrawlJob.website_id.in_(accessible_website_ids)
                ).count(),
                'total_pages_crawled': CrawledPage.query.join(CrawlJob).filter(
                    CrawlJob.website_id.in_(accessible_website_ids)
                ).count(),
                'total_mappings': ContentMapping.query.join(CrawledPage).join(CrawlJob).filter(
                    db.and_(
                        ContentMapping.is_active == True,
                        CrawlJob.website_id.in_(accessible_website_ids)
                    )
                ).count(),
                'high_confidence_mappings': ContentMapping.query.join(CrawledPage).join(CrawlJob).filter(
                    db.and_(
                        ContentMapping.confidence_score >= 0.8,
                        ContentMapping.is_active == True,
                        CrawlJob.website_id.in_(accessible_website_ids)
                    )
                ).count()
            }
    
    # Persona mapping distribution filtered by accessible websites and optionally by crawl job
    if accessible_website_ids:
        persona_query = db.session.query(
            Persona.title,
            db.func.count(ContentMapping.id).label('mapping_count'),
            db.func.avg(ContentMapping.confidence_score).label('avg_confidence')
        ).join(
            ContentMapping, Persona.id == ContentMapping.persona_id
        ).join(
            CrawledPage, ContentMapping.page_id == CrawledPage.id
        ).join(
            CrawlJob, CrawledPage.crawl_job_id == CrawlJob.id
        )
        
        # Base filters
        filters = [
            Persona.is_active == True,
            ContentMapping.is_active == True,
            ContentMapping.created_at >= start_date,
            Persona.website_id.in_(accessible_website_ids)
        ]
        
        # Add crawl job filter if selected
        if crawl_job_filter:
            filters.append(CrawlJob.id == crawl_job_filter.id)
        else:
            filters.append(CrawlJob.website_id.in_(accessible_website_ids))
        
        persona_stats = persona_query.filter(db.and_(*filters)).group_by(
            Persona.id, Persona.title
        ).order_by(db.desc('mapping_count')).all()
    else:
        persona_stats = []
    
    # Crawl job performance filtered by accessible websites and optionally by specific crawl job
    if accessible_website_ids:
        if crawl_job_filter:
            # Show only the selected crawl job
            job_stats = db.session.query(
                CrawlJob.name,
                CrawlJob.pages_crawled,
                CrawlJob.pages_mapped,
                CrawlJob.status,
                CrawlJob.last_run_at
            ).filter(CrawlJob.id == crawl_job_filter.id).all()
        else:
            # Show all accessible crawl jobs
            job_stats = db.session.query(
                CrawlJob.name,
                CrawlJob.pages_crawled,
                CrawlJob.pages_mapped,
                CrawlJob.status,
                CrawlJob.last_run_at
            ).filter(
                CrawlJob.website_id.in_(accessible_website_ids)
            ).order_by(CrawlJob.pages_crawled.desc()).limit(10).all()
    else:
        job_stats = []
    
    # Daily mapping trends filtered by accessible websites and optionally by crawl job
    if accessible_website_ids:
        daily_query = db.session.query(
            db.func.date(ContentMapping.created_at).label('date'),
            db.func.count(ContentMapping.id).label('count')
        ).join(
            CrawledPage, ContentMapping.page_id == CrawledPage.id
        ).join(
            CrawlJob, CrawledPage.crawl_job_id == CrawlJob.id
        )
        
        # Base filters for daily mappings
        daily_filters = [
            ContentMapping.is_active == True,
            ContentMapping.created_at >= start_date
        ]
        
        # Add crawl job filter if selected
        if crawl_job_filter:
            daily_filters.append(CrawlJob.id == crawl_job_filter.id)
        else:
            daily_filters.append(CrawlJob.website_id.in_(accessible_website_ids))
        
        daily_mappings = daily_query.filter(db.and_(*daily_filters)).group_by(
            db.func.date(ContentMapping.created_at)
        ).order_by('date').all()
    else:
        daily_mappings = []
    
    # Confidence score distribution filtered by accessible websites and optionally by crawl job
    if accessible_website_ids:
        confidence_query = db.session.query(
            db.case(
                (ContentMapping.confidence_score >= 0.9, 'Very High (0.9+)'),
                (ContentMapping.confidence_score >= 0.7, 'High (0.7-0.9)'),
                (ContentMapping.confidence_score >= 0.5, 'Medium (0.5-0.7)'),
                (ContentMapping.confidence_score >= 0.3, 'Low (0.3-0.5)'),
                else_='Very Low (<0.3)'
            ).label('confidence_range'),
            db.func.count(ContentMapping.id).label('count')
        ).join(
            CrawledPage, ContentMapping.page_id == CrawledPage.id
        ).join(
            CrawlJob, CrawledPage.crawl_job_id == CrawlJob.id
        )
        
        # Base filters for confidence distribution
        confidence_filters = [
            ContentMapping.is_active == True,
            ContentMapping.created_at >= start_date
        ]
        
        # Add crawl job filter if selected
        if crawl_job_filter:
            confidence_filters.append(CrawlJob.id == crawl_job_filter.id)
        else:
            confidence_filters.append(CrawlJob.website_id.in_(accessible_website_ids))
        
        confidence_distribution = confidence_query.filter(db.and_(*confidence_filters)).group_by('confidence_range').all()
    else:
        confidence_distribution = []
    
    # Get website names for context
    website_names = [w.name for w in accessible_websites]
    
    return render_template('reports/dashboard.html',
                         stats=stats,
                         persona_stats=persona_stats,
                         job_stats=job_stats,
                         daily_mappings=daily_mappings,
                         confidence_distribution=confidence_distribution,
                         days=days,
                         is_super_admin=current_user.is_super_admin,
                         accessible_websites=website_names,
                         available_crawl_jobs=available_crawl_jobs,
                         selected_crawl_job_id=selected_crawl_job_id,
                         selected_crawl_job=crawl_job_filter)

@bp.route('/personas')
@login_required
def persona_report():
    """Detailed persona performance report."""
    # Get accessible website IDs for the current user (including via organization access)
    accessible_websites = current_user.get_accessible_websites()
    accessible_website_ids = [w.id for w in accessible_websites]
    
    # Get all active personas with their statistics, filtered by accessible websites
    personas_data = []
    
    if accessible_website_ids:
        personas_query = Persona.query.filter(
            db.and_(
                Persona.is_active == True,
                Persona.website_id.in_(accessible_website_ids)
            )
        ).all()
    else:
        personas_query = []
    
    for persona in personas_query:
        mappings = persona.content_mappings.filter_by(is_active=True)
        total_mappings = mappings.count()
        
        if total_mappings > 0:
            avg_confidence = mappings.with_entities(
                db.func.avg(ContentMapping.confidence_score)
            ).scalar()
            
            high_confidence_count = mappings.filter(
                ContentMapping.confidence_score >= 0.8
            ).count()
            
            recent_mappings = mappings.filter(
                ContentMapping.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
        else:
            avg_confidence = 0
            high_confidence_count = 0
            recent_mappings = 0
        
        personas_data.append({
            'persona': persona,
            'total_mappings': total_mappings,
            'avg_confidence': round(avg_confidence or 0, 3),
            'high_confidence_count': high_confidence_count,
            'high_confidence_rate': (high_confidence_count / total_mappings * 100) if total_mappings > 0 else 0,
            'recent_mappings': recent_mappings
        })
    
    # Sort by total mappings
    personas_data.sort(key=lambda x: x['total_mappings'], reverse=True)
    
    return render_template('reports/personas.html', personas_data=personas_data)

@bp.route('/crawl-jobs')
@login_required
def crawl_jobs_report():
    """Detailed crawl job performance report."""
    # Get accessible website IDs for the current user (including via organization access)
    accessible_websites = current_user.get_accessible_websites()
    accessible_website_ids = [w.id for w in accessible_websites]
    
    jobs_data = []
    
    if accessible_website_ids:
        jobs_query = CrawlJob.query.filter(
            CrawlJob.website_id.in_(accessible_website_ids)
        ).all()
    else:
        jobs_query = []
    
    for job in jobs_query:
        total_pages = job.crawled_pages.count()
        processed_pages = job.crawled_pages.filter_by(is_processed=True).count()
        
        # Count pages with mappings
        pages_with_mappings = db.session.query(CrawledPage).join(
            ContentMapping, CrawledPage.id == ContentMapping.page_id
        ).filter(
            db.and_(
                CrawledPage.crawl_job_id == job.id,
                ContentMapping.is_active == True
            )
        ).distinct().count()
        
        # Average confidence score for this job's mappings
        avg_confidence = db.session.query(
            db.func.avg(ContentMapping.confidence_score)
        ).join(
            CrawledPage, ContentMapping.page_id == CrawledPage.id
        ).filter(
            db.and_(
                CrawledPage.crawl_job_id == job.id,
                ContentMapping.is_active == True
            )
        ).scalar()
        
        jobs_data.append({
            'job': job,
            'total_pages': total_pages,
            'processed_pages': processed_pages,
            'pages_with_mappings': pages_with_mappings,
            'processing_rate': (processed_pages / total_pages * 100) if total_pages > 0 else 0,
            'mapping_rate': (pages_with_mappings / total_pages * 100) if total_pages > 0 else 0,
            'avg_confidence': round(avg_confidence or 0, 3)
        })
    
    # Sort by total pages crawled
    jobs_data.sort(key=lambda x: x['total_pages'], reverse=True)
    
    return render_template('reports/crawl_jobs.html', jobs_data=jobs_data)

@bp.route('/content-analysis')
@login_required
def content_analysis():
    """Content analysis and mapping insights with filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get accessible website IDs for the current user (including via organization access)
    accessible_websites = current_user.get_accessible_websites()
    accessible_website_ids = [w.id for w in accessible_websites]
    
    # Get filter parameters
    slug_filter = request.args.get('slug', '').strip()
    crawl_job_filter = request.args.get('crawl_job', '', type=str)
    persona_filter = request.args.get('persona', '', type=str)
    
    # If user has no website access, return empty results
    if not accessible_website_ids:
        pages = type('Pages', (), {'items': [], 'total': 0, 'pages': 0, 'page': 1, 'per_page': per_page, 'has_prev': False, 'has_next': False})()
        stats = {'total_pages': 0, 'mapped_pages': 0, 'unmapped_pages': 0, 'mapping_rate': 0}
        method_distribution = []
        crawl_jobs = []
        personas = []
    else:
        # Build base query - only include pages from accessible websites
        pages_query = db.session.query(CrawledPage).options(
            db.joinedload(CrawledPage.crawl_job)
        ).join(CrawlJob).filter(CrawlJob.website_id.in_(accessible_website_ids))
        
        # Apply filters
        if slug_filter:
            pages_query = pages_query.filter(CrawledPage.url.contains(slug_filter))
        
        if crawl_job_filter and crawl_job_filter != 'all':
            if crawl_job_filter.isdigit():
                pages_query = pages_query.filter(CrawledPage.crawl_job_id == int(crawl_job_filter))
        
        if persona_filter and persona_filter != 'all':
            if persona_filter == 'no_mappings':
                # Pages with no mappings
                pages_query = pages_query.outerjoin(ContentMapping).filter(ContentMapping.id.is_(None))
            elif persona_filter == 'with_mappings':
                # Pages with any mappings
                pages_query = pages_query.join(ContentMapping).filter(
                    ContentMapping.is_active == True
                ).distinct()
            elif persona_filter.isdigit():
                # Pages mapped to specific persona
                pages_query = pages_query.join(ContentMapping).filter(
                    db.and_(
                        ContentMapping.persona_id == int(persona_filter),
                        ContentMapping.is_active == True
                    )
                ).distinct()
        
        pages_query = pages_query.order_by(CrawledPage.crawled_at.desc())
        pages = pages_query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get filter options - only from accessible websites
        crawl_jobs = CrawlJob.query.filter(
            CrawlJob.website_id.in_(accessible_website_ids)
        ).order_by(CrawlJob.name).all()
        personas = Persona.query.filter(
            db.and_(
                Persona.is_active == True,
                Persona.website_id.in_(accessible_website_ids)
            )
        ).order_by(Persona.title).all()
        
        # Get mapping method distribution - only from accessible websites
        method_distribution = db.session.query(
            ContentMapping.mapping_method,
            db.func.count(ContentMapping.id).label('count'),
            db.func.avg(ContentMapping.confidence_score).label('avg_confidence')
        ).join(CrawledPage).join(CrawlJob).filter(
            db.and_(
                ContentMapping.is_active == True,
                CrawlJob.website_id.in_(accessible_website_ids)
            )
        ).group_by(ContentMapping.mapping_method).all()
        
        # Get content with no mappings - only from accessible websites
        unmapped_content_count = db.session.query(CrawledPage).join(CrawlJob).outerjoin(
            ContentMapping, CrawledPage.id == ContentMapping.page_id
        ).filter(
            db.and_(
                CrawlJob.website_id.in_(accessible_website_ids),
                ContentMapping.id.is_(None)
            )
        ).count()
        
        # Get total stats - only from accessible websites
        total_pages = db.session.query(CrawledPage).join(CrawlJob).filter(
            CrawlJob.website_id.in_(accessible_website_ids)
        ).count()
        mapped_pages = db.session.query(CrawledPage).join(CrawlJob).join(
            ContentMapping, CrawledPage.id == ContentMapping.page_id
        ).filter(
            db.and_(
                ContentMapping.is_active == True,
                CrawlJob.website_id.in_(accessible_website_ids)
            )
        ).distinct().count()
        
        stats = {
            'total_pages': total_pages,
            'mapped_pages': mapped_pages,
            'unmapped_pages': unmapped_content_count,
            'mapping_rate': (mapped_pages / total_pages * 100) if total_pages > 0 else 0
        }
    
    return render_template('reports/content_analysis.html',
                         pages=pages,
                         method_distribution=method_distribution,
                         stats=stats,
                         crawl_jobs=crawl_jobs,
                         personas=personas,
                         current_filters={
                             'slug': slug_filter,
                             'crawl_job': crawl_job_filter,
                             'persona': persona_filter
                         })

@bp.route('/export/personas')
@login_required
def export_personas():
    """Export persona data as CSV."""
    # Get crawl job filter from query parameters
    selected_crawl_job_id = request.args.get('crawl_job_id', type=int)
    
    # Get accessible website IDs for the current user (including via organization access)
    accessible_websites = current_user.get_accessible_websites()
    accessible_website_ids = [w.id for w in accessible_websites]
    
    # Apply crawl job filter if selected
    crawl_job_filter = None
    if selected_crawl_job_id and accessible_website_ids:
        crawl_job_filter = CrawlJob.query.filter(
            db.and_(
                CrawlJob.id == selected_crawl_job_id,
                CrawlJob.website_id.in_(accessible_website_ids)
            )
        ).first()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Title', 'Description', 'Keywords', 'Total Mappings',
        'High Confidence Mappings', 'Average Confidence', 'Created At'
    ])
    
    # Write data - only for accessible websites
    if accessible_website_ids:
        personas_query = Persona.query.filter(
            db.and_(
                Persona.is_active == True,
                Persona.website_id.in_(accessible_website_ids)
            )
        ).all()
    else:
        personas_query = []
    
    for persona in personas_query:
        mappings = persona.content_mappings.filter_by(is_active=True)
        total_mappings = mappings.count()
        high_confidence = mappings.filter(ContentMapping.confidence_score >= 0.8).count()
        avg_confidence = mappings.with_entities(
            db.func.avg(ContentMapping.confidence_score)
        ).scalar() or 0
        
        writer.writerow([
            persona.id,
            persona.title,
            persona.description,
            persona.keywords,
            total_mappings,
            high_confidence,
            round(avg_confidence, 3),
            persona.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    
    # Include crawl job in filename if filtered
    if crawl_job_filter:
        safe_name = ''.join(c for c in crawl_job_filter.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f'personas_export_{safe_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    else:
        filename = f'personas_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@bp.route('/export/mappings')
@login_required
def export_mappings():
    """Export content mappings as CSV."""
    # Get crawl job filter from query parameters
    selected_crawl_job_id = request.args.get('crawl_job_id', type=int)
    
    # Get accessible website IDs for the current user (including via organization access)
    accessible_websites = current_user.get_accessible_websites()
    accessible_website_ids = [w.id for w in accessible_websites]
    
    # Apply crawl job filter if selected
    crawl_job_filter = None
    if selected_crawl_job_id and accessible_website_ids:
        crawl_job_filter = CrawlJob.query.filter(
            db.and_(
                CrawlJob.id == selected_crawl_job_id,
                CrawlJob.website_id.in_(accessible_website_ids)
            )
        ).first()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Mapping ID', 'Page URL', 'Page Title', 'Persona Title',
        'Confidence Score', 'Confidence Level', 'Mapping Method',
        'Mapping Reason', 'Is Verified', 'Created At'
    ])
    
    # Write data - only for accessible websites, optionally filtered by crawl job
    if accessible_website_ids:
        mappings_query = db.session.query(
            ContentMapping, CrawledPage, Persona
        ).join(
            CrawledPage, ContentMapping.page_id == CrawledPage.id
        ).join(
            CrawlJob, CrawledPage.crawl_job_id == CrawlJob.id
        ).join(
            Persona, ContentMapping.persona_id == Persona.id
        )
        
        # Base filters
        filters = [
            ContentMapping.is_active == True,
            Persona.is_active == True,
            Persona.website_id.in_(accessible_website_ids)
        ]
        
        # Add crawl job filter if selected
        if crawl_job_filter:
            filters.append(CrawlJob.id == crawl_job_filter.id)
        else:
            filters.append(CrawlJob.website_id.in_(accessible_website_ids))
        
        mappings = mappings_query.filter(db.and_(*filters)).order_by(ContentMapping.confidence_score.desc()).all()
    else:
        mappings = []
    
    for mapping, page, persona in mappings:
        writer.writerow([
            mapping.id,
            page.url,
            page.title or '',
            persona.title,
            round(mapping.confidence_score, 3),
            mapping.get_confidence_level(),
            mapping.mapping_method,
            mapping.mapping_reason or '',
            mapping.is_verified,
            mapping.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    
    # Include crawl job in filename if filtered
    if crawl_job_filter:
        safe_name = ''.join(c for c in crawl_job_filter.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f'mappings_export_{safe_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    else:
        filename = f'mappings_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics."""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = {
        'total_personas': Persona.query.filter_by(is_active=True).count(),
        'total_crawl_jobs': CrawlJob.query.count(),
        'total_pages_crawled': CrawledPage.query.count(),
        'total_mappings': ContentMapping.query.filter_by(is_active=True).count(),
        'high_confidence_mappings': ContentMapping.query.filter(
            db.and_(
                ContentMapping.confidence_score >= 0.8,
                ContentMapping.is_active == True
            )
        ).count(),
        'recent_mappings': ContentMapping.query.filter(
            db.and_(
                ContentMapping.is_active == True,
                ContentMapping.created_at >= start_date
            )
        ).count()
    }
    
    return jsonify(stats)
