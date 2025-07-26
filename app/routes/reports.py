from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required
from app import db
from app.models import Persona, CrawlJob, CrawledPage, ContentMapping
from datetime import datetime, timedelta
import csv
import io

bp = Blueprint('reports', __name__)

@bp.route('/')
@login_required
def dashboard():
    """Reports dashboard with overview charts and statistics."""
    # Get date range from query parameters
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Overall statistics
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
        ).count()
    }
    
    # Persona mapping distribution
    persona_stats = db.session.query(
        Persona.title,
        db.func.count(ContentMapping.id).label('mapping_count'),
        db.func.avg(ContentMapping.confidence_score).label('avg_confidence')
    ).join(
        ContentMapping, Persona.id == ContentMapping.persona_id
    ).filter(
        db.and_(
            Persona.is_active == True,
            ContentMapping.is_active == True,
            ContentMapping.created_at >= start_date
        )
    ).group_by(Persona.id, Persona.title).order_by(
        db.desc('mapping_count')
    ).all()
    
    # Crawl job performance
    job_stats = db.session.query(
        CrawlJob.name,
        CrawlJob.pages_crawled,
        CrawlJob.pages_mapped,
        CrawlJob.status,
        CrawlJob.last_run_at
    ).order_by(CrawlJob.pages_crawled.desc()).limit(10).all()
    
    # Daily mapping trends
    daily_mappings = db.session.query(
        db.func.date(ContentMapping.created_at).label('date'),
        db.func.count(ContentMapping.id).label('count')
    ).filter(
        db.and_(
            ContentMapping.is_active == True,
            ContentMapping.created_at >= start_date
        )
    ).group_by(db.func.date(ContentMapping.created_at)).order_by('date').all()
    
    # Confidence score distribution
    confidence_distribution = db.session.query(
        db.case(
            (ContentMapping.confidence_score >= 0.9, 'Very High (0.9+)'),
            (ContentMapping.confidence_score >= 0.7, 'High (0.7-0.9)'),
            (ContentMapping.confidence_score >= 0.5, 'Medium (0.5-0.7)'),
            (ContentMapping.confidence_score >= 0.3, 'Low (0.3-0.5)'),
            else_='Very Low (<0.3)'
        ).label('confidence_range'),
        db.func.count(ContentMapping.id).label('count')
    ).filter(
        db.and_(
            ContentMapping.is_active == True,
            ContentMapping.created_at >= start_date
        )
    ).group_by('confidence_range').all()
    
    return render_template('reports/dashboard.html',
                         stats=stats,
                         persona_stats=persona_stats,
                         job_stats=job_stats,
                         daily_mappings=daily_mappings,
                         confidence_distribution=confidence_distribution,
                         days=days)

@bp.route('/personas')
@login_required
def persona_report():
    """Detailed persona performance report."""
    # Get all active personas with their statistics
    personas_data = []
    
    for persona in Persona.query.filter_by(is_active=True).all():
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
    jobs_data = []
    
    for job in CrawlJob.query.all():
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
    
    # Get filter parameters
    slug_filter = request.args.get('slug', '').strip()
    crawl_job_filter = request.args.get('crawl_job', '', type=str)
    persona_filter = request.args.get('persona', '', type=str)
    
    # Build base query
    pages_query = db.session.query(CrawledPage).options(
        db.joinedload(CrawledPage.crawl_job)
    )
    
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
    
    # Get filter options
    crawl_jobs = CrawlJob.query.order_by(CrawlJob.name).all()
    personas = Persona.query.filter_by(is_active=True).order_by(Persona.title).all()
    
    # Get mapping method distribution
    method_distribution = db.session.query(
        ContentMapping.mapping_method,
        db.func.count(ContentMapping.id).label('count'),
        db.func.avg(ContentMapping.confidence_score).label('avg_confidence')
    ).filter_by(is_active=True).group_by(
        ContentMapping.mapping_method
    ).all()
    
    # Get content with no mappings
    unmapped_content_count = db.session.query(CrawledPage).outerjoin(
        ContentMapping, CrawledPage.id == ContentMapping.page_id
    ).filter(ContentMapping.id.is_(None)).count()
    
    # Get total stats
    total_pages = CrawledPage.query.count()
    mapped_pages = db.session.query(CrawledPage).join(
        ContentMapping, CrawledPage.id == ContentMapping.page_id
    ).filter(ContentMapping.is_active == True).distinct().count()
    
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
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Title', 'Description', 'Keywords', 'Total Mappings',
        'High Confidence Mappings', 'Average Confidence', 'Created At'
    ])
    
    # Write data
    for persona in Persona.query.filter_by(is_active=True).all():
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
    response.headers['Content-Disposition'] = f'attachment; filename=personas_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

@bp.route('/export/mappings')
@login_required
def export_mappings():
    """Export content mappings as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Mapping ID', 'Page URL', 'Page Title', 'Persona Title',
        'Confidence Score', 'Confidence Level', 'Mapping Method',
        'Mapping Reason', 'Is Verified', 'Created At'
    ])
    
    # Write data
    mappings = db.session.query(
        ContentMapping, CrawledPage, Persona
    ).join(
        CrawledPage, ContentMapping.page_id == CrawledPage.id
    ).join(
        Persona, ContentMapping.persona_id == Persona.id
    ).filter(
        db.and_(
            ContentMapping.is_active == True,
            Persona.is_active == True
        )
    ).order_by(ContentMapping.confidence_score.desc()).all()
    
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
    response.headers['Content-Disposition'] = f'attachment; filename=mappings_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
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
