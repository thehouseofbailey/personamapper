from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, IntegerField, FloatField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class OrganisationForm(FlaskForm):
    """Form for creating and editing organisations."""
    name = StringField('Organisation Name', validators=[
        DataRequired(),
        Length(min=2, max=200, message='Name must be between 2 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=1000, message='Description must be less than 1000 characters')
    ])

class AIConfigForm(FlaskForm):
    """Form for configuring AI settings for an organisation."""
    
    # Basic AI Settings
    ai_enabled = BooleanField('Enable AI Analysis')
    ai_analysis_mode = SelectField('AI Analysis Mode', choices=[
        ('keyword', 'Keyword Matching Only'),
        ('local', 'Local AI (Sentence Transformers)'),
        ('ai', 'OpenAI GPT Analysis'),
        ('hybrid', 'Hybrid (Keyword + AI)'),
        ('validation', 'AI Validation of Keyword Matches')
    ], default='keyword')
    
    # OpenAI Configuration
    openai_api_key = PasswordField('OpenAI API Key', validators=[Optional()])
    openai_model = SelectField('OpenAI Model', choices=[
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo (Recommended)'),
        ('gpt-3.5-turbo-16k', 'GPT-3.5 Turbo 16K'),
        ('gpt-4', 'GPT-4'),
        ('gpt-4-turbo-preview', 'GPT-4 Turbo Preview')
    ], default='gpt-3.5-turbo')
    
    openai_max_tokens = IntegerField('Max Tokens per Request', validators=[
        NumberRange(min=100, max=4000, message='Max tokens must be between 100 and 4000')
    ], default=1000)
    
    openai_temperature = FloatField('Temperature (Creativity)', validators=[
        NumberRange(min=0.0, max=2.0, message='Temperature must be between 0.0 and 2.0')
    ], default=0.3)
    
    # Cost Controls
    ai_daily_cost_limit = FloatField('Daily Cost Limit (USD)', validators=[
        NumberRange(min=0.0, max=1000.0, message='Daily limit must be between $0 and $1000')
    ], default=10.0)
    
    ai_monthly_cost_limit = FloatField('Monthly Cost Limit (USD)', validators=[
        NumberRange(min=0.0, max=10000.0, message='Monthly limit must be between $0 and $10,000')
    ], default=100.0)
    
    # Local AI Configuration
    local_ai_model = SelectField('Local AI Model', choices=[
        ('all-MiniLM-L6-v2', 'all-MiniLM-L6-v2 (Fast, Lightweight)'),
        ('all-mpnet-base-v2', 'all-mpnet-base-v2 (Higher Quality)'),
        ('paraphrase-MiniLM-L6-v2', 'paraphrase-MiniLM-L6-v2 (Paraphrase Detection)')
    ], default='all-MiniLM-L6-v2')
    
    local_ai_similarity_threshold = FloatField('Local AI Similarity Threshold', validators=[
        NumberRange(min=0.0, max=1.0, message='Similarity threshold must be between 0.0 and 1.0')
    ], default=0.5)
    
    # General AI Settings
    ai_confidence_threshold = FloatField('AI Confidence Threshold', validators=[
        NumberRange(min=0.0, max=1.0, message='Confidence threshold must be between 0.0 and 1.0')
    ], default=0.3)
    
    ai_content_chunk_size = IntegerField('Content Chunk Size (characters)', validators=[
        NumberRange(min=500, max=10000, message='Chunk size must be between 500 and 10,000 characters')
    ], default=2000)
    
    def validate(self, extra_validators=None):
        """Custom validation logic."""
        if not super().validate(extra_validators):
            return False
        
        # If AI is enabled and mode requires OpenAI, ensure API key is provided
        if (self.ai_enabled.data and 
            self.ai_analysis_mode.data in ['ai', 'hybrid', 'validation'] and 
            not self.openai_api_key.data):
            self.openai_api_key.errors.append(
                'OpenAI API key is required for the selected AI analysis mode.'
            )
            return False
        
        return True
