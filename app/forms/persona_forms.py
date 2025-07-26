from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import Persona

class PersonaForm(FlaskForm):
    """Form for creating and editing personas."""
    
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=2, max=200, message='Title must be between 2 and 200 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required'),
        Length(min=10, max=2000, message='Description must be between 10 and 2000 characters')
    ])
    
    keywords = TextAreaField('Keywords', validators=[
        DataRequired(message='Keywords are required'),
        Length(min=5, max=1000, message='Keywords must be between 5 and 1000 characters')
    ])
    
    submit = SubmitField('Save Persona')
    
    def __init__(self, persona=None, *args, **kwargs):
        """Initialize form with optional persona for editing."""
        super(PersonaForm, self).__init__(*args, **kwargs)
        self.persona = persona
    
    def validate_title(self, field):
        """Validate that title is unique."""
        query = Persona.query.filter_by(title=field.data, is_active=True)
        
        # If editing, exclude current persona from uniqueness check
        if self.persona:
            query = query.filter(Persona.id != self.persona.id)
        
        if query.first():
            raise ValidationError('A persona with this title already exists.')
    
    def validate_keywords(self, field):
        """Validate keywords format."""
        keywords = field.data.strip()
        if not keywords:
            raise ValidationError('Keywords are required.')
        
        # Split by comma and check each keyword
        keyword_list = [kw.strip() for kw in keywords.split(',')]
        keyword_list = [kw for kw in keyword_list if kw]  # Remove empty strings
        
        if len(keyword_list) < 2:
            raise ValidationError('Please provide at least 2 keywords separated by commas.')
        
        # Check for very short keywords
        short_keywords = [kw for kw in keyword_list if len(kw) < 2]
        if short_keywords:
            raise ValidationError(f'Keywords must be at least 2 characters long: {", ".join(short_keywords)}')
        
        # Check for very long keywords
        long_keywords = [kw for kw in keyword_list if len(kw) > 50]
        if long_keywords:
            raise ValidationError(f'Keywords must be less than 50 characters: {", ".join(long_keywords)}')
