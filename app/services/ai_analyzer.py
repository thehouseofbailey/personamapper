import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from flask import current_app
from app.models import Persona, CrawledPage, ContentMapping
from app import db

# Set up logging
logger = logging.getLogger(__name__)

class AIAnalysisError(Exception):
    """Custom exception for AI analysis errors."""
    pass

class CostLimitExceededError(AIAnalysisError):
    """Exception raised when AI cost limits are exceeded."""
    pass

class AIContentAnalyzer:
    """AI-powered content analyzer for persona mapping."""
    
    def __init__(self):
        self.openai_client = None
        self.sentence_transformer = None
        self.daily_cost = 0.0
        self.monthly_cost = 0.0
        self._initialize_ai_services()
    
    def _initialize_ai_services(self):
        """Initialize AI services based on configuration."""
        try:
            # Initialize OpenAI if enabled and API key is available
            if current_app.config.get('AI_ENABLED') and current_app.config.get('OPENAI_API_KEY'):
                try:
                    import openai
                    self.openai_client = openai.OpenAI(
                        api_key=current_app.config['OPENAI_API_KEY']
                    )
                    logger.info("OpenAI client initialized successfully")
                except ImportError:
                    logger.warning("OpenAI package not installed. Install with: pip install openai")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
            
            # Initialize Sentence Transformers for local AI
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                from sklearn.metrics.pairwise import cosine_similarity
                
                model_name = current_app.config.get('LOCAL_AI_MODEL', 'all-MiniLM-L6-v2')
                self.sentence_transformer = SentenceTransformer(model_name)
                self.np = np
                self.cosine_similarity = cosine_similarity
                logger.info(f"Sentence Transformer model '{model_name}' initialized successfully")
            except ImportError:
                logger.warning("Sentence Transformers not installed. Install with: pip install sentence-transformers")
            except Exception as e:
                logger.error(f"Failed to initialize Sentence Transformer: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing AI services: {e}")
    
    def analyze_page(self, page: CrawledPage) -> List[Dict]:
        """
        Analyze a crawled page using AI and return potential persona mappings.
        
        Args:
            page: CrawledPage object to analyze
            
        Returns:
            List of dictionaries containing persona mappings with confidence scores
        """
        if not page.content or len(page.content.strip()) < current_app.config.get('CONTENT_MIN_LENGTH', 100):
            return []
        
        # Get all active personas
        personas = Persona.query.filter_by(is_active=True).all()
        if not personas:
            return []
        
        analysis_mode = current_app.config.get('AI_ANALYSIS_MODE', 'hybrid')
        
        try:
            if analysis_mode == 'ai' and self.openai_client:
                return self._analyze_with_openai(page, personas)
            elif analysis_mode == 'local' and self.sentence_transformer:
                return self._analyze_with_sentence_transformer(page, personas)
            elif analysis_mode == 'hybrid':
                return self._analyze_hybrid(page, personas)
            elif analysis_mode == 'validation':
                return self._analyze_with_validation(page, personas)
            else:
                # Fallback to keyword analysis
                logger.warning(f"AI analysis mode '{analysis_mode}' not available, falling back to keyword analysis")
                return self._fallback_to_keyword_analysis(page, personas)
                
        except CostLimitExceededError:
            logger.warning("AI cost limit exceeded, falling back to keyword analysis")
            return self._fallback_to_keyword_analysis(page, personas)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_to_keyword_analysis(page, personas)
    
    def _analyze_with_openai(self, page: CrawledPage, personas: List[Persona]) -> List[Dict]:
        """Analyze content using OpenAI GPT."""
        if not self.openai_client:
            raise AIAnalysisError("OpenAI client not initialized")
        
        # Check cost limits
        self._check_cost_limits()
        
        # Prepare content for analysis
        content = self._prepare_content_for_analysis(page.content)
        
        # Create prompt
        prompt = self._create_openai_prompt(content, page, personas)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are an expert content analyst specializing in persona mapping for marketing and content strategy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=current_app.config.get('OPENAI_MAX_TOKENS', 1000),
                temperature=current_app.config.get('OPENAI_TEMPERATURE', 0.3)
            )
            
            # Track costs (approximate)
            self._track_openai_cost(response.usage.total_tokens)
            
            # Parse response
            return self._parse_openai_response(response.choices[0].message.content, personas)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIAnalysisError(f"OpenAI analysis failed: {e}")
    
    def _analyze_with_sentence_transformer(self, page: CrawledPage, personas: List[Persona]) -> List[Dict]:
        """Analyze content using local Sentence Transformers."""
        if not self.sentence_transformer:
            raise AIAnalysisError("Sentence Transformer not initialized")
        
        # Prepare content
        content = self._prepare_content_for_analysis(page.content)
        
        # Create embeddings
        content_embedding = self.sentence_transformer.encode([content])
        
        mappings = []
        
        for persona in personas:
            # Create persona description for embedding
            persona_text = self._create_persona_description(persona)
            persona_embedding = self.sentence_transformer.encode([persona_text])
            
            # Calculate similarity
            similarity = self.cosine_similarity(content_embedding, persona_embedding)[0][0]
            
            # Convert similarity to confidence score (0-1)
            confidence_score = max(0.0, min(1.0, similarity))
            
            # Only include if above threshold
            threshold = current_app.config.get('LOCAL_AI_SIMILARITY_THRESHOLD', 0.5)
            if confidence_score > threshold:
                mappings.append({
                    'persona_id': persona.id,
                    'persona_title': persona.title,
                    'confidence_score': confidence_score,
                    'mapping_reason': f"AI semantic similarity: {similarity:.3f}",
                    'mapping_method': 'ai_local'
                })
        
        # Sort by confidence score
        mappings.sort(key=lambda x: x['confidence_score'], reverse=True)
        return mappings
    
    def _analyze_hybrid(self, page: CrawledPage, personas: List[Persona]) -> List[Dict]:
        """Combine AI and keyword analysis for best results."""
        ai_mappings = []
        keyword_mappings = []
        
        # Try AI analysis first
        try:
            if self.openai_client:
                ai_mappings = self._analyze_with_openai(page, personas)
            elif self.sentence_transformer:
                ai_mappings = self._analyze_with_sentence_transformer(page, personas)
        except Exception as e:
            logger.warning(f"AI analysis failed in hybrid mode: {e}")
        
        # Get keyword analysis as fallback/supplement
        keyword_mappings = self._fallback_to_keyword_analysis(page, personas)
        
        # Combine and deduplicate results
        return self._combine_analysis_results(ai_mappings, keyword_mappings)
    
    def _analyze_with_validation(self, page: CrawledPage, personas: List[Persona]) -> List[Dict]:
        """Use AI to validate keyword-based mappings."""
        # Get keyword mappings first
        keyword_mappings = self._fallback_to_keyword_analysis(page, personas)
        
        if not keyword_mappings:
            return []
        
        # Use AI to validate each mapping
        validated_mappings = []
        
        for mapping in keyword_mappings:
            try:
                persona = next(p for p in personas if p.id == mapping['persona_id'])
                ai_confidence = self._validate_mapping_with_ai(page, persona)
                
                # Combine keyword and AI confidence
                combined_confidence = (mapping['confidence_score'] + ai_confidence) / 2
                
                validated_mappings.append({
                    'persona_id': mapping['persona_id'],
                    'persona_title': mapping['persona_title'],
                    'confidence_score': combined_confidence,
                    'mapping_reason': f"Keyword + AI validation: {mapping['mapping_reason']}",
                    'mapping_method': 'ai_validation'
                })
                
            except Exception as e:
                logger.warning(f"AI validation failed for persona {mapping['persona_id']}: {e}")
                # Keep original mapping if validation fails
                validated_mappings.append(mapping)
        
        return validated_mappings
    
    def _create_openai_prompt(self, content: str, page: CrawledPage, personas: List[Persona]) -> str:
        """Create a structured prompt for OpenAI analysis."""
        # Truncate content if too long
        max_content_length = current_app.config.get('AI_CONTENT_CHUNK_SIZE', 2000)
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        personas_info = []
        for persona in personas:
            keywords = ', '.join(persona.get_keywords_list()) if persona.keywords else 'None'
            personas_info.append(f"- {persona.title}: {persona.description} (Keywords: {keywords})")
        
        prompt = f"""
Analyze this web content and determine its relevance to each persona. Provide a confidence score (0-100) and reasoning for each persona.

URL: {page.url}
Title: {page.title or 'No title'}

Content:
{content}

Personas to evaluate:
{chr(10).join(personas_info)}

Please respond in JSON format:
{{
    "analysis": [
        {{
            "persona_title": "Persona Name",
            "confidence": 85,
            "reasoning": "Brief explanation of why this content matches this persona"
        }}
    ]
}}

Only include personas with confidence > 30. Focus on semantic meaning, not just keyword matching.
"""
        return prompt
    
    def _parse_openai_response(self, response_text: str, personas: List[Persona]) -> List[Dict]:
        """Parse OpenAI response and convert to mapping format."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
            else:
                response_data = json.loads(response_text)
            
            mappings = []
            persona_lookup = {p.title: p for p in personas}
            
            for analysis in response_data.get('analysis', []):
                persona_title = analysis.get('persona_title')
                confidence = analysis.get('confidence', 0)
                reasoning = analysis.get('reasoning', 'AI analysis')
                
                if persona_title in persona_lookup and confidence > 30:
                    persona = persona_lookup[persona_title]
                    mappings.append({
                        'persona_id': persona.id,
                        'persona_title': persona.title,
                        'confidence_score': confidence / 100.0,  # Convert to 0-1 scale
                        'mapping_reason': f"AI analysis: {reasoning}",
                        'mapping_method': 'ai_openai'
                    })
            
            return sorted(mappings, key=lambda x: x['confidence_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.debug(f"Response text: {response_text}")
            return []
    
    def _create_persona_description(self, persona: Persona) -> str:
        """Create a text description of a persona for embedding."""
        keywords = ', '.join(persona.get_keywords_list()) if persona.keywords else ''
        return f"{persona.title}: {persona.description}. Keywords: {keywords}"
    
    def _prepare_content_for_analysis(self, content: str) -> str:
        """Clean and prepare content for AI analysis."""
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters but keep basic punctuation
        content = re.sub(r'[^\w\s.,!?;:-]', ' ', content)
        
        return content.strip()
    
    def _fallback_to_keyword_analysis(self, page: CrawledPage, personas: List[Persona]) -> List[Dict]:
        """Fallback to original keyword-based analysis."""
        try:
            from app.services.content_analyzer import ContentAnalyzer
            analyzer = ContentAnalyzer()
            return analyzer.analyze_page(page)
        except Exception as e:
            logger.error(f"Keyword analysis fallback failed: {e}")
            return []
    
    def _combine_analysis_results(self, ai_mappings: List[Dict], keyword_mappings: List[Dict]) -> List[Dict]:
        """Combine AI and keyword analysis results."""
        combined = {}
        
        # Add AI mappings first (higher priority)
        for mapping in ai_mappings:
            persona_id = mapping['persona_id']
            combined[persona_id] = mapping.copy()
            combined[persona_id]['mapping_method'] = 'ai_hybrid'
        
        # Add keyword mappings, combining with AI if exists
        for mapping in keyword_mappings:
            persona_id = mapping['persona_id']
            if persona_id in combined:
                # Combine confidence scores (weighted average)
                ai_confidence = combined[persona_id]['confidence_score']
                keyword_confidence = mapping['confidence_score']
                combined_confidence = (ai_confidence * 0.7) + (keyword_confidence * 0.3)
                
                combined[persona_id]['confidence_score'] = combined_confidence
                combined[persona_id]['mapping_reason'] += f" + {mapping['mapping_reason']}"
            else:
                combined[persona_id] = mapping.copy()
                combined[persona_id]['mapping_method'] = 'keyword_hybrid'
        
        # Convert back to list and sort
        result = list(combined.values())
        result.sort(key=lambda x: x['confidence_score'], reverse=True)
        return result
    
    def _validate_mapping_with_ai(self, page: CrawledPage, persona: Persona) -> float:
        """Use AI to validate a single persona mapping."""
        if not self.openai_client:
            return 0.5  # Default confidence if AI not available
        
        content = self._prepare_content_for_analysis(page.content[:1000])  # Shorter for validation
        
        prompt = f"""
