# Crawler User Agent Configuration Fix

## Problem Identified

The user correctly identified that the `.env.example` file contained a user agent string (`PersonaMap-Bot/1.0`) that would likely get blocked by many websites, while the actual web crawler was hardcoded to use a realistic Mozilla/Chrome user agent string.

## Issues Found

1. **Hardcoded User Agent**: The web crawler had a hardcoded Mozilla user agent string
2. **Misleading .env.example**: The example configuration suggested using `PersonaMap-Bot/1.0` which would get blocked
3. **No Environment Configuration**: The user agent wasn't configurable through environment variables
4. **Inconsistent Configuration**: Config.py still had the old bot user agent

## Changes Made

### 1. Updated `.env.example`
**Before:**
```bash
CRAWLER_USER_AGENT=PersonaMap-Bot/1.0
```

**After:**
```bash
CRAWLER_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

### 2. Updated `app/services/web_crawler.py`
**Before:**
```python
self.session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})
```

**After:**
```python
# Use configurable user agent from environment, with fallback to current working default
user_agent = current_app.config.get(
    'CRAWLER_USER_AGENT', 
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)
self.session.headers.update({
    'User-Agent': user_agent
})
```

### 3. Updated `config.py`
**Before:**
```python
CRAWLER_USER_AGENT = 'PersonaMap-Bot/1.0'
CRAWLER_DELAY = 1
CRAWLER_MAX_PAGES_DEFAULT = 100
```

**After:**
```python
CRAWLER_USER_AGENT = os.environ.get('CRAWLER_USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
CRAWLER_DELAY = int(os.environ.get('CRAWLER_DELAY', '1'))
CRAWLER_MAX_PAGES_DEFAULT = int(os.environ.get('CRAWLER_MAX_PAGES_DEFAULT', '100'))
```

## Benefits of the Fix

### 1. **Avoids Website Blocks**
- Uses a realistic browser user agent by default
- Websites are less likely to block or restrict access
- Better crawling success rates

### 2. **Configurable**
- Users can now customize the user agent through environment variables
- Easy to change for different websites or requirements
- No need to modify code for different user agents

### 3. **Flexible Options**
Users can now choose from different approaches:

**Stealth Mode (Default):**
```bash
CRAWLER_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

**Transparent Bot (if preferred):**
```bash
CRAWLER_USER_AGENT=PersonaMap-Bot/1.0
```

**Custom User Agent:**
```bash
CRAWLER_USER_AGENT=MyCompany-Crawler/2.0 (+https://mycompany.com/bot)
```

### 4. **Consistent Configuration**
- All crawler settings now use environment variables
- Consistent pattern with other configuration options
- Easy to manage in different environments (dev, staging, production)

## Recommendations

### For Most Users
Use the default Mozilla user agent (already configured) for best compatibility and success rates.

### For Ethical Considerations
If you want to be transparent about being a bot, you can use:
```bash
CRAWLER_USER_AGENT=PersonaMap-Bot/1.0 (+https://yoursite.com/bot-info)
```

But be aware this may result in more blocked requests and lower success rates.

### For Specific Sites
Some sites may require specific user agents or have different blocking patterns. You can customize as needed:
```bash
CRAWLER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

## Testing the Fix

The server is already running on port 5002. You can test the configuration by:

1. **Check Current Configuration**: Visit the AI Integration page in the admin dropdown to see current settings
2. **Test API Endpoint**: Use `/api/ai/status` to check current analyzer configuration
3. **Create a Test Crawl Job**: Set up a small crawl job to verify the user agent is working
4. **Monitor Logs**: Check application logs to see the user agent being used in requests

## Migration Notes

### Existing Installations
- The changes are backward compatible
- Default behavior now uses the working Mozilla user agent
- No action required for existing users unless they want to customize

### New Installations
- Copy `.env.example` to `.env` and the user agent will work out of the box
- No additional configuration needed for basic crawling

## Security and Legal Considerations

### User Agent Spoofing
- Using a browser user agent is a common practice for web scraping
- It helps avoid unnecessary blocks while remaining technically honest about capabilities
- Most websites expect this behavior from legitimate crawlers

### Rate Limiting
- The crawler still respects rate limiting (configurable via `CRAWLER_DELAY`)
- Robots.txt checking can be enabled if needed
- Always follow website terms of service

### Best Practices
1. **Use realistic user agents** for better success rates
2. **Respect rate limits** to avoid overwhelming servers
3. **Check robots.txt** for sites that require it
4. **Monitor for blocks** and adjust user agent if needed
5. **Be transparent** in your bot identification URL if using a bot user agent

## Summary

This fix resolves the user agent configuration issue by:
- ✅ Making user agent configurable through environment variables
- ✅ Using a working Mozilla user agent as the default
- ✅ Updating all configuration files consistently
- ✅ Providing flexibility for different use cases
- ✅ Maintaining backward compatibility
- ✅ Improving crawling success rates

The PersonaMap crawler will now work better out of the box while still allowing customization for specific needs.
