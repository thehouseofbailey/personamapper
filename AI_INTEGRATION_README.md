# Organisation-Specific AI Configuration

## AI Integration Guide (Updated for Organisation-Specific Config)

PersonaMap supports multiple AI analysis modes to automatically map website content to personas, with each organisation able to configure their own settings:

1. **Keyword Matching** - Fast rule-based matching using persona keywords
2. **Local AI** - Free local sentence transformers (no API required)
3. **AI Analysis** - GPT-powered content analysis (per-organisation API keys)
4. **Hybrid Mode** - Combines keyword + AI for best accuracy
5. **Validation Mode** - Uses AI to validate keyword matches

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New AI dependencies include:
- `openai>=1.0.0` - For OpenAI GPT integration
- `sentence-transformers>=2.2.0` - For local AI analysis
- `tiktoken>=0.5.0` - For token counting
- `numpy>=1.21.0` - For numerical operations
- `scikit-learn>=1.0.0` - For similarity calculations

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` to configure AI settings:

```bash
## Configuration (Per-Organisation)

### Accessing AI Configuration

1. Navigate to an organisation: `http://localhost:8080/organisations/<id>`
2. Click the **"AI Config"** button (requires organisation management permissions)
3. Configure AI settings for that specific organisation

### Database Fields

AI configuration is stored in the `organisations` table:

```sql
-- Basic AI Settings
ai_enabled BOOLEAN DEFAULT 0
ai_analysis_mode TEXT DEFAULT 'keyword'

-- OpenAI Configuration
openai_api_key TEXT
openai_model TEXT DEFAULT 'gpt-3.5-turbo'
openai_max_tokens INTEGER DEFAULT 1000
openai_temperature REAL DEFAULT 0.3

-- Cost Controls
ai_daily_cost_limit REAL DEFAULT 10.0
ai_monthly_cost_limit REAL DEFAULT 100.0

-- Local AI Configuration
local_ai_model TEXT DEFAULT 'all-MiniLM-L6-v2'
local_ai_similarity_threshold REAL DEFAULT 0.5

-- General Settings
ai_confidence_threshold REAL DEFAULT 0.3
ai_content_chunk_size INTEGER DEFAULT 2000
```

### Using AI Configuration in Code

```python
from app.services.ai_config_service import get_ai_config_for_organisation

# Get AI config for specific organisation
config = get_ai_config_for_organisation(organisation_id)
if config['ai_enabled']:
    # Perform AI analysis using organisation's settings
    pass
```
```

### 3. Start the Application

```bash
python run.py
```

## Analysis Modes

### Keyword Mode (Default)
- **Description**: Traditional keyword matching
- **Pros**: Fast, free, no external dependencies
- **Cons**: Limited accuracy, no semantic understanding
- **Setup**: No additional configuration needed

```bash
AI_ENABLED=false
AI_ANALYSIS_MODE=keyword
```

### AI Mode (OpenAI)
- **Description**: Uses OpenAI GPT for semantic content analysis
- **Pros**: High accuracy, semantic understanding, natural language reasoning
- **Cons**: Costs money, requires internet, slower
- **Setup**: Requires OpenAI API key

```bash
AI_ENABLED=true
AI_ANALYSIS_MODE=ai
OPENAI_API_KEY=your-key-here
```

### Hybrid Mode (Recommended)
- **Description**: Combines AI and keyword analysis
- **Pros**: Best accuracy, fallback to keywords if AI fails
- **Cons**: Moderate cost, complexity
- **Setup**: Requires OpenAI API key

```bash
AI_ENABLED=true
AI_ANALYSIS_MODE=hybrid
OPENAI_API_KEY=your-key-here
```

### Local AI Mode
- **Description**: Uses local Sentence Transformers
- **Pros**: Privacy-focused, no API costs, offline capable
- **Cons**: Lower accuracy than GPT, requires more memory
- **Setup**: No API key needed

```bash
AI_ENABLED=true
AI_ANALYSIS_MODE=local
LOCAL_AI_MODEL=all-MiniLM-L6-v2
```

### Validation Mode
- **Description**: AI validates keyword-based mappings
- **Pros**: Improves keyword accuracy, cost-effective
- **Cons**: Still limited by keyword matching
- **Setup**: Requires OpenAI API key

```bash
AI_ENABLED=true
AI_ANALYSIS_MODE=validation
OPENAI_API_KEY=your-key-here
```

## Configuration Options

### OpenAI Settings

```bash
OPENAI_API_KEY=your-key-here          # Required for OpenAI modes
OPENAI_MODEL=gpt-3.5-turbo            # Model to use (gpt-3.5-turbo, gpt-4)
OPENAI_MAX_TOKENS=1000                # Maximum tokens per request
OPENAI_TEMPERATURE=0.3                # Creativity level (0.0-1.0)
```

### Cost Controls

```bash
AI_DAILY_COST_LIMIT=10.0              # Daily spending limit (USD)
AI_MONTHLY_COST_LIMIT=100.0           # Monthly spending limit (USD)
```

### Local AI Settings

```bash
LOCAL_AI_MODEL=all-MiniLM-L6-v2       # Sentence transformer model
LOCAL_AI_SIMILARITY_THRESHOLD=0.5     # Minimum similarity score
```

### Analysis Settings

```bash
AI_CONFIDENCE_THRESHOLD=0.3           # Minimum confidence for mappings
AI_CONTENT_CHUNK_SIZE=2000            # Max characters per AI request
```

## API Endpoints

### Check AI Status
```bash
GET /api/ai/status
```

Returns current AI configuration and availability.

### Analyze Content
```bash
POST /api/ai/analyze
Content-Type: application/json

