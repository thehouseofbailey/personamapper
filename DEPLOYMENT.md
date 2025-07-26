# PersonaMap Deployment Guide

This guide covers various deployment options for PersonaMap, from local development to production deployment on AWS.

## 📋 Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [AWS Deployment](#aws-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Monitoring & Maintenance](#monitoring--maintenance)

## 🏠 Local Development

### Prerequisites
- Python 3.9+
- pip
- Git

### Quick Setup
```bash
# Clone repository
git clone https://github.com/yourusername/personamap.git
cd personamap

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python run.py init-db

# Start application
python run.py
```

Visit `http://localhost:5002` with credentials: `admin` / `admin123`

## 🐳 Docker Deployment

### Development with Docker
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f personamap

# Stop services
docker-compose down
```

### Production Docker Setup
```bash
# Create production environment file
cp .env.example .env.production
# Edit .env.production with production settings

# Build production image
docker build --target production -t personamap:latest .

# Run with production settings
docker run -d \
  --name personamap \
  -p 5002:5002 \
  --env-file .env.production \
  -v personamap_data:/app/instance \
  personamap:latest
```

### Docker with PostgreSQL
```bash
# Start with PostgreSQL
docker-compose --profile postgres up -d

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://personamap:personamap_password@postgres:5432/personamap
```

## 🚀 Production Deployment

### Production Checklist

#### Security
- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY`
- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Configure firewall rules
- [ ] Set up proper authentication
- [ ] Review API access controls

#### Database
- [ ] Use PostgreSQL or MySQL (not SQLite)
- [ ] Set up database backups
- [ ] Configure connection pooling
- [ ] Optimize database settings

#### Performance
- [ ] Use reverse proxy (Nginx/Apache)
- [ ] Configure caching (Redis)
- [ ] Set up CDN for static files
- [ ] Optimize AI model loading
- [ ] Configure proper logging

#### Monitoring
- [ ] Set up health checks
- [ ] Configure log aggregation
- [ ] Set up alerting
- [ ] Monitor resource usage
- [ ] Track AI costs (if enabled)

### Production Environment Variables
```bash
# Flask Configuration
SECRET_KEY=your-very-secure-secret-key-here
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host:5432/personamap

# Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true

# AI Configuration (if using)
AI_ENABLED=true
AI_ANALYSIS_MODE=hybrid
OPENAI_API_KEY=your-openai-api-key
AI_DAILY_COST_LIMIT=50.0
AI_MONTHLY_COST_LIMIT=500.0

# Crawler Settings
CRAWLER_DELAY=2
CRAWLER_MAX_PAGES_DEFAULT=1000
```

## ☁️ AWS Deployment

### Option 1: ECS Fargate (Recommended)

#### Prerequisites
- AWS CLI configured
- Docker installed
- ECR repository created

#### Steps

1. **Build and Push Image**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build --target production -t personamap:latest .
docker tag personamap:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/personamap:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/personamap:latest
```

2. **Create RDS Database**
```bash
aws rds create-db-instance \
  --db-instance-identifier personamap-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username personamap \
  --master-user-password your-secure-password \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxxx
