# MySQL Queries for PythonAnywhere Crawl Mapping Progress

## 🔍 Quick Mapping Count Queries (MySQL Syntax)

### 1. Total Active Mappings
```sql
SELECT COUNT(*) as total_active_mappings 
FROM content_mappings 
WHERE is_active = 1;
```

### 2. Current Crawl Progress (MySQL Compatible)
```sql
SELECT 
    cj.name,
    cj.pages_crawled,
    COUNT(cm.id) as total_mappings,
    COUNT(CASE WHEN cm.is_active = 1 THEN 1 END) as active_mappings,
    ROUND(COUNT(cm.id) * 100.0 / NULLIF(cj.pages_crawled, 0), 2) as mapping_percentage
FROM crawl_jobs cj
LEFT JOIN crawled_pages cp ON cp.crawl_job_id = cj.id
LEFT JOIN content_mappings cm ON cm.page_id = cp.id
WHERE cj.status IN ('running', 'active') 
   OR cj.last_activity_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY cj.id, cj.name, cj.pages_crawled
ORDER BY cj.last_activity_at DESC;
```

### 3. Simple Running Crawl Check
```sql
SELECT 
    cj.id,
    cj.name,
    cj.status,
    cj.pages_crawled,
    cj.last_activity_at
FROM crawl_jobs cj
WHERE cj.status IN ('running', 'active') 
   OR cj.last_activity_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY cj.last_activity_at DESC;
```

### 4. Mappings by Crawl Job (Simplified)
```sql
SELECT 
    cj.id,
    cj.name,
    cj.pages_crawled,
    COUNT(cm.id) as total_mappings
FROM crawl_jobs cj
LEFT JOIN crawled_pages cp ON cp.crawl_job_id = cj.id
LEFT JOIN content_mappings cm ON cm.page_id = cp.id
GROUP BY cj.id, cj.name, cj.pages_crawled
ORDER BY cj.id DESC;
```

### 5. Recent Mappings (Last Hour)
```sql
SELECT COUNT(*) as recent_mappings
FROM content_mappings 
WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
  AND is_active = 1;
```

### 6. Most Recent 20 Mappings
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

### 7. Mappings by Persona (Current Crawls)
```sql
SELECT 
    p.title as persona_name,
    COUNT(cm.id) as total_mappings,
    COUNT(CASE WHEN cm.is_active = 1 THEN 1 END) as active_mappings,
    ROUND(AVG(cm.confidence_score), 2) as avg_confidence
FROM personas p
JOIN content_mappings cm ON cm.persona_id = p.id
JOIN crawled_pages cp ON cp.id = cm.page_id
JOIN crawl_jobs cj ON cj.id = cp.crawl_job_id
WHERE cj.status IN ('running', 'active') 
   OR cj.last_activity_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY p.id, p.title
ORDER BY total_mappings DESC;
```

### 8. Hourly Mapping Rate (Last 24 Hours)
```sql
SELECT 
    DATE_FORMAT(cm.created_at, '%Y-%m-%d %H:00:00') as hour,
    COUNT(*) as mappings_created
FROM content_mappings cm
JOIN crawled_pages cp ON cp.id = cm.page_id
JOIN crawl_jobs cj ON cj.id = cp.crawl_job_id
WHERE cm.created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
  AND (cj.status IN ('running', 'active') OR cj.last_activity_at > DATE_SUB(NOW(), INTERVAL 2 HOUR))
GROUP BY DATE_FORMAT(cm.created_at, '%Y-%m-%d %H:00:00')
ORDER BY hour DESC;
```

## 🚀 Quick Commands for PythonAnywhere MySQL

### Connect to MySQL:
```bash
mysql -u [yourusername] -p -h [yourusername].mysql.pythonanywhere-services.com '[yourusername]$personamap'
```

### Or use the simpler connection:
```bash
mysql -u [yourusername] -p [yourusername]$personamap
```

## ⚡ **EASIEST - Start with these simple queries:**

### 1. Just count total mappings:
```sql
SELECT COUNT(*) FROM content_mappings WHERE is_active = 1;
```

### 2. See your crawl jobs:
```sql
SELECT id, name, status, pages_crawled, last_activity_at FROM crawl_jobs ORDER BY last_activity_at DESC LIMIT 5;
```

### 3. Count mappings per crawl:
```sql
SELECT 
    cj.name,
    COUNT(cm.id) as mappings
FROM crawl_jobs cj
LEFT JOIN crawled_pages cp ON cp.crawl_job_id = cj.id
LEFT JOIN content_mappings cm ON cm.page_id = cp.id
GROUP BY cj.id, cj.name
ORDER BY mappings DESC;
```

## 🔧 Key MySQL Syntax Differences:
- `datetime('now', '-1 hour')` → `DATE_SUB(NOW(), INTERVAL 1 HOUR)`
- `datetime('now')` → `NOW()`
- Date formatting uses `DATE_FORMAT()` instead of SQLite functions
- Added `NULLIF()` to prevent division by zero errors

Try the simple queries first, then work up to the more complex ones!