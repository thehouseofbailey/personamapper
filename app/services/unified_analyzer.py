"""
Unified Content Analyzer that chooses between AI and keyword analysis based on configuration.
"""

import logging
from typing import List, Dict
from flask import current_app
from app.models import CrawledPage, Persona, ContentMapping
from app.services.content_analyzer import ContentAnalyzer
from app.services.ai_analyzer import AIContentAnalyzer

logger = logging.getLogger(__name__)

class UnifiedContentAnalyzer:
    """
    Unified analyzer that automatically chooses the best analysis method
    based on configuration and availability.
    """
    
    def __init__(self):
        self.keyword_analyzer = ContentAnalyzer()
        self.ai_analyzer = None
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Initialize analyzers based on configuration."""
        try:
            # Initialize AI analyzer if enabled
            if current_app.config.get('AI_ENABLED', False):
                self.ai_analyzer = AIContentAnalyzer()
                logger.info("AI analyzer initialized successfully")
            else:
                logger.info("AI analysis disabled in configuration")
        except Exception as e:
            logger.error(f"Failed to initialize AI analyzer: {e}")
            self.ai_analyzer = None
    
    def analyze_page(self, page: CrawledPage) -> List[Dict]:
        """
        Analyze a page using the best available method.
        
        Args:
            page: CrawledPage object to analyze
            
        Returns:
            List of mapping dictionaries
        """
        analysis_mode = current_app.config.get('AI_ANALYSIS_MODE', 'keyword')
        
        # Use AI analyzer if available and configured
        if self.ai_analyzer and analysis_mode != 'keyword':
            try:
                return self.ai_analyzer.analyze_page(page)
            except Exception as e:
                logger.warning(f"AI analysis failed, falling back to keyword analysis: {e}")
                return self.keyword_analyzer.analyze_page(page)
        else:
            # Use keyword analyzer
            return self.keyword_analyzer.analyze_page(page)
    
    def process_page(self, page: CrawledPage) -> int:
        """
        Process a page with the best available analyzer.
        
        Args:
            page: CrawledPage object to process
            
        Returns:
            Number of mappings created
        """
        analysis_mode = current_app.config.get('AI_ANALYSIS_MODE', 'keyword')
        
        # Use AI analyzer if available and configured
        if self.ai_analyzer and analysis_mode != 'keyword':
            try:
                return self.ai_analyzer.process_page(page)
            except Exception as e:
                logger.warning(f"AI processing failed, falling back to keyword analysis: {e}")
                return self.keyword_analyzer.process_page(page)
        else:
            # Use keyword analyzer
            return self.keyword_analyzer.process_page(page)
    
    def create_mappings(self, page: CrawledPage, mappings: List[Dict]) -> List[ContentMapping]:
        """
        Create ContentMapping objects from analysis results.
        
        Args:
            page: CrawledPage object
            mappings: List of mapping dictionaries
            
        Returns:
            List of created ContentMapping objects
        """
        # Both analyzers use the same mapping creation logic
        return self.keyword_analyzer.create_mappings(page, mappings)
    
    def get_analyzer_info(self) -> Dict:
        """Get information about available analyzers."""
        info = {
            'keyword_available': True,
            'ai_available': self.ai_analyzer is not None,
            'current_mode': current_app.config.get('AI_ANALYSIS_MODE', 'keyword'),
            'ai_enabled': current_app.config.get('AI_ENABLED', False)
        }
        
        if self.ai_analyzer:
            info.update(self.ai_analyzer.get_analysis_stats())
        
        return info
    
    def analyze_content_for_persona(self, content: str, persona: Persona) -> Dict:
        """
        Analyze content for a specific persona.
        
        Args:
            content: Text content to analyze
            persona: Persona object to match against
            
        Returns:
            Dictionary with mapping decision and details
        """
        # For now, use keyword analyzer for single persona analysis
        # This could be extended to use AI in the future
        return self.keyword_analyzer.analyze_content_for_persona(content, persona)
    
    def batch_process_pages(self, pages: List[CrawledPage]) -> Dict[str, int]:
        """
        Process multiple pages in batch.
        
        Args:
            pages: List of CrawledPage objects to process
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'processed': 0,
            'mappings_created': 0,
            'errors': 0,
            'ai_used': 0,
            'keyword_used': 0
        }
        
        analysis_mode = current_app.config.get('AI_ANALYSIS_MODE', 'keyword')
        
        for page in pages:
            try:
                # Track which analyzer was used
                if self.ai_analyzer and analysis_mode != 'keyword':
                    try:
                        mappings_count = self.ai_analyzer.process_page(page)
                        stats['ai_used'] += 1
                    except Exception as e:
                        logger.warning(f"AI processing failed for page {page.url}, using keyword fallback: {e}")
                        mappings_count = self.keyword_analyzer.process_page(page)
                        stats['keyword_used'] += 1
                else:
                    mappings_count = self.keyword_analyzer.process_page(page)
                    stats['keyword_used'] += 1
                
                stats['processed'] += 1
                stats['mappings_created'] += mappings_count
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing page {page.url}: {str(e)}")
        
        return stats
