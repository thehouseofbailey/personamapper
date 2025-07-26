import re
from typing import List, Dict, Tuple
from flask import current_app
from app.models import Persona, CrawledPage, ContentMapping
from app import db

class ContentAnalyzer:
    """Service for analyzing content and mapping it to personas."""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
    
    def analyze_page(self, page: CrawledPage) -> List[Dict]:
        """
        Analyze a crawled page and return potential persona mappings.
        
        Args:
            page: CrawledPage object to analyze
            
        Returns:
            List of dictionaries containing persona mappings with confidence scores
        """
        if not page.content or len(page.content.strip()) < 50:
            return []
        
        # Get all active personas
        personas = Persona.query.filter_by(is_active=True).all()
        if not personas:
            return []
        
        mappings = []
        content_words = self._extract_content_words(page.content)
        
        for persona in personas:
            confidence_score, reason = self._calculate_persona_match(
                content_words, persona, page
            )
            
            if confidence_score > 0.1:  # Only include mappings with some confidence
                mappings.append({
                    'persona_id': persona.id,
                    'persona_title': persona.title,
                    'confidence_score': confidence_score,
                    'mapping_reason': reason,
                    'mapping_method': 'keyword'
                })
        
        # Sort by confidence score (highest first)
        mappings.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return mappings
    
    def create_mappings(self, page: CrawledPage, mappings: List[Dict]) -> List[ContentMapping]:
        """
        Create ContentMapping objects from analysis results.
        
        Args:
            page: CrawledPage object
            mappings: List of mapping dictionaries from analyze_page
            
        Returns:
            List of created ContentMapping objects
        """
        created_mappings = []
        
        for mapping_data in mappings:
            # Check if mapping already exists
            existing_mapping = ContentMapping.query.filter_by(
                page_id=page.id,
                persona_id=mapping_data['persona_id'],
                is_active=True
            ).first()
            
            if existing_mapping:
                # Update existing mapping if confidence is higher
                if mapping_data['confidence_score'] > existing_mapping.confidence_score:
                    existing_mapping.update_confidence(
                        mapping_data['confidence_score'],
                        mapping_data['mapping_reason']
                    )
                    created_mappings.append(existing_mapping)
            else:
                # Create new mapping
                new_mapping = ContentMapping(
                    page_id=page.id,
                    persona_id=mapping_data['persona_id'],
                    confidence_score=mapping_data['confidence_score'],
                    mapping_reason=mapping_data['mapping_reason'],
                    mapping_method=mapping_data['mapping_method']
                )
                db.session.add(new_mapping)
                created_mappings.append(new_mapping)
        
        return created_mappings
    
    def _extract_content_words(self, content: str) -> List[str]:
        """Extract and clean words from content."""
        # Remove HTML tags if any
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Remove stop words
        words = [word for word in words if word not in self.stop_words]
        
        return words
    
    def _calculate_persona_match(self, content_words: List[str], persona: Persona, page: CrawledPage) -> Tuple[float, str]:
        """
        Calculate how well content matches a persona.
        
        Args:
            content_words: List of words from the content
            persona: Persona object to match against
            page: CrawledPage object for additional context
            
        Returns:
            Tuple of (confidence_score, reason)
        """
        if not content_words:
            return 0.0, "No content to analyze"
        
        persona_keywords = persona.get_keywords_list()
        if not persona_keywords:
            return 0.0, "No keywords defined for persona"
        
        # Convert persona keywords to lowercase for matching
        persona_keywords_lower = [kw.lower().strip() for kw in persona_keywords]
        
        # Count keyword matches
        matches = []
        total_keyword_score = 0
        
        for keyword in persona_keywords_lower:
            # Check for exact keyword matches
            keyword_count = content_words.count(keyword)
            if keyword_count > 0:
                matches.append(f"'{keyword}' ({keyword_count}x)")
                total_keyword_score += keyword_count
            
            # Check for partial matches in multi-word keywords
            elif ' ' in keyword:
                keyword_parts = keyword.split()
                if all(part in content_words for part in keyword_parts):
                    matches.append(f"'{keyword}' (partial)")
                    total_keyword_score += 0.5
        
        if not matches:
            return 0.0, "No keyword matches found"
        
        # Calculate base confidence score
        unique_matches = len(matches)
        total_keywords = len(persona_keywords_lower)
        
        # Base score: percentage of keywords that matched
        base_score = unique_matches / total_keywords
        
        # Boost score based on frequency of matches
        frequency_boost = min(total_keyword_score / len(content_words), 0.3)
        
        # Title and URL bonus
        title_bonus = 0
        if page.title:
            title_words = self._extract_content_words(page.title)
            title_matches = sum(1 for kw in persona_keywords_lower if kw in title_words)
            title_bonus = (title_matches / len(persona_keywords_lower)) * 0.2
        
        url_bonus = 0
        if page.url:
            url_words = self._extract_content_words(page.url)
            url_matches = sum(1 for kw in persona_keywords_lower if kw in url_words)
            url_bonus = (url_matches / len(persona_keywords_lower)) * 0.1
        
        # Final confidence score (capped at 1.0)
        confidence_score = min(base_score + frequency_boost + title_bonus + url_bonus, 1.0)
        
        # Create reason string
        reason = f"Matched keywords: {', '.join(matches[:5])}"  # Limit to first 5 matches
        if len(matches) > 5:
            reason += f" and {len(matches) - 5} more"
        
        if title_bonus > 0:
            reason += " (title match)"
        if url_bonus > 0:
            reason += " (URL match)"
        
        return confidence_score, reason
    
    def process_page(self, page: CrawledPage) -> int:
        """
        Process a single page: analyze and create mappings.
        
        Args:
            page: CrawledPage object to process
            
        Returns:
            Number of mappings created
        """
        try:
            # Analyze the page
            mappings = self.analyze_page(page)
            
            if mappings:
                # Create mappings in database
                created_mappings = self.create_mappings(page, mappings)
                
                # Mark page as processed
                page.mark_as_processed()
                
                # Update word count
                page.calculate_word_count()
                
                db.session.commit()
                
                return len(created_mappings)
            else:
                # Mark as processed even if no mappings found
                page.mark_as_processed()
                page.calculate_word_count()
                db.session.commit()
                
                return 0
                
        except Exception as e:
            # Mark page as processed with error
            page.mark_as_processed(str(e))
            db.session.commit()
            raise e
    
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
            'errors': 0
        }
        
        for page in pages:
            try:
                mappings_count = self.process_page(page)
                stats['processed'] += 1
                stats['mappings_created'] += mappings_count
            except Exception as e:
                stats['errors'] += 1
                print(f"Error processing page {page.url}: {str(e)}")
        
        return stats
    
    def analyze_content_for_persona(self, content: str, persona: Persona) -> Dict:
        """
        Analyze content for a specific persona and return mapping decision.
        
        Args:
            content: Text content to analyze
            persona: Persona object to match against
            
        Returns:
            Dictionary with mapping decision and details
        """
        if not content or len(content.strip()) < 50:
            return {
                'should_map': False,
                'confidence': 0.0,
                'reason': 'Content too short to analyze'
            }
        
        if not persona.keywords:
            return {
                'should_map': False,
                'confidence': 0.0,
                'reason': 'No keywords defined for persona'
            }
        
        # Extract words from content
        content_words = self._extract_content_words(content)
        
        if not content_words:
            return {
                'should_map': False,
                'confidence': 0.0,
                'reason': 'No meaningful words found in content'
            }
        
        # Get persona keywords
        persona_keywords = persona.get_keywords_list()
        persona_keywords_lower = [kw.lower().strip() for kw in persona_keywords]
        
        # Count keyword matches
        matches = []
        total_keyword_score = 0
        
        for keyword in persona_keywords_lower:
            # Check for exact keyword matches
            keyword_count = content_words.count(keyword)
            if keyword_count > 0:
                matches.append(f"'{keyword}' ({keyword_count}x)")
                total_keyword_score += keyword_count
            
            # Check for partial matches in multi-word keywords
            elif ' ' in keyword:
                keyword_parts = keyword.split()
                if all(part in content_words for part in keyword_parts):
                    matches.append(f"'{keyword}' (partial)")
                    total_keyword_score += 0.5
        
        if not matches:
            return {
                'should_map': False,
                'confidence': 0.0,
                'reason': 'No keyword matches found'
            }
        
        # Calculate confidence score
        unique_matches = len(matches)
        total_keywords = len(persona_keywords_lower)
        
        # Base score: percentage of keywords that matched
        base_score = unique_matches / total_keywords
        
        # Boost score based on frequency of matches
        frequency_boost = min(total_keyword_score / len(content_words), 0.3)
        
        # Final confidence score (capped at 1.0)
        confidence_score = min(base_score + frequency_boost, 1.0)
        
        # Create reason string
        reason = f"Matched keywords: {', '.join(matches[:5])}"
        if len(matches) > 5:
            reason += f" and {len(matches) - 5} more"
        
        # Decide whether to map (threshold of 0.1)
        should_map = confidence_score > 0.1
        
        return {
            'should_map': should_map,
            'confidence': confidence_score,
            'reason': reason
        }
