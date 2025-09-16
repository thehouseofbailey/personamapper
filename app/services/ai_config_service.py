"""
Utility functions for accessing organisation-specific AI configuration.
This replaces the global .env AI settings with per-organisation configuration.
"""

from app.models import Organisation

def get_ai_config_for_organisation(organisation_id):
    """
    Get AI configuration for a specific organisation.
    Falls back to default values if organisation doesn't exist.
    """
    organisation = Organisation.query.get(organisation_id)
    
    if not organisation:
        # Return default configuration if organisation not found
        return {
            'ai_enabled': False,
            'ai_analysis_mode': 'keyword',
            'openai_api_key': None,
            'openai_model': 'gpt-3.5-turbo',
            'openai_max_tokens': 1000,
            'openai_temperature': 0.3,
            'ai_daily_cost_limit': 10.0,
            'ai_monthly_cost_limit': 100.0,
            'local_ai_model': 'all-MiniLM-L6-v2',
            'local_ai_similarity_threshold': 0.5,
            'ai_confidence_threshold': 0.3,
            'ai_content_chunk_size': 2000,
            'has_openai_key': False
        }
    
    return organisation.get_ai_config()

def get_ai_config_for_website(website_id):
    """
    Get AI configuration for a website based on its organisation.
    Returns None if website doesn't exist or has no organisation.
    """
    from app.models import Website
    
    website = Website.query.get(website_id)
    if not website:
        return None
    
    # Get the first organisation that has access to this website
    from app.models import OrganisationWebsite
    org_website = OrganisationWebsite.query.filter_by(website_id=website_id).first()
    
    if not org_website:
        return None
    
    return get_ai_config_for_organisation(org_website.organisation_id)

def is_ai_enabled_for_organisation(organisation_id):
    """Quick check if AI is enabled for an organisation."""
    config = get_ai_config_for_organisation(organisation_id)
    return config.get('ai_enabled', False)

def is_ai_enabled_for_website(website_id):
    """Quick check if AI is enabled for a website."""
    config = get_ai_config_for_website(website_id)
    return config.get('ai_enabled', False) if config else False

def get_available_ai_modes():
    """Get list of available AI analysis modes."""
    return [
        ('keyword', 'Keyword Matching Only'),
        ('local', 'Local AI (Sentence Transformers)'),
        ('ai', 'OpenAI GPT Analysis'),
        ('hybrid', 'Hybrid (Keyword + AI)'),
        ('validation', 'AI Validation of Keyword Matches')
    ]

def validate_ai_config(config):
    """
    Validate AI configuration dictionary.
    Returns (is_valid, error_message).
    """
    if not isinstance(config, dict):
        return False, "Configuration must be a dictionary"
    
    # Check required fields for OpenAI modes
    ai_modes_requiring_key = ['ai', 'hybrid', 'validation']
    if (config.get('ai_enabled') and 
        config.get('ai_analysis_mode') in ai_modes_requiring_key and 
        not config.get('openai_api_key')):
        return False, f"OpenAI API key is required for {config.get('ai_analysis_mode')} mode"
    
    # Validate numeric ranges
    numeric_validations = [
        ('openai_max_tokens', 100, 4000),
        ('openai_temperature', 0.0, 2.0),
        ('ai_daily_cost_limit', 0.0, 1000.0),
        ('ai_monthly_cost_limit', 0.0, 10000.0),
        ('local_ai_similarity_threshold', 0.0, 1.0),
        ('ai_confidence_threshold', 0.0, 1.0),
        ('ai_content_chunk_size', 500, 10000)
    ]
    
    for field, min_val, max_val in numeric_validations:
        if field in config:
            value = config[field]
            if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                return False, f"{field} must be between {min_val} and {max_val}"
    
    return True, None
