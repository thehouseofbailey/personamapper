#!/usr/bin/env python3
"""
Cleanup script to remove duplicate persona mappings.
This will keep only the highest confidence mapping for each page-persona pair.
"""

from app import create_app, db
from app.models import ContentMapping
from sqlalchemy import func

def cleanup_duplicate_mappings():
    """Remove duplicate persona mappings, keeping the highest confidence one."""
    app = create_app()
    
    with app.app_context():
        try:
            # Find duplicate mappings (same page_id and persona_id)
            duplicates = db.session.query(
                ContentMapping.page_id,
                ContentMapping.persona_id,
                func.count(ContentMapping.id).label('count')
            ).filter(
                ContentMapping.is_active == True
            ).group_by(
                ContentMapping.page_id,
                ContentMapping.persona_id
            ).having(
                func.count(ContentMapping.id) > 1
            ).all()
            
            if not duplicates:
                print("✅ No duplicate mappings found!")
                return True
            
            print(f"🔍 Found {len(duplicates)} sets of duplicate mappings")
            
            total_removed = 0
            
            for page_id, persona_id, count in duplicates:
                print(f"📄 Processing page {page_id} -> persona {persona_id} ({count} duplicates)")
                
                # Get all mappings for this page-persona pair, ordered by confidence (highest first)
                mappings = ContentMapping.query.filter_by(
                    page_id=page_id,
                    persona_id=persona_id,
                    is_active=True
                ).order_by(
                    ContentMapping.confidence_score.desc(),
                    ContentMapping.created_at.desc()
                ).all()
                
                # Keep the first one (highest confidence), remove the rest
                if len(mappings) > 1:
                    keep_mapping = mappings[0]
                    remove_mappings = mappings[1:]
                    
                    print(f"  ✅ Keeping mapping {keep_mapping.id} (confidence: {keep_mapping.confidence_score:.3f})")
                    
                    for mapping in remove_mappings:
                        print(f"  ❌ Removing mapping {mapping.id} (confidence: {mapping.confidence_score:.3f})")
                        db.session.delete(mapping)
                        total_removed += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"🎉 Cleanup completed! Removed {total_removed} duplicate mappings")
            return True
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    cleanup_duplicate_mappings()
