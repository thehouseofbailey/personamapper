# AI Configuration Migration Summary

## Overview

Successfully migrated AI configuration from global `.env` settings to **organisation-specific database configuration**. This allows each organisation to have independent AI analysis settings, API keys, and cost limits.

## Files Modified

### 🗄️ Database Changes
- **Migration**: `migrations/add_ai_config_to_organisations.py`
  - Added 12 AI configuration fields to `organisations` table
  - Preserved backward compatibility with existing data

### 🏗️ Model Changes
- **`app/models/organisation.py`**
  - Added AI configuration fields to Organisation model
  - Added `get_ai_config()` and `update_ai_config()` methods
  - Updated `to_dict()` to include AI status

### 🔧 Service Layer Updates
- **`app/services/ai_config_service.py`** *(NEW)*
  - Utility functions for accessing organisation-specific AI config
  - `get_ai_config_for_organisation()` - Get config by org ID
  - `get_ai_config_for_website()` - Get config by website ID
  - Configuration validation helpers

- **`app/services/unified_analyzer.py`**
  - Updated constructor to accept `website_id` and `ai_config` parameters
  - Modified `_initialize_analyzers()` to use organisation-specific config
  - Updated all analysis methods to use org-specific settings
  - Added fallback to global config for backward compatibility

- **`app/services/ai_analyzer.py`**
  - Updated constructor to accept `ai_config` parameter
  - Modified all config references to use organisation-specific values
  - Updated OpenAI client initialization with org-specific API keys
  - Updated cost limit checks with org-specific limits

- **`app/services/web_crawler.py`**
  - Modified to initialize `UnifiedContentAnalyzer` with website-specific config
  - Added safety checks for content analyzer availability
  - Analyzer now gets correct AI settings based on crawl job's website

### 🌐 Route & Form Changes
- **`app/routes/organisations.py`**
  - Added `/organisations/<id>/ai-config` route
  - Comprehensive AI configuration form handling
  - Permission checks (org admin required)
  - Form validation and error handling

- **`app/routes/api.py`**
  - Updated `/ai/status` endpoint to accept optional `website_id` parameter
  - Updated `/analyze/content` endpoint to use website-specific AI config
  - Added organisation-aware analysis capabilities

- **`app/forms/organisation_forms.py`** *(NEW)*
  - `AIConfigForm` - Comprehensive form for AI settings
  - Custom validation for OpenAI requirements
  - Range validation for all numeric fields

### 🎨 Template Changes
- **`app/templates/organisations/ai_config.html`** *(NEW)*
  - Beautiful, responsive AI configuration interface
  - Real-time range slider updates
  - Conditional UI sections based on AI mode
  - Current configuration preview panel
  - Helpful tips and guidance

- **`app/templates/organisations/view.html`**
  - Added "AI Config" button for organisation managers
  - Updated quick stats to show AI status (Enabled/Disabled + Mode)

### 📄 Configuration Files
- **`.env`**
  - Commented out deprecated AI settings
  - Added deprecation notices pointing to new org-specific config

- **`AI_INTEGRATION_README.md`**
  - Updated documentation for new organisation-specific approach
  - Added code examples for accessing org-specific config

## New AI Configuration Fields

Each organisation now has these configurable AI settings:

```sql
-- Basic Settings
ai_enabled BOOLEAN DEFAULT 0
ai_analysis_mode TEXT DEFAULT 'keyword'

-- OpenAI Settings  
openai_api_key TEXT
openai_model TEXT DEFAULT 'gpt-3.5-turbo'
openai_max_tokens INTEGER DEFAULT 1000
openai_temperature REAL DEFAULT 0.3

-- Cost Controls
ai_daily_cost_limit REAL DEFAULT 10.0
ai_monthly_cost_limit REAL DEFAULT 100.0

-- Local AI Settings
local_ai_model TEXT DEFAULT 'all-MiniLM-L6-v2'
local_ai_similarity_threshold REAL DEFAULT 0.5

-- General Settings
ai_confidence_threshold REAL DEFAULT 0.3
ai_content_chunk_size INTEGER DEFAULT 2000
```

## AI Analysis Modes

1. **Keyword**: Traditional keyword matching (free, fast)
2. **Local AI**: Sentence transformers (free, requires processing power)
3. **OpenAI GPT**: Full GPT analysis (requires API key, costs money)
4. **Hybrid**: Combines keyword + AI approaches
5. **Validation**: AI validates keyword matches (lower cost)

## Usage Examples

### Get Organisation AI Config
```python
from app.services.ai_config_service import get_ai_config_for_organisation

config = get_ai_config_for_organisation(org_id)
if config['ai_enabled']:
    # Use AI features with org-specific settings
    mode = config['ai_analysis_mode']
    api_key = config['openai_api_key']
```

### Website-Based AI Config
```python
from app.services.ai_config_service import get_ai_config_for_website

config = get_ai_config_for_website(website_id)
if config and config['ai_enabled']:
    # Perform AI analysis using website's organisation settings
```

### Content Analysis with Organisation Config
```python
from app.services.unified_analyzer import UnifiedContentAnalyzer

# Analyzer automatically uses website's organisation AI config
analyzer = UnifiedContentAnalyzer(website_id=website_id)
mappings = analyzer.analyze_page(page)
```

## Benefits Achieved

✅ **Multi-tenant AI Configuration**: Each org has independent settings  
✅ **Cost Management**: Individual cost limits per organisation  
✅ **Security**: API keys isolated per organisation  
✅ **Flexibility**: Different AI modes per organisation  
✅ **Scalability**: No global configuration bottlenecks  
✅ **User Experience**: Intuitive web-based configuration  
✅ **Backward Compatibility**: Falls back to global config if needed  

## Migration Impact

- **Zero Downtime**: All existing functionality preserved
- **Graceful Fallback**: Falls back to global config for compatibility
- **Default Values**: New organisations start with sensible defaults
- **Data Integrity**: All existing organisations get default AI settings

## Next Steps

1. **Organisation Admins** can now configure AI settings via: `/organisations/<id>/ai-config`
2. **Crawl Jobs** will automatically use their website's organisation AI settings
3. **API Endpoints** support organisation-specific AI configuration
4. **Cost Tracking** can be implemented per-organisation
5. **Global `.env` AI Settings** can be completely removed in future versions

## Testing

The system maintains full backward compatibility while adding the new organisation-specific functionality. All AI analysis now respects organisation boundaries and uses appropriate configuration for each context.
