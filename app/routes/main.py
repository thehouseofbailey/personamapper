from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import Persona, CrawlJob, CrawledPage, ContentMapping
from app import db
from sqlalchemy import func, and_
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise show landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing overview statistics."""
    # Get overview statistics
    stats = {
        'total_personas': Persona.query.filter_by(is_active=True).count(),
        'total_crawl_jobs': CrawlJob.query.count(),
        'active_crawl_jobs': CrawlJob.query.filter_by(status='active').count(),
        'running_crawl_jobs': CrawlJob.query.filter_by(status='running').count(),
        'total_pages_crawled': CrawledPage.query.count(),
        'total_mappings': ContentMapping.query.filter_by(is_active=True).count(),
        'high_confidence_mappings': ContentMapping.query.filter(
            db.and_(
                ContentMapping.confidence_score >= 0.8,
                ContentMapping.is_active == True
            )
        ).count()
    }
    
    # Get recent activity
    recent_pages = CrawledPage.query.order_by(
        CrawledPage.crawled_at.desc()
    ).limit(5).all()
    
    recent_mappings = ContentMapping.query.filter_by(is_active=True).order_by(
        ContentMapping.created_at.desc()
    ).limit(5).all()
    
    # Get top personas by mapping count
    top_personas = db.session.query(
        Persona,
        db.func.count(ContentMapping.id).label('mapping_count')
    ).join(
        ContentMapping, Persona.id == ContentMapping.persona_id
    ).filter(
        db.and_(
            Persona.is_active == True,
            ContentMapping.is_active == True
        )
    ).group_by(Persona.id).order_by(
        db.desc('mapping_count')
    ).limit(5).all()
    
    # Get chart data for persona confidence over time
    chart_data = get_persona_confidence_chart_data()
    
    return render_template('dashboard.html',
                         stats=stats,
                         recent_pages=recent_pages,
                         recent_mappings=recent_mappings,
                         top_personas=top_personas,
                         chart_data=chart_data)

@bp.route('/about')
def about():
    """About page with application information."""
    return render_template('about.html')

@bp.route('/help')
@login_required
def help():
    """Help page with user documentation."""
    return render_template('help.html')

@bp.route('/ai-integration')
@login_required
def ai_integration():
    """AI Integration documentation page."""
    return render_template('ai_integration.html')

def get_persona_confidence_chart_data():
    """Get data for persona confidence over time chart."""
    # Query to get average confidence scores by persona and date
    # Group by persona and crawl_timestamp date (not time)
    query = db.session.query(
        Persona.id,
        Persona.title,
        func.date(ContentMapping.crawl_timestamp).label('crawl_date'),
        func.avg(ContentMapping.confidence_score).label('avg_confidence')
    ).join(
        ContentMapping, Persona.id == ContentMapping.persona_id
    ).filter(
        and_(
            Persona.is_active == True,
            ContentMapping.is_active == True,
            ContentMapping.crawl_timestamp.isnot(None)
        )
    ).group_by(
        Persona.id,
        Persona.title,
        func.date(ContentMapping.crawl_timestamp)
    ).order_by(
        func.date(ContentMapping.crawl_timestamp),
        Persona.title
    ).all()
    
    # Organize data by persona
    personas_data = {}
    all_dates = set()
    
    for persona_id, persona_title, crawl_date, avg_confidence in query:
        if persona_id not in personas_data:
            personas_data[persona_id] = {
                'title': persona_title,
                'data': {}
            }
        
        date_str = str(crawl_date) if crawl_date else None
        if date_str:
            personas_data[persona_id]['data'][date_str] = round(avg_confidence * 100, 1)  # Convert to percentage
            all_dates.add(date_str)
    
    # Sort dates
    sorted_dates = sorted(list(all_dates))
    
    # Prepare chart data structure
    chart_data = {
        'labels': sorted_dates,
        'datasets': []
    }
    
    # Color palette for different personas
    colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
    ]
    
    # Create dataset for each persona
    for i, (persona_id, persona_info) in enumerate(personas_data.items()):
        color = colors[i % len(colors)]
        dataset = {
            'label': persona_info['title'],
            'data': [],
            'borderColor': color,
            'backgroundColor': color + '20',  # Add transparency
            'fill': False,
            'tension': 0.1,
            'borderWidth': 2,
            'pointBackgroundColor': color,
            'pointBorderColor': '#fff',
            'pointBorderWidth': 2,
            'spanGaps': True  # Connect points even if there are null values
        }
        
        # Fill data points for each date
        for date in sorted_dates:
            confidence = persona_info['data'].get(date, None)
            dataset['data'].append(confidence)
        
        # Only add dataset if it has at least one non-null value
        if any(x is not None for x in dataset['data']):
            chart_data['datasets'].append(dataset)
    
    return chart_data

@bp.route('/api/persona-confidence-chart')
@login_required
def persona_confidence_chart_api():
    """API endpoint for persona confidence chart data."""
    return jsonify(get_persona_confidence_chart_data())