{
  "content": "Your content to analyze",
  "url": "https://example.com/page",
  "title": "Page Title"
}
```

Returns persona mappings with confidence scores and analysis method used.

## How It Works

### AI Analysis Process

1. **Content Preparation**: Text is cleaned and prepared for analysis
2. **Persona Matching**: Content is analyzed against all active personas
3. **Confidence Scoring**: Each mapping gets a confidence score (0-1)
4. **Method Tracking**: System tracks which analysis method was used
5. **Fallback Handling**: If AI fails, system falls back to keyword analysis

### Prompt Engineering (OpenAI)

The system uses structured prompts that include:
- Page content (truncated if too long)
- Persona descriptions and keywords
- Instructions for JSON response format
- Confidence scoring guidelines

### Local AI (Sentence Transformers)

- Creates embeddings for content and persona descriptions
- Uses cosine similarity to calculate relevance scores
- Configurable similarity thresholds
- No external API calls required

## Cost Management

### OpenAI Costs

- Approximate cost: $0.002 per 1K tokens
- Average page analysis: $0.01-0.05
- Daily/monthly limits prevent overspending
- Cost tracking in application logs

### Cost Optimization Tips

1. Use `hybrid` mode for best cost/accuracy balance
2. Set appropriate `AI_CONTENT_CHUNK_SIZE` (default: 2000 chars)
3. Configure `AI_CONFIDENCE_THRESHOLD` to filter low-quality results
4. Monitor costs via `/api/ai/status` endpoint
5. Use `local` mode for high-volume, privacy-sensitive applications

## Troubleshooting

### Common Issues

**AI not working**
- Check `AI_ENABLED=true` in `.env`
- Verify OpenAI API key is valid
- Check internet connection for OpenAI modes
- Review application logs for error messages

**High costs**
- Reduce `AI_CONTENT_CHUNK_SIZE`
- Increase `AI_CONFIDENCE_THRESHOLD`
- Lower daily/monthly limits
- Switch to `local` or `validation` mode

**Poor accuracy**
- Try `hybrid` mode for best results
- Improve persona descriptions and keywords
- Adjust `OPENAI_TEMPERATURE` (lower = more focused)
- Use GPT-4 model for better accuracy (higher cost)

**Local AI memory issues**
- Use smaller model: `all-MiniLM-L6-v2` (default)
- Reduce batch sizes in crawler
- Monitor system memory usage

### Logs and Monitoring

Check application logs for:
- AI initialization status
- Cost tracking information
- Analysis method fallbacks
- Error messages and warnings

### Performance Tips

1. **Batch Processing**: Process multiple pages together when possible
2. **Caching**: Results are cached to avoid re-analysis
3. **Incremental Mode**: Use incremental crawling to avoid re-processing
4. **Resource Limits**: Set appropriate memory and CPU limits

## Migration from Keyword-Only

Existing PersonaMap installations can enable AI gradually:

1. **Start with Validation Mode**: Improves existing keyword mappings
2. **Test with Hybrid Mode**: Compare results with keyword-only
3. **Monitor Costs**: Track spending and adjust limits
4. **Full AI Mode**: Switch when confident in results and costs

## Security Considerations

### API Key Security
- Store OpenAI API keys in environment variables, never in code
- Use `.env` files that are excluded from version control
- Rotate API keys regularly
- Monitor API usage for unusual activity

### Data Privacy
- **OpenAI Mode**: Content is sent to OpenAI servers for analysis
- **Local Mode**: All processing happens locally, no external data transfer
- **Hybrid/Validation**: Only uses OpenAI when necessary
- Consider data sensitivity when choosing analysis modes

### Cost Protection
- Set daily and monthly spending limits
- Monitor usage via API endpoints
- Implement additional rate limiting if needed
- Use local mode for sensitive or high-volume content

## Examples

### Basic Setup (Keyword Only)
```bash
# .env
AI_ENABLED=false
AI_ANALYSIS_MODE=keyword
```

### OpenAI Integration
```bash
# .env
AI_ENABLED=true
AI_ANALYSIS_MODE=hybrid
OPENAI_API_KEY=sk-your-key-here
AI_DAILY_COST_LIMIT=5.0
```

### Privacy-Focused Setup
```bash
# .env
AI_ENABLED=true
AI_ANALYSIS_MODE=local
LOCAL_AI_MODEL=all-MiniLM-L6-v2
```

### Testing AI Analysis
```bash
# Test the AI status endpoint
curl http://localhost:8080/api/ai/status

# Test content analysis
curl -X POST http://localhost:8080/api/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This article discusses API development best practices for software engineers and technical teams.",
    "title": "API Development Guide"
  }'
```

## Support

For issues with AI integration:

1. Check the application logs for error messages
2. Verify your configuration in `.env`
3. Test with the `/api/ai/status` endpoint
4. Start with `keyword` mode and gradually enable AI features
5. Monitor costs and performance metrics

The AI integration is designed to enhance PersonaMap's accuracy while maintaining backward compatibility with existing keyword-based analysis.