Rate how relevant this content is to the persona "{persona.title}" on a scale of 0-100.

Persona: {persona.title}
Description: {persona.description}
Keywords: {', '.join(persona.get_keywords_list()) if persona.keywords else 'None'}

Content: {content}

Respond with just a number (0-100):
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            # Extract number from response
            score_text = response.choices[0].message.content.strip()
            score = float(re.search(r'\d+', score_text).group()) / 100.0
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"AI validation failed: {e}")
            return 0.5
    
    def _check_cost_limits(self):
        """Check if AI usage is within cost limits."""
        daily_limit = current_app.config.get('AI_DAILY_COST_LIMIT', 10.0)
        monthly_limit = current_app.config.get('AI_MONTHLY_COST_LIMIT', 100.0)
        
        if self.daily_cost > daily_limit:
            raise CostLimitExceededError(f"Daily cost limit exceeded: ${self.daily_cost:.2f} > ${daily_limit}")
        
        if self.monthly_cost > monthly_limit:
            raise CostLimitExceededError(f"Monthly cost limit exceeded: ${self.monthly_cost:.2f} > ${monthly_limit}")
    
    def _track_openai_cost(self, tokens: int):
        """Track approximate OpenAI API costs."""
        # Approximate cost calculation (GPT-3.5-turbo pricing)
        cost_per_1k_tokens = 0.002  # $0.002 per 1K tokens
        cost = (tokens / 1000) * cost_per_1k_tokens
        
        self.daily_cost += cost
        self.monthly_cost += cost
        
        logger.debug(f"OpenAI API call cost: ${cost:.4f} (tokens: {tokens})")
    
    def create_mappings(self, page: CrawledPage, mappings: List[Dict]) -> List[ContentMapping]:
        """
        Create ContentMapping objects from AI analysis results.
        
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
                    existing_mapping.mapping_method = mapping_data['mapping_method']
                    created_mappings.append(existing_mapping)
            else:
                # Create new mapping
                new_mapping = ContentMapping(
                    page_id=page.id,
                    persona_id=mapping_data['persona_id'],
                    confidence_score=mapping_data['confidence_score'],
                    mapping_reason=mapping_data['mapping_reason'],
                    mapping_method=mapping_data['mapping_method'],
                    crawl_timestamp=datetime.utcnow()
                )
                db.session.add(new_mapping)
                created_mappings.append(new_mapping)
        
        return created_mappings
    
    def process_page(self, page: CrawledPage) -> int:
        """
        Process a single page: analyze with AI and create mappings.
        
        Args:
            page: CrawledPage object to process
            
        Returns:
            Number of mappings created
        """
        try:
            # Analyze the page with AI
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
    
    def get_analysis_stats(self) -> Dict:
        """Get statistics about AI analysis usage."""
        return {
            'ai_enabled': current_app.config.get('AI_ENABLED', False),
            'analysis_mode': current_app.config.get('AI_ANALYSIS_MODE', 'hybrid'),
            'openai_available': self.openai_client is not None,
            'local_ai_available': self.sentence_transformer is not None,
            'daily_cost': self.daily_cost,
            'monthly_cost': self.monthly_cost,
            'daily_limit': current_app.config.get('AI_DAILY_COST_LIMIT', 10.0),
            'monthly_limit': current_app.config.get('AI_MONTHLY_COST_LIMIT', 100.0)
        }
