# PersonaMap

PersonaMap is an AI-powered web content analysis platform that automatically maps website content to user personas. It crawls websites, analyzes content using both keyword matching and AI techniques, and provides insights into which personas are most relevant to different pages.

## 🚀 Features

### Core Functionality
- **Web Crawling**: Sitemap-based crawling with configurable patterns and limits
- **Content Analysis**: Multiple analysis modes including keyword matching, AI analysis, and hybrid approaches
- **Persona Mapping**: Automatic mapping of content to user-defined personas with confidence scores
- **Real-time Dashboard**: Visual insights into crawl progress and persona mappings
- **Historical Tracking**: Track persona mapping changes over time

### AI Integration
- **OpenAI GPT Integration**: Semantic content analysis using GPT models
- **Local AI Models**: Privacy-focused analysis using Sentence Transformers
- **Hybrid Analysis**: Combines AI and keyword analysis for optimal results
- **Cost Management**: Built-in spending limits and usage tracking
- **Multiple Analysis Modes**: keyword, ai, hybrid, validation, and local modes

### API & Integration
- **RESTful API**: Complete API for persona predictions and content analysis
- **JavaScript Client**: Easy integration with existing websites
- **Tag Manager Integration**: Google Tag Manager compatible
- **Real-time Analysis**: Live content analysis endpoints

## 📋 Requirements

- Python 3.9+
- Flask 2.3+
- SQLite (development) / PostgreSQL (production)
- Optional: OpenAI API key for AI analysis
- Optional: Docker for containerized deployment

## 🛠️ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/personamap.git
cd personamap
```
### Note: you may need to setup a virtual environment first
Example for Mint Linux
sudo apt update
sudo apt install python3-venv
python3 -m venv .venv


### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environmentsource .venv/bin/activate
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Initialize Database and Create Admin User
```bash
export FLASK_APP=run.py; flask init-db
```

### 5. Start the Application
```bash
python run.py
```

Visit `http://localhost:5002` and login with:
- **Username**: admin
- **Password**: admin123

## 🔧 Configuration

### Basic Configuration (.env)
```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///personamap.db

# AI Analysis (Optional)
AI_ENABLED=false
AI_ANALYSIS_MODE=keyword
OPENAI_API_KEY=your-openai-api-key-here

# Crawler Settings
CRAWLER_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
CRAWLER_DELAY=1
```

### AI Analysis Modes
- **keyword**: Traditional keyword matching (default, no AI required)
- **ai**: Pure AI analysis using OpenAI GPT
- **hybrid**: Combines AI and keyword analysis (recommended)
- **validation**: Uses AI to validate keyword mappings
- **local**: Uses local Sentence Transformers (privacy-focused)

See [AI_INTEGRATION_README.md](AI_INTEGRATION_README.md) for detailed AI configuration.

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 📖 Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [AI Integration Guide](AI_INTEGRATION_README.md) - AI setup and configuration
- [Deployment Guide](DEPLOYMENT.md) - Docker and AWS deployment
- [Crawler User Agent Fix](CRAWLER_USER_AGENT_FIX.md) - User agent configuration

## 🏗️ Architecture

```
PersonaMap/
├── app/                    # Main application package
│   ├── models/            # Database models
│   ├── routes/            # Flask blueprints/routes
│   ├── services/          # Business logic services
│   ├── templates/         # HTML templates
│   └── static/            # Static assets
├── instance/              # Instance-specific files
├── migrations/            # Database migrations (if using Flask-Migrate)
└── run.py                # Application entry point
```

### Key Components
- **Web Crawler**: Sitemap-based crawling with rate limiting and robots.txt support
- **Content Analyzer**: Multiple analysis engines (keyword, AI, hybrid)
- **Persona Engine**: User-defined personas with keyword and AI matching
- **API Layer**: RESTful API for external integrations
- **Dashboard**: Web interface for management
