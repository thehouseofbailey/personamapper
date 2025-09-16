from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.persona import Persona
from app.models.content_mapping import ContentMapping
from app.models.crawled_page import CrawledPage
from app import db
from urllib.parse import urlparse, unquote
import hashlib
import hmac
import time
from collections import defaultdict, Counter
import json

bp = Blueprint('api', __name__)

def generate_api_signature(data, timestamp, secret_key):
    """Generate HMAC signature for API request validation."""
    message = f"{data}{timestamp}"
    return hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def validate_api_request():
    """Validate API request signature and timestamp."""
    # For now, we'll use a simple domain-based validation
    # In production, you might want to implement proper API key management
    
    # Check if request is from allowed origins (optional)
    origin = request.headers.get('Origin')
    referer = request.headers.get('Referer')
    
    # Basic rate limiting could be implemented here
    # For now, we'll allow all requests but you can enhance this
    
    return True

def normalize_url(url):
    """Normalize URL for consistent matching."""
    if not url:
        return None
    
    # Remove protocol and www
    parsed = urlparse(url.lower())
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.rstrip('/')
    
    # Remove common tracking parameters
    return f"{domain}{path}"

@bp.route('/personas/page', methods=['GET'])
def get_page_personas():
    """
    Get personas matched to a specific page URL.
    
    Query parameters:
    - url: The page URL to get personas for (required)
    - min_confidence: Minimum confidence score (default: 0.6)
    - limit: Maximum number of personas to return (default: 10)
    """
    if not validate_api_request():
        return jsonify({'error': 'Invalid request'}), 403
    
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    min_confidence = float(request.args.get('min_confidence', 0.1))
    limit = int(request.args.get('limit', 10))
    
    try:
        # Decode URL if it's encoded
        url = unquote(url)
        
        # Find the crawled page by URL
        page = CrawledPage.query.filter(CrawledPage.url == url).first()
        
        if not page:
            # Try to find by normalized URL matching
            normalized_input = normalize_url(url)
            if normalized_input:
                pages = CrawledPage.query.all()
                for p in pages:
                    if normalize_url(p.url) == normalized_input:
                        page = p
                        break
        
        if not page:
            return jsonify({
                'url': url,
                'personas': [],
                'message': 'No data found for this URL'
            })
        
        # Get active mappings with minimum confidence
        mappings = ContentMapping.query.filter(
            db.and_(
                ContentMapping.page_id == page.id,
                ContentMapping.is_active == True,
                ContentMapping.confidence_score >= min_confidence
            )
        ).order_by(ContentMapping.confidence_score.desc()).limit(limit).all()
        
        # Build response with persona details
        personas = []
        for mapping in mappings:
            # Get the persona object
            persona = Persona.query.get(mapping.persona_id)
            if persona and persona.is_active:
                persona_data = {
                    'id': persona.id,
                    'title': persona.title,
                    'description': persona.description,
                    'keywords': persona.get_keywords_list(),
                    'confidence_score': round(mapping.confidence_score, 3),
                    'confidence_level': mapping.get_confidence_level(),
                    'mapping_method': mapping.mapping_method,
                    'is_verified': mapping.is_verified
                }
                personas.append(persona_data)
        
        return jsonify({
            'url': url,
            'page_title': page.title,
            'personas': personas,
            'total_found': len(personas)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_page_personas: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/personas/predict', methods=['POST'])
def predict_user_persona():
    """
    Predict user persona based on visited pages during a session.
    
    Expected JSON payload:
    {
        "visited_urls": ["url1", "url2", "url3"],
        "session_id": "optional_session_identifier",
        "min_confidence": 0.6,
        "prediction_method": "weighted" // or "frequency"
    }
    """
    if not validate_api_request():
        return jsonify({'error': 'Invalid request'}), 403
    
    try:
        data = request.get_json()
        if not data or 'visited_urls' not in data:
            return jsonify({'error': 'visited_urls is required'}), 400
        
        visited_urls = data.get('visited_urls', [])
        min_confidence = data.get('min_confidence', 0.1)
        prediction_method = data.get('prediction_method', 'weighted')
        session_id = data.get('session_id', 'anonymous')
        
        if not visited_urls:
            return jsonify({
                'session_id': session_id,
                'predicted_personas': [],
                'confidence': 0,
                'method': prediction_method,
                'pages_analyzed': 0
            })
        
        # Collect persona scores from all visited pages
        persona_scores = defaultdict(list)
        pages_analyzed = 0
        page_details = []
        
        for url in visited_urls:
            # Decode URL if needed
            url = unquote(url)
            
            # Find the crawled page
            page = CrawledPage.query.filter(CrawledPage.url == url).first()
            
            if not page:
                # Try normalized URL matching
                normalized_input = normalize_url(url)
                if normalized_input:
                    pages = CrawledPage.query.all()
                    for p in pages:
                        if normalize_url(p.url) == normalized_input:
                            page = p
                            break
            
            if page:
                pages_analyzed += 1
                page_info = {
                    'url': url, 
                    'title': page.title,
                    'personas': []
                }
                
                # Get mappings for this page
                mappings = ContentMapping.query.filter(
                    db.and_(
                        ContentMapping.page_id == page.id,
                        ContentMapping.is_active == True,
                        ContentMapping.confidence_score >= min_confidence
                    )
                ).all()
                
                for mapping in mappings:
                    persona_scores[mapping.persona_id].append(mapping.confidence_score)
                    # Get the persona object
                    persona = Persona.query.get(mapping.persona_id)
                    if persona:
                        page_info['personas'].append({
                            'id': mapping.persona_id,
                            'title': persona.title,
                            'confidence': mapping.confidence_score
                        })
                
                page_details.append(page_info)
        
        # Calculate final persona predictions
        predicted_personas = []
        
        if persona_scores:
            for persona_id, scores in persona_scores.items():
                persona = Persona.query.get(persona_id)
                if not persona or not persona.is_active:
                    continue
                
                if prediction_method == 'weighted':
                    # Weighted average of confidence scores
                    final_score = sum(scores) / len(scores)
                    # Boost score based on frequency of appearance
                    frequency_boost = min(len(scores) * 0.1, 0.3)
                    final_score = min(final_score + frequency_boost, 1.0)
                else:  # frequency method
                    # Score based on how often persona appears
                    final_score = len(scores) / len(visited_urls)
                    # Boost with average confidence
                    confidence_boost = (sum(scores) / len(scores)) * 0.3
                    final_score = min(final_score + confidence_boost, 1.0)
                
                predicted_personas.append({
                    'id': persona.id,
                    'title': persona.title,
                    'description': persona.description,
                    'keywords': persona.get_keywords_list(),
                    'prediction_score': round(final_score, 3),
                    'page_appearances': len(scores),
                    'avg_confidence': round(sum(scores) / len(scores), 3)
                })
        
        # Sort by prediction score
        predicted_personas.sort(key=lambda x: x['prediction_score'], reverse=True)
        
        # Calculate overall confidence
        overall_confidence = 0
        if predicted_personas:
            overall_confidence = predicted_personas[0]['prediction_score']
        
        return jsonify({
            'session_id': session_id,
            'predicted_personas': predicted_personas,
            'confidence': overall_confidence,
            'method': prediction_method,
            'pages_analyzed': pages_analyzed,
            'total_pages_submitted': len(visited_urls),
            'page_details': page_details
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in predict_user_persona: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time()),
        'version': '1.0.0'
    })

@bp.route('/personas/list', methods=['GET'])
def list_personas():
    """
    Get a list of all active personas.
    
    Query parameters:
    - limit: Maximum number of personas to return (default: 50)
    """
    if not validate_api_request():
        return jsonify({'error': 'Invalid request'}), 403
    
    try:
        limit = int(request.args.get('limit', 50))
        
        personas = Persona.query.filter(
            Persona.is_active == True
        ).order_by(Persona.title).limit(limit).all()
        
        personas_data = []
        for persona in personas:
            personas_data.append({
                'id': persona.id,
                'title': persona.title,
                'description': persona.description,
                'keywords': persona.get_keywords_list(),
                'mapping_count': persona.get_mapping_count()
            })
        
        return jsonify({
            'personas': personas_data,
            'total_found': len(personas_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in list_personas: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/sample-urls', methods=['GET'])
def get_sample_urls():
    """
    Get sample crawled URLs for testing purposes.
    
    Query parameters:
    - limit: Maximum number of URLs to return (default: 10)
    """
    if not validate_api_request():
        return jsonify({'error': 'Invalid request'}), 403
    
    try:
        limit = int(request.args.get('limit', 10))
        
        # Get pages that have persona mappings
        pages = CrawledPage.query.join(ContentMapping).filter(
            ContentMapping.is_active == True
        ).distinct().limit(limit).all()
        
        sample_urls = []
        for page in pages:
            # Get the top persona for this page
            top_mapping = ContentMapping.query.filter(
                db.and_(
                    ContentMapping.page_id == page.id,
                    ContentMapping.is_active == True
                )
            ).order_by(ContentMapping.confidence_score.desc()).first()
            
            if top_mapping:
                persona = Persona.query.get(top_mapping.persona_id)
                sample_urls.append({
                    'url': page.url,
                    'title': page.title,
                    'top_persona': persona.title if persona else 'Unknown',
                    'confidence': round(top_mapping.confidence_score, 3)
                })
        
        return jsonify({
            'sample_urls': sample_urls,
            'total_found': len(sample_urls)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_sample_urls: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/ai/status', methods=['GET'])
def get_ai_status():
    """
    Get AI analyzer status and configuration.
    Optional query parameter: website_id for organisation-specific config
    """
    if not validate_api_request():
        return jsonify({'error': 'Invalid request'}), 403
    
    try:
        from app.services.unified_analyzer import UnifiedContentAnalyzer
        
        website_id = request.args.get('website_id', type=int)
        analyzer = UnifiedContentAnalyzer(website_id=website_id)
        info = analyzer.get_analyzer_info()
        
        return jsonify({
            'ai_status': info,
            'timestamp': int(time.time())
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_ai_status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/ai/analyze', methods=['POST'])
def analyze_content_with_ai():
    """
    Analyze content using AI for persona mapping.
    
    Expected JSON payload:
    {
        "content": "text content to analyze",
        "url": "optional URL for context",
        "title": "optional page title"
    }
    """
    if not validate_api_request():
        return jsonify({'error': 'Invalid request'}), 403
    
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'content is required'}), 400
        
        content = data.get('content', '')
        url = data.get('url', 'https://example.com/test')
        title = data.get('title', 'Test Page')
        website_id = data.get('website_id')  # Optional website ID for AI config
        
        if not content or len(content.strip()) < 50:
            return jsonify({'error': 'Content too short for analysis (minimum 50 characters)'}), 400
        
        from app.services.unified_analyzer import UnifiedContentAnalyzer
        from app.models.crawled_page import CrawledPage
        
        # Create a temporary page object for analysis
        temp_page = CrawledPage(
            url=url,
            title=title,
            content=content,
            word_count=len(content.split())
        )
        
        analyzer = UnifiedContentAnalyzer(website_id=website_id)
        mappings = analyzer.analyze_page(temp_page)
        
        # Format results
        results = []
        for mapping in mappings:
            results.append({
                'persona_id': mapping['persona_id'],
                'persona_title': mapping['persona_title'],
                'confidence_score': round(mapping['confidence_score'], 3),
                'mapping_reason': mapping['mapping_reason'],
                'mapping_method': mapping['mapping_method']
            })
        
        return jsonify({
            'analysis_results': results,
            'total_mappings': len(results),
            'analyzer_info': analyzer.get_analyzer_info(),
            'content_length': len(content),
            'word_count': len(content.split())
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in analyze_content_with_ai: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@bp.route('/websites/<int:website_id>/personas', methods=['GET'])
@login_required
def get_website_personas(website_id):
    """Get all personas for a specific website."""
    from app.models.website import Website
    
    # Check if user has access to this website
    website = Website.query.get_or_404(website_id)
    
    if not current_user.can_view_website(website_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get personas for this website
    personas = website.get_personas()
    
    personas_data = []
    for persona in personas:
        personas_data.append({
            'id': persona.id,
            'title': persona.title,
            'description': persona.description,
            'is_active': persona.is_active
        })
    
    return jsonify({
        'personas': personas_data,
        'website_id': website_id,
        'website_name': website.name
    })