```

3. **Create ECS Task Definition**
```json
{
  "family": "personamap",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "personamap",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/personamap:latest",
      "portMappings": [
        {
          "containerPort": 5002,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://personamap:password@personamap-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/personamap"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/personamap",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

4. **Create ECS Service**
```bash
aws ecs create-service \
  --cluster personamap-cluster \
  --service-name personamap-service \
  --task-definition personamap:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxx],securityGroups=[sg-xxxxxxxxx],assignPublicIp=ENABLED}"
```

5. **Set up Application Load Balancer**
```bash
# Create target group
aws elbv2 create-target-group \
  --name personamap-targets \
  --protocol HTTP \
  --port 5002 \
  --vpc-id vpc-xxxxxxxxx \
  --target-type ip \
  --health-check-path /api/health

# Create load balancer
aws elbv2 create-load-balancer \
  --name personamap-alb \
  --subnets subnet-xxxxxxxxx subnet-yyyyyyyyy \
  --security-groups sg-xxxxxxxxx
```

### Option 2: Elastic Beanstalk

1. **Create Application**
```bash
# Install EB CLI
pip install awsebcli

# Initialize application
eb init personamap --platform python-3.9 --region us-east-1

# Create environment
eb create personamap-prod --database.engine postgres
```

2. **Deploy**
```bash
eb deploy
```

### Option 3: EKS (Kubernetes)

1. **Create Kubernetes Manifests**

**deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: personamap
spec:
  replicas: 3
  selector:
    matchLabels:
      app: personamap
  template:
    metadata:
      labels:
        app: personamap
    spec:
      containers:
      - name: personamap
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/personamap:latest
        ports:
        - containerPort: 5002
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: personamap-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

**service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: personamap-service
spec:
  selector:
    app: personamap
  ports:
  - port: 80
    targetPort: 5002
  type: LoadBalancer
```

2. **Deploy to EKS**
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## 🔧 Environment Configuration

### Required Environment Variables
```bash
# Core Configuration
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
FLASK_ENV=production

# AI Configuration (Optional)
AI_ENABLED=true
AI_ANALYSIS_MODE=hybrid
OPENAI_API_KEY=your-openai-key
AI_DAILY_COST_LIMIT=10.0
AI_MONTHLY_COST_LIMIT=100.0

# Crawler Configuration
CRAWLER_USER_AGENT=Mozilla/5.0...
CRAWLER_DELAY=1
CRAWLER_MAX_PAGES_DEFAULT=100
```

### AWS Secrets Manager Integration
```python
# Add to config.py for production
import boto3
import json

def get_secret(secret_name, region_name="us-east-1"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    return json.loads(get_secret_value_response['SecretString'])

# Usage in Config class
if os.environ.get('USE_AWS_SECRETS'):
    secrets = get_secret('personamap/prod')
    SECRET_KEY = secrets['SECRET_KEY']
    DATABASE_URL = secrets['DATABASE_URL']
    OPENAI_API_KEY = secrets['OPENAI_API_KEY']
```

## 🗄️ Database Setup

### PostgreSQL Production Setup
```sql
-- Create database and user
CREATE DATABASE personamap;
CREATE USER personamap WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE personamap TO personamap;

-- Connect to personamap database
\c personamap

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Database Migration
```python
# Add to run.py for production migrations
@app.cli.command()
def migrate_to_postgres():
    """Migrate from SQLite to PostgreSQL."""
    # Implementation for data migration
    pass
```

### Database Backup Script
```bash
#!/bin/bash
# backup_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="personamap_backup_$DATE.sql"

pg_dump -h your-rds-endpoint \
        -U personamap \
        -d personamap \
        -f $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/database/
```

## 📊 Monitoring & Maintenance

### Health Checks
The application includes a health check endpoint at `/api/health`:

```python
@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time()),
        'version': '1.0.0'
    })
```

### CloudWatch Monitoring
```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name PersonaMap \
  --dashboard-body file://cloudwatch-dashboard.json
```

### Log Configuration
```python
# Add to app/__init__.py for production logging
import logging
from logging.handlers import RotatingFileHandler
import os

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/personamap.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('PersonaMap startup')
```

### Scaling Considerations

#### Horizontal Scaling
- **ECS/EKS**: Increase task/pod count
- **Database**: Use read replicas for read-heavy workloads
- **Load Balancing**: Distribute traffic across multiple instances
- **Caching**: Implement Redis for session and data caching

#### Vertical Scaling
- **Memory**: Increase for AI model loading (sentence-transformers)
- **CPU**: Scale for concurrent crawling operations
- **Storage**: Monitor database growth and optimize queries

### Backup Strategy
```bash
# Automated backup script
#!/bin/bash
# Daily backup with retention
RETENTION_DAYS=30
DATE=$(date +%Y%m%d)

# Database backup
pg_dump $DATABASE_URL > backup_${DATE}.sql
aws s3 cp backup_${DATE}.sql s3://your-backup-bucket/daily/

# Clean old backups
aws s3 ls s3://your-backup-bucket/daily/ | while read -r line; do
    createDate=$(echo $line | awk '{print $1" "$2}')
    createDate=$(date -d "$createDate" +%s)
    olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
    if [[ $createDate -lt $olderThan ]]; then
        fileName=$(echo $line | awk '{print $4}')
        aws s3 rm s3://your-backup-bucket/daily/$fileName
    fi
done
```

### Troubleshooting

#### Common Issues

**Container Won't Start**
```bash
# Check logs
docker logs personamap
# or for ECS
aws logs get-log-events --log-group-name /ecs/personamap
```

**Database Connection Issues**
```bash
# Test database connectivity
python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Database connection successful')
"
```

**AI Model Loading Issues**
```bash
# Check available memory
free -h
# Monitor model loading
docker exec personamap python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model loaded successfully')
"
```

**High Memory Usage**
- Reduce AI model size or disable AI features
- Implement model caching strategies
- Use model quantization for production

#### Performance Optimization

**Database Optimization**
```sql
-- Add indexes for common queries
CREATE INDEX idx_content_mapping_persona_id ON content_mapping(persona_id);
CREATE INDEX idx_content_mapping_page_id ON content_mapping(page_id);
CREATE INDEX idx_crawled_page_url ON crawled_page(url);
CREATE INDEX idx_crawled_page_crawled_at ON crawled_page(crawled_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM content_mapping WHERE persona_id = 1;
```

**Application Optimization**
```python
# Add to config.py
# Connection pooling
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True
}

# Caching configuration
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/0'
```

### Security Hardening

#### Network Security
```bash
# Security group rules (AWS)
# Allow only necessary ports
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Database security group (restrict to app only)
aws ec2 authorize-security-group-ingress \
  --group-id sg-database \
  --protocol tcp \
  --port 5432 \
  --source-group sg-app
```

#### Application Security
```python
# Add to config.py for production
class ProductionConfig(Config):
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'"
    }
    
    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
```

### Cost Optimization

#### AWS Cost Management
- Use Spot instances for non-critical workloads
- Implement auto-scaling to match demand
- Use Reserved Instances for predictable workloads
- Monitor and set billing alerts
- Optimize AI usage with cost limits

#### Resource Optimization
```yaml
# ECS task definition with resource limits
"cpu": "256",
"memory": "512",
"memoryReservation": "256"
```

### Disaster Recovery

#### Backup Verification
```bash
# Test backup restoration
pg_restore --verbose --clean --no-acl --no-owner \
  -h localhost -U personamap -d personamap_test backup.sql
```

#### Multi-Region Setup
- Deploy to multiple AWS regions
- Use RDS cross-region read replicas
- Implement DNS failover with Route 53
- Sync static assets across regions

### Maintenance Tasks

#### Regular Maintenance
```bash
# Weekly tasks
- Monitor disk usage and clean logs
- Review security updates
- Check backup integrity
- Monitor AI costs and usage
- Review crawler performance

# Monthly tasks
- Update dependencies
- Review and rotate secrets
- Analyze performance metrics
- Optimize database queries
- Review access logs
```

#### Database Maintenance
```sql
-- Monthly database maintenance
VACUUM ANALYZE;
REINDEX DATABASE personamap;

-- Clean old crawl data (optional)
DELETE FROM crawled_page WHERE crawled_at < NOW() - INTERVAL '90 days';
DELETE FROM content_mapping WHERE created_at < NOW() - INTERVAL '90 days' AND is_active = false;
```

#### Log Rotation
```bash
# Add to crontab for log rotation
0 2 * * * /usr/sbin/logrotate /etc/logrotate.d/personamap
```

## 🎯 Quick Reference

### Essential Commands
```bash
# Local development
python run.py init-db
python run.py

# Docker development
docker-compose up -d
docker-compose logs -f personamap

# Production deployment
docker build --target production -t personamap:latest .
docker run -d --name personamap -p 5002:5002 --env-file .env.production personamap:latest

# Database backup
pg_dump $DATABASE_URL > backup.sql

# Health check
curl http://localhost:5002/api/health
```

### Important URLs
- **Application**: `http://localhost:5002`
- **Health Check**: `http://localhost:5002/api/health`
- **API Status**: `http://localhost:5002/api/ai/status`
- **API Documentation**: Available in `API_DOCUMENTATION.md`

### Default Credentials
- **Username**: admin
- **Password**: admin123
- **⚠️ Change immediately in production!**

---

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment configuration
3. Test database connectivity
4. Review security group settings (AWS)
5. Monitor resource usage

This deployment guide provides multiple options for running PersonaMap from development to production scale. Choose the deployment method that best fits your infrastructure requirements and expertise level.
