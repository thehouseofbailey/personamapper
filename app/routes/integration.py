from flask import Blueprint, render_template, request, jsonify, current_app, url_for
from flask_login import login_required, current_user
from functools import wraps

bp = Blueprint('integration', __name__)

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_super_admin or current_user.is_organisation_admin()):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/tag-manager')
@login_required
@admin_required
def tag_manager_integration():
    """Display Tag Manager integration code for admins."""
    
    # Get the base URL for the API
    base_url = request.url_root.rstrip('/')
    api_url = f"{base_url}/api"
    client_js_url = f"{base_url}/static/personamap-client.js"
    
    # Generate the integration code
    integration_data = {
        'api_url': api_url,
        'client_js_url': client_js_url,
        'base_url': base_url
    }
    
    return render_template('integration/tag_manager.html', **integration_data)

@bp.route('/api/integration-code')
@login_required
@admin_required
def get_integration_code():
    """API endpoint to get integration code snippets."""
    
    base_url = request.url_root.rstrip('/')
    api_url = f"{base_url}/api"
    client_js_url = f"{base_url}/static/personamap-client.js"
    
    # HTML Tag code for GTM
    html_tag_code = f'''<!-- PersonaMap Integration -->
<script>
// Configuration
window.PERSONAMAP_API_URL = '{api_url}';
window.PERSONAMAP_AUTO_INIT = true;
</script>
<script src="{client_js_url}"></script>

<script>
// Optional: Listen for persona prediction events
document.addEventListener('DOMContentLoaded', function() {{
    if (window.personaMapInstance) {{
        window.personaMapInstance.on('onPersonaPrediction', function(data) {{
            console.log('PersonaMap: Persona predicted', data.predicted_personas[0]?.title);
        }});
    }}
}});
</script>'''

    # GA4 Event Tag code
    ga4_event_code = '''// GA4 Event Tag (triggered by personaPredictionUpdate)
gtag('event', 'persona_identified', {
  'persona_name': '{{predictedPersona}}',
  'confidence_score': '{{personaConfidence}}',
  'pages_analyzed': '{{personaPagesAnalyzed}}',
  'session_id': '{{personaSessionId}}'
});'''

    # Custom JavaScript Variable code
    custom_js_variable = '''function() {
    // Get current predicted persona
    if (window.dataLayer) {
        for (var i = window.dataLayer.length - 1; i >= 0; i--) {
            if (window.dataLayer[i].predictedPersona) {
                return window.dataLayer[i].predictedPersona;
            }
        }
    }
    return 'Unknown';
}'''

    # Trigger configuration
    trigger_config = {
        'name': 'PersonaMap - Persona Prediction Update',
        'type': 'Custom Event',
        'event_name': 'personaPredictionUpdate',
        'description': 'Fires when PersonaMap updates the predicted persona'
    }

    return jsonify({
        'html_tag_code': html_tag_code,
        'ga4_event_code': ga4_event_code,
        'custom_js_variable': custom_js_variable,
        'trigger_config': trigger_config,
        'api_url': api_url,
        'client_js_url': client_js_url,
        'variables': {
            'predictedPersona': 'The predicted persona name',
            'personaConfidence': 'Confidence score (0-1)',
            'personaTimestamp': 'When prediction was made',
            'personaSessionId': 'Session identifier',
            'personaPagesAnalyzed': 'Number of pages analyzed'
        }
    })
