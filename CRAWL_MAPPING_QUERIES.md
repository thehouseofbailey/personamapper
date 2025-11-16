# SQL Queries to Check Crawl Mapping Progress

## 🔍 Quick Mapping Count Queries

### 1. Total Active Mappings Across All Crawls
```sql
SELECT COUNT(*) as total_active_mappings 
FROM content_mappings 
WHERE is_active = 1;
```

### 2. Mappings by Crawl Job (with job names)
```sql
SELECT 
    cj.id,
    cj.name as crawl_job_name,
    cj.status,
    cj.pages_crawled,
    COUNT(cm.id) as total_mappings,
    COUNT(CASE WHEN cm.is_active = 1 THEN 1 END) as active_mappings
FROM crawl_jobs cj
LEFT JOIN crawled_pages cp ON cp.crawl_job_id = cj.id
LEFT JOIN content_mappings cm ON cm.page_id = cp.id
GROUP BY cj.id, cj.name, cj.status, cj.pages_crawled
ORDER BY cj.id DESC;
```

### 3. Latest/Current Running Crawl Progress
```sql
SELECT 
    cj.id,
    cj.name,
    cj.status,
    cj.pages_crawled,
    cj.last_activity_at,
    COUNT(DISTINCT cp.id) as pages_processed,
    COUNT(cm.id) as total_mappings,
    COUNT(CASE WHEN cm.is_active = 1 THEN 1 END) as active_mappings,
    ROUND(COUNT(cm.id) * 100.0 / cj.pages_crawled, 2) as mapping_percentage
FROM crawl_jobs cj
LEFT JOIN crawled_pages cp ON cp.crawl_job_id = cj.id
LEFT JOIN content_mappings cm ON cm.page_id = cp.id
WHERE cj.status IN ('running', 'active') 
   OR cj.last_activity_at > datetime('now', '-1 hour')
GROUP BY cj.id
ORDER BY cj.last_activity_at DESC;
```

### 4. Mappings by Persona (for current crawls)
```sql
SELECT 
    p.title as persona_name,
    COUNT(cm.id) as total_mappings,
    COUNT(CASE WHEN cm.is_active = 1 THEN 1 END) as active_mappings,
    AVG(cm.confidence_score) as avg_confidence
FROM personas p
JOIN content_mappings cm ON cm.persona_id = p.id
JOIN crawled_pages cp ON cp.id = cm.page_id
JOIN crawl_jobs cj ON cj.id = cp.crawl_job_id
WHERE cj.status IN ('running', 'active') 
   OR cj.last_activity_at > datetime('now', '-1 hour')
GROUP BY p.id, p.title
ORDER BY total_mappings DESC;
```

### 5. Most Recent Mappings (to see current progress)
```sql
SELECT 
    cj.name as crawl_job,
    p.title as persona,
    cm.confidence_score,
    cm.created_at,
    cp.url
FROM content_mappings cm
JOIN crawled_pages cp ON cp.id = cm.page_id
JOIN crawl_jobs cj ON cj.id = cp.crawl_job_id
JOIN personas p ON p.id = cm.persona_id
WHERE cm.is_active = 1
ORDER BY cm.created_at DESC
LIMIT 20;
```

### 6. Hourly Mapping Rate (to see processing speed)
```sql
SELECT 
    datetime(cm.created_at, 'start of hour') as hour,
    COUNT(*) as mappings_created
FROM content_mappings cm
JOIN crawled_pages cp ON cp.id = cm.page_id
JOIN crawl_jobs cj ON cj.id = cp.crawl_job_id
WHERE cm.created_at > datetime('now', '-24 hours')
  AND (cj.status IN ('running', 'active') OR cj.last_activity_at > datetime('now', '-2 hours'))
GROUP BY datetime(cm.created_at, 'start of hour')
ORDER BY hour DESC;
```

## 🚀 Quick Commands for PythonAnywhere

### Via MySQL Console:
```bash
# Connect to your database
mysql -u [username] -p[password] -h [hostname] [database_name]

# Then run any of the above queries
```

### Via Python (if you prefer):
```python
# In PythonAnywhere bash console
cd ~/personamapper
python3.10 -c "
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Quick mapping count
    result = db.session.execute(text('SELECT COUNT(*) as total FROM content_mappings WHERE is_active = 1')).fetchone()
    print(f'Total active mappings: {result[0]}')
    
    # Current crawl progress
    query = '''
    SELECT cj.name, cj.pages_crawled, COUNT(cm.id) as mappings 
    FROM crawl_jobs cj
    LEFT JOIN crawled_pages cp ON cp.crawl_job_id = cj.id
    LEFT JOIN content_mappings cm ON cm.page_id = cp.id
    WHERE cj.status IN (\"running\", \"active\") OR cj.last_activity_at > datetime(\"now\", \"-1 hour\")
    GROUP BY cj.id
    ORDER BY cj.last_activity_at DESC
    '''
    results = db.session.execute(text(query)).fetchall()
    for row in results:
        print(f'{row[0]}: {row[1]} pages crawled, {row[2]} mappings')
"
```

## 📊 Expected Output Examples

For a running crawl, you might see:
- **Total mappings**: Increasing number (e.g., 1,247)
- **Mapping percentage**: How much of crawled content is mapped (e.g., 15.3%)
- **Recent activity**: Timestamps showing recent mapping creation
- **Persona distribution**: Which personas are getting the most mappings

## 🔍 What to Look For
- **Active mappings increasing**: Good sign that analysis is working
- **Recent timestamps**: Shows the crawler is actively processing
- **Mapping percentage**: Higher is better (depends on content relevance)
- **Error patterns**: If mappings suddenly stop, check for issues

Choose the query that best fits what you want to monitor!