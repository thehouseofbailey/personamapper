# PersonaMap API Documentation

## Overview

The PersonaMap API provides a lightweight, secure, read-only interface for retrieving persona data and predictions. It's designed to be used by JavaScript applications, particularly through Google Tag Manager, without exposing sensitive keys or credentials.

## Base URL

All API endpoints are prefixed with `/api`

## Authentication

Currently, the API uses basic request validation without requiring API keys. This makes it suitable for client-side JavaScript usage. For production environments, you may want to enhance the `validate_api_request()` function in `app/routes/api.py` to implement:

- Domain-based restrictions
- Rate limiting
- API key validation
- Request signing

## Endpoints

### 1. Get Page Personas

**Endpoint:** `GET /api/personas/page`

Retrieves personas matched to a specific page URL.

**Query Parameters:**
- `url` (required): The page URL to get personas for
- `min_confidence` (optional): Minimum confidence score (default: 0.6)
- `limit` (optional): Maximum number of personas to return (default: 10)

**Example Request:**
```
GET /api/personas/page?url=https://example.com/products&min_confidence=0.7&limit=5
```

**Example Response:**
```json
{
  "url": "https://example.com/products",
  "page_title": "Our Products",
  "personas": [
    {
      "id": 1,
      "title": "Tech Enthusiast",
      "description": "Early adopters who love new technology",
      "keywords": ["technology", "innovation", "gadgets"],
      "confidence_score": 0.85,
      "confidence_level": "High",
      "mapping_method": "keyword",
      "is_verified": true
    }
  ],
  "total_found": 1
}
```

### 2. Predict User Persona

**Endpoint:** `POST /api/personas/predict`

Predicts user persona based on visited pages during a session.

**Request Body:**
```json
{
  "visited_urls": ["url1", "url2", "url3"],
  "session_id": "optional_session_identifier",
  "min_confidence": 0.6,
  "prediction_method": "weighted"
}
```

**Parameters:**
- `visited_urls` (required): Array of URLs visited during the session
- `session_id` (optional): Session identifier for tracking
- `min_confidence` (optional): Minimum confidence score for page mappings (default: 0.6)
- `prediction_method` (optional): "weighted" or "frequency" (default: "weighted")

**Prediction Methods:**
- **weighted**: Uses weighted average of confidence scores with frequency boost
- **frequency**: Based on how often persona appears across visited pages

**Example Response:**
```json
{
  "session_id": "pm_1234567890_abc123",
  "predicted_personas": [
    {
      "id": 1,
      "title": "Tech Enthusiast",
      "description": "Early adopters who love new technology",
      "keywords": ["technology", "innovation", "gadgets"],
      "prediction_score": 0.78,
      "page_appearances": 3,
      "avg_confidence": 0.82
    }
  ],
  "confidence": 0.78,
  "method": "weighted",
  "pages_analyzed": 5,
  "total_pages_submitted": 7,
  "page_details": [
    {
      "url": "https://example.com/tech",
      "title": "Tech News",
      "personas": [
        {
          "id": 1,
          "title": "Tech Enthusiast",
          "confidence": 0.85
        }
      ]
    }
  ]
}
```

### 3. List All Personas

**Endpoint:** `GET /api/personas/list`

Returns a list of all active personas.

**Query Parameters:**
- `limit` (optional): Maximum number of personas to return (default: 50)

**Example Response:**
```json
{
  "personas": [
    {
      "id": 1,
      "title": "Tech Enthusiast",
      "description": "Early adopters who love new technology",
      "keywords": ["technology", "innovation", "gadgets"],
      "mapping_count": 25
    }
  ],
  "total_found": 1
}
```

### 4. Health Check

**Endpoint:** `GET /api/health`

Simple health check endpoint.

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": 1704067200,
  "version": "1.0.0"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (missing required parameters)
- `403`: Forbidden (request validation failed)
- `500`: Internal Server Error

## JavaScript Client Library

### Basic Usage

