from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app import db
from app.models import Persona, ContentMapping
from app.forms import PersonaForm

bp = Blueprint('personas', __name__)

@bp.route('/')
@login_required
def list_personas():
    """List all personas."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    personas = Persona.query.filter_by(is_active=True).order_by(
        Persona.created_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('personas/list.html', personas=personas)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_persona():
    """Create a new persona."""
    form = PersonaForm()
    
    if form.validate_on_submit():
        # Create new persona
        persona = Persona(
            title=form.title.data,
            description=form.description.data,
            keywords=form.keywords.data
        )
        
        db.session.add(persona)
        db.session.commit()
        
        flash(f'Persona "{persona.title}" created successfully!', 'success')
        return redirect(url_for('personas.view_persona', id=persona.id))
    
    return render_template('personas/create.html', form=form)

@bp.route('/<int:id>')
@login_required
def view_persona(id):
    """View a specific persona and its mappings."""
    persona = Persona.query.get_or_404(id)
    
    if not persona.is_active:
        flash('This persona is not active.', 'warning')
        return redirect(url_for('personas.list_personas'))
    
    # Get mapping statistics
    total_mappings = persona.content_mappings.filter_by(is_active=True).count()
    high_confidence_mappings = persona.content_mappings.filter(
        db.and_(
            ContentMapping.confidence_score >= 0.8,
            ContentMapping.is_active == True
        )
    ).count()
    
    # Get recent mappings
    recent_mappings = persona.content_mappings.filter_by(is_active=True).order_by(
        ContentMapping.created_at.desc()
    ).limit(10).all()
    
    # Get top mappings by confidence
    top_mappings = persona.content_mappings.filter_by(is_active=True).order_by(
        ContentMapping.confidence_score.desc()
    ).limit(10).all()
    
    return render_template('personas/view.html',
                         persona=persona,
                         mappings=recent_mappings,
                         high_confidence_count=high_confidence_mappings)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_persona(id):
    """Edit an existing persona."""
    persona = Persona.query.get_or_404(id)
    
    if not persona.is_active:
        flash('This persona is not active and cannot be edited.', 'error')
        return redirect(url_for('personas.list_personas'))
    
    form = PersonaForm(persona=persona, obj=persona)
    
    if form.validate_on_submit():
        # Update persona
        form.populate_obj(persona)
        db.session.commit()
        
        flash(f'Persona "{persona.title}" updated successfully!', 'success')
        return redirect(url_for('personas.view_persona', id=persona.id))
    
    return render_template('personas/edit.html', persona=persona, form=form)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_persona(id):
    """Soft delete a persona (mark as inactive)."""
    persona = Persona.query.get_or_404(id)
    
    if not persona.is_active:
        flash('This persona is already inactive.', 'warning')
        return redirect(url_for('personas.list_personas'))
    
    # Soft delete by marking as inactive
    persona.is_active = False
    
    # Also deactivate all related content mappings
    ContentMapping.query.filter_by(persona_id=id).update({'is_active': False})
    
    db.session.commit()
    
    flash(f'Persona "{persona.title}" has been deleted.', 'success')
    return redirect(url_for('personas.list_personas'))

@bp.route('/<int:id>/mappings')
@login_required
def persona_mappings(id):
    """View all content mappings for a persona."""
    persona = Persona.query.get_or_404(id)
    
    if not persona.is_active:
        flash('This persona is not active.', 'warning')
        return redirect(url_for('personas.list_personas'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    mappings = persona.content_mappings.filter_by(is_active=True).order_by(
        ContentMapping.confidence_score.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('personas/mappings.html', 
                         persona=persona, 
                         mappings=mappings)

@bp.route('/api/<int:id>')
@login_required
def api_get_persona(id):
    """API endpoint to get persona data as JSON."""
    persona = Persona.query.get_or_404(id)
    
    if not persona.is_active:
        return jsonify({'error': 'Persona not found'}), 404
    
    return jsonify(persona.to_dict())

@bp.route('/api')
@login_required
def api_list_personas():
    """API endpoint to get all active personas as JSON."""
    personas = Persona.query.filter_by(is_active=True).order_by(
        Persona.title
    ).all()
    
    return jsonify([persona.to_dict() for persona in personas])
