#!/usr/bin/env python3
"""
PersonaMap Application Entry Point

This is the main entry point for the PersonaMap application.
Run this file to start the Flask development server.
"""

import os
from app import create_app, db
from app.models import User, Persona, CrawlJob, CrawledPage, ContentMapping

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        'db': db,
        'User': User,
        'Persona': Persona,
        'CrawlJob': CrawlJob,
        'CrawledPage': CrawledPage,
        'ContentMapping': ContentMapping
    }

@app.cli.command()
def init_db():
    """Initialize the database with sample data."""
    db.create_all()
    
    # Create default admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@personamap.local',
            role='admin'
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        
        print("Created default admin user:")
        print("Username: admin")
        print("Password: admin123")
        print("Please change the password after first login!")
    
    # Create sample personas
    if Persona.query.count() == 0:
        sample_personas = [
            {
                'title': 'Tech Enthusiast',
                'description': 'Early adopters who are interested in the latest technology trends, gadgets, and innovations.',
                'keywords': 'technology, innovation, gadgets, AI, software, hardware, tech news, startups'
            },
            {
                'title': 'Business Professional',
                'description': 'Working professionals focused on career growth, business strategies, and industry insights.',
                'keywords': 'business, career, professional development, leadership, strategy, management, productivity'
            },
            {
                'title': 'Content Creator',
                'description': 'Individuals who create and share content across various platforms and are interested in creative tools and techniques.',
                'keywords': 'content creation, social media, blogging, video, photography, design, creative tools'
            }
        ]
        
        for persona_data in sample_personas:
            persona = Persona(**persona_data)
            db.session.add(persona)
        
        print("Created sample personas")
    
    db.session.commit()
    print("Database initialized successfully!")

if __name__ == '__main__':
    # Set environment variables for development
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    print("Starting PersonaMap Application...")
    print("Access the application at: http://localhost:5002")
    print("Default admin credentials: admin / admin123")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