```html
<!-- Include the client library -->
<script src="personamap-client.js"></script>

<script>
// Auto-initialization (default behavior)
// The library will automatically start tracking when the page loads

// Access the global instance
const pm = window.personaMapInstance;

// Listen for events
pm.on('onPagePersonas', function(data) {
    console.log('Page personas:', data.personas);
});

pm.on('onPersonaPrediction', function(data) {
    console.log('Predicted personas:', data.predicted_personas);
});

pm.on('onError', function(error) {
    console.error('PersonaMap error:', error);
});

// Get current page personas
pm.getCurrentPagePersonas(); // Returns cached data

// Get predicted personas
pm.getPredictedPersonas(); // Returns cached data

// Manual refresh
pm.refreshCurrentPage().then(data => {
    console.log('Refreshed page personas:', data);
});

pm.refreshPrediction().then(data => {
    console.log('Refreshed prediction:', data);
});
</script>
```

### Manual Initialization

```html
<script>
// Disable auto-initialization
window.PERSONAMAP_AUTO_INIT = false;
</script>
<script src="personamap-client.js"></script>

<script>
// Manual initialization with custom config
const pm = new PersonaMap({
    apiBaseUrl: 'https://your-domain.com/api',
    debounceDelay: 2000,
    maxStoredPages: 100
});
</script>
```

### Google Tag Manager Integration

#### Automatic DataLayer Integration

The PersonaMap client automatically pushes persona predictions to the DataLayer with the following structure:

```javascript
// Persona prediction event
{
  'event': 'personaPredictionUpdate',
  'predictedPersona': 'Tech Buyers',
  'personaConfidence': 0.78,
  'personaTimestamp': 1704067200000,
  'personaSessionId': 'pm_1234567890_abc123',
  'personaPagesAnalyzed': 5
}

// Simple variable for easy access
{
  'predictedPersona': 'Tech Buyers'
}
```

#### Custom HTML Tag

```html
<script>
// Set configuration before loading the library
window.PERSONAMAP_API_URL = '{{API Base URL}}'; // GTM variable
window.PERSONAMAP_AUTO_INIT = true;
</script>
<script src="{{PersonaMap Client URL}}"></script>

<script>
// The library automatically pushes to dataLayer
// You can also listen for events if needed
document.addEventListener('DOMContentLoaded', function() {
    const pm = window.personaMapInstance;
    
    pm.on('onPersonaPrediction', function(data) {
        console.log('Persona prediction updated:', data);
        // Additional custom logic here if needed
    });
});
</script>
```

#### GTM Trigger Setup

Create a Custom Event trigger in GTM:
- **Trigger Type**: Custom Event
- **Event Name**: `personaPredictionUpdate`
- **This trigger fires on**: All Custom Events

#### GTM Variables

Create these Built-in Variables or Custom Variables:
- `{{predictedPersona}}` - The predicted persona name
- `{{personaConfidence}}` - Confidence score (0-1)
- `{{personaTimestamp}}` - When prediction was made
- `{{personaSessionId}}` - Session identifier
- `{{personaPagesAnalyzed}}` - Number of pages analyzed

#### Google Analytics 4 Tag Example

```javascript
// GA4 Event Tag triggered by personaPredictionUpdate
gtag('event', 'persona_identified', {
  'persona_name': '{{predictedPersona}}',
  'confidence_score': '{{personaConfidence}}',
  'pages_analyzed': '{{personaPagesAnalyzed}}',
  'session_id': '{{personaSessionId}}'
});

// Set custom dimension
gtag('config', 'GA_MEASUREMENT_ID', {
  'custom_map': {
    'dimension1': '{{predictedPersona}}'
  }
});
```

#### Custom JavaScript Variable (GTM)

```javascript
function() {
    // Get current predicted personas
    if (window.personaMapInstance) {
        const prediction = window.personaMapInstance.getPredictedPersonas();
        if (prediction && prediction.predicted_personas.length > 0) {
            return prediction.predicted_personas[0].title;
        }
    }
    return 'Unknown';
}
```

### Advanced Usage

#### Custom Event Tracking

```javascript
const pm = new PersonaMap();

pm.on('onPersonaPrediction', function(data) {
    // Custom business logic
    if (data.confidence > 0.8) {
        // High confidence prediction
        showPersonalizedContent(data.predicted_personas[0]);
    }
    
    // Send to your analytics platform
    analytics.track('Persona Predicted', {
        persona: data.predicted_personas[0]?.title,
        confidence: data.confidence,
        pages_analyzed: data.pages_analyzed
    });
});

function showPersonalizedContent(persona) {
    // Example: Show different content based on persona
    const contentArea = document.getElementById('personalized-content');
    if (contentArea) {
        contentArea.innerHTML = `
            <h3>Recommended for ${persona.title}</h3>
            <p>${persona.description}</p>
        `;
    }
}
```

