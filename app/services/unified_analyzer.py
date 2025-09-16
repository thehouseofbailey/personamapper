"""
Unified Content Analyzer that chooses between AI and keyword analysis based on configuration.
"""

import logging
from typing import List, Dict
from flask import current_app
from app.models import CrawledPage, Persona, ContentMapping
from app.services.content_analyzer import ContentAnalyzer
from app.services.ai_analyzer import AIContentAnalyzer
from app.services.ai_config_service import get_ai_config_for_website

logger = logging.getLogger(__name__)

class UnifiedContentAnalyzer:
    """
    Unified analyzer that automatically chooses the best analysis method
    based on configuration and availability.
    """
    
    def __init__(self, website_id=None, ai_config=None):
        """
        Initialize the unified analyzer.
        
        Args:
            website_id: ID of the website being analyzed (for org-specific config)
            ai_config: Pre-loaded AI configuration dict (optional)
        """
        self.website_id = website_id
        self.ai_config = ai_config
        self.keyword_analyzer = ContentAnalyzer()
        self.ai_analyzer = None
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Initialize analyzers based on organisation-specific configuration."""
        try:
            # Get AI configuration for this website/organisation
            if not self.ai_config and self.website_id:
                self.ai_config = get_ai_config_for_website(self.website_id)
            
            # Fall back to global config if no org-specific config available
            if not self.ai_config:
                self.ai_config = {
                    'ai_enabled': current_app.config.get('AI_ENABLED', False),
                    'ai_analysis_mode': current_app.config.get('AI_ANALYSIS_MODE', 'keyword'),
                    'openai_api_key': current_app.config.get('OPENAI_API_KEY'),
                    'openai_model': current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                    'openai_max_tokens': current_app.config.get('OPENAI_MAX_TOKENS', 1000),
                    'openai_temperature': current_app.config.get('OPENAI_TEMPERATURE', 0.3),
                    'ai_daily_cost_limit': current_app.config.get('AI_DAILY_COST_LIMIT', 10.0),
                    'ai_monthly_cost_limit': current_app.config.get('AI_MONTHLY_COST_LIMIT', 100.0),
                    'local_ai_model': current_app.config.get('LOCAL_AI_MODEL', 'all-MiniLM-L6-v2'),
                    'local_ai_similarity_threshold': current_app.config.get('LOCAL_AI_SIMILARITY_THRESHOLD', 0.5),
                    'ai_confidence_threshold': current_app.config.get('AI_CONFIDENCE_THRESHOLD', 0.3),
                    'ai_content_chunk_size': current_app.config.get('AI_CONTENT_CHUNK_SIZE', 2000)
                }
            
            # Initialize AI analyzer if enabled
            if self.ai_config.get('ai_enabled', False):
                self.ai_analyzer = AIContentAnalyzer(ai_config=self.ai_config)
                logger.info(f"AI analyzer initialized successfully with mode: {self.ai_config.get('ai_analysis_mode')}")
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
        analysis_mode = self.ai_config.get('ai_analysis_mode', 'keyword')
        
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
        analysis_mode = self.ai_config.get('ai_analysis_mode', 'keyword')
        
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
            'current_mode': self.ai_config.get('ai_analysis_mode', 'keyword'),
            'ai_enabled': self.ai_config.get('ai_enabled', False),
            'website_id': self.website_id
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