#### Session Management

```javascript
const pm = new PersonaMap();

// Clear session data (useful for testing or user logout)
pm.clearSession();

// Get session information
console.log('Session ID:', pm.getSessionId());
console.log('Visited Pages:', pm.getVisitedPagesData());

// Check if browser is supported
if (PersonaMap.isSupported()) {
    console.log('PersonaMap is supported in this browser');
} else {
    console.log('PersonaMap requires sessionStorage and XMLHttpRequest');
}
```

## Configuration Options

The JavaScript client accepts the following configuration options:

```javascript
const pm = new PersonaMap({
    // API base URL (default: '/api')
    apiBaseUrl: 'https://your-domain.com/api',
    
    // Session storage key (default: 'personamap_session')
    sessionStorageKey: 'my_app_session',
    
    // Visited pages storage key (default: 'personamap_visited_pages')
    visitedPagesKey: 'my_app_pages',
    
    // Maximum pages to store in session (default: 50)
    maxStoredPages: 100,
    
    // Debounce delay for prediction updates in ms (default: 1000)
    debounceDelay: 2000,
    
    // Number of retry attempts for failed requests (default: 3)
    retryAttempts: 5,
    
    // Delay between retries in ms (default: 1000)
    retryDelay: 1500
});
```

## Security Considerations

### For Production Use

1. **Domain Restrictions**: Modify `validate_api_request()` to check the `Origin` or `Referer` headers
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **HTTPS Only**: Ensure all API calls are made over HTTPS
4. **CORS Configuration**: Configure proper CORS headers for your domain

### Example Enhanced Validation

```python
def validate_api_request():
    """Enhanced API request validation for production."""
    
    # Check allowed origins
    allowed_origins = ['https://yourdomain.com', 'https://www.yourdomain.com']
    origin = request.headers.get('Origin')
    referer = request.headers.get('Referer')
    
    if origin:
        if origin not in allowed_origins:
            return False
    elif referer:
        parsed_referer = urlparse(referer)
        if f"{parsed_referer.scheme}://{parsed_referer.netloc}" not in allowed_origins:
            return False
    
    # Basic rate limiting (implement with Redis for production)
    # This is a simple example - use proper rate limiting in production
    client_ip = request.environ.get('REMOTE_ADDR')
    # ... implement rate limiting logic
    
    return True
```

## Testing the API

### Using curl

```bash
# Test page personas endpoint
curl "http://localhost:5000/api/personas/page?url=https://example.com/test"

# Test persona prediction
curl -X POST http://localhost:5000/api/personas/predict \
  -H "Content-Type: application/json" \
  -d '{
    "visited_urls": ["https://example.com/page1", "https://example.com/page2"],
    "session_id": "test_session",
    "prediction_method": "weighted"
  }'

# Test health endpoint
curl "http://localhost:5000/api/health"

# Test personas list
curl "http://localhost:5000/api/personas/list?limit=10"
```

### JavaScript Testing

```javascript
// Test in browser console
fetch('/api/personas/page?url=' + encodeURIComponent(window.location.href))
  .then(response => response.json())
  .then(data => console.log('Page personas:', data));

fetch('/api/personas/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    visited_urls: [window.location.href],
    session_id: 'test_session'
  })
})
.then(response => response.json())
.then(data => console.log('Prediction:', data));
```

## Troubleshooting

### Common Issues

1. **No personas returned**: Check if the URL exists in your crawled pages database
2. **CORS errors**: Ensure proper CORS configuration in Flask
3. **Session storage issues**: Check browser compatibility and privacy settings
4. **API errors**: Check Flask application logs for detailed error messages

### Debug Mode

Enable debug logging in the JavaScript client:

```javascript
const pm = new PersonaMap({
    debug: true // Add this to see console logs
});
```

### Flask Debug

For API debugging, check the Flask application logs and ensure debug mode is enabled during development.

## Performance Considerations

- The API includes database indexes for efficient querying
- URL normalization reduces duplicate lookups
- Session storage keeps client-side data lightweight
- Debounced prediction updates prevent excessive API calls
- Configurable limits prevent large response payloads

## Browser Compatibility

The JavaScript client requires:
- `sessionStorage` support
