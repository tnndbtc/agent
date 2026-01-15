# Novel Writing Agent

An AI-powered novel writing assistant that helps authors create complete novels through an intelligent, step-by-step workflow. Available as both a command-line interface (CLI) and a full-featured web application.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Development](#local-development)
- [Installation](#installation)
- [Usage](#usage)
  - [CLI Interface](#cli-interface)
  - [Web Application](#web-application)
  - [Mobile Usage](#mobile-usage)
  - [First Novel Workflow](#first-novel-workflow)
- [Deployment](#deployment)
  - [Docker Deployment](#docker-deployment)
  - [Production Deployment](#production-deployment)
  - [Cloud Platform Deployment](#cloud-platform-deployment)
- [Internationalization](#internationalization)
- [Restarting the Application](#restarting-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Extending the System](#extending-the-system)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [License](#license)

## Features

### Core Capabilities

1. **Brainstorming & Ideation**
   - Generate multiple plot ideas based on genre and themes
   - Refine and expand ideas with user feedback
   - Constraint-based brainstorming

2. **Plot Development**
   - Create detailed three-act story structures
   - Generate subplots and key scenes
   - Identify crucial story moments

3. **Character Creation**
   - Generate protagonist, antagonist, and supporting characters
   - Create detailed character profiles with backgrounds, motivations, and arcs
   - Map character relationships

4. **World-Building**
   - Design primary and secondary settings
   - Create magic/technology systems for fantasy/sci-fi
   - Develop cultural elements and traditions

5. **Chapter Outlining**
   - Generate comprehensive chapter-by-chapter outlines
   - Scene breakdowns for each chapter
   - Pacing analysis and recommendations

6. **Writing**
   - Write chapters paragraph-by-paragraph
   - Generate dialogue, descriptions, and action scenes
   - Multi-language support (English, Chinese, French, Spanish, etc.)

7. **Editing & Refinement**
   - Style improvements
   - Pacing adjustments
   - Grammar and mechanics checking
   - Dialogue enhancement
   - Text compression

8. **Consistency Checking**
   - Character trait consistency
   - Setting and world-building consistency
   - Timeline verification
   - Plot consistency

9. **Scoring System**
   - Adjustable scoring categories and weights
   - Detailed feedback for each category
   - Overall grade and recommendations

10. **Example Management**
    - Store good and bad writing examples
    - Learn from examples during generation
    - Category-based organization

11. **Multi-Language Export**
    - Export to .txt files in multiple languages
    - Complete package export with all components
    - Individual chapter exports

## Quick Start

Get the Novel Writing Agent up and running in minutes.

### Prerequisites

**Option 1: Docker (Recommended)**
- Docker 20.10+
- Docker Compose 2.0+
- OpenAI API key

**Option 2: Local Development**
- Python 3.11+
- PostgreSQL 16+ (or SQLite for quick testing)
- Redis 7+
- OpenAI API key

### Docker (Recommended)

#### Step 1: Clone and Configure

```bash
cd novel_web

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Minimum required:
# - OPENAI_API_KEY=your-key-here
# - SECRET_KEY=generate-with-command-below
```

Generate a SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Step 2: Build and Start

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Run database migrations
docker compose exec web python manage.py migrate

# Create admin user
docker compose exec web python manage.py createsuperuser

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

#### Step 3: Access the Application

Open your browser:
- **Main app**: http://localhost:8000
- **Admin panel**: http://localhost:8000/admin/
- **API docs**: http://localhost:8000/api/

### Local Development

#### Step 1: Setup Environment

```bash
cd novel_web

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install novel_agent package from parent directory
pip install -e ../

# Install web application dependencies
pip install -r requirements-web.txt

# Configure environment
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
```

#### Step 2: Setup Database

For quick testing with SQLite:
```bash
# .env should have:
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=db.sqlite3

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### Step 3: Start Services

Terminal 1 - Django:
```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Terminal 2 - Celery (for AI tasks):
```bash
source venv/bin/activate
celery -A novel_web worker -l info
```

Terminal 3 - Redis (if not running as service):
```bash
redis-server
```

## Installation

### CLI Tool Prerequisites

- Python 3.12+
- OpenAI API key

### CLI Setup

1. Navigate to the agent directory:
```bash
cd /path/to/agent
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Web Application Setup

See [Quick Start](#quick-start) section above for detailed web application setup.

## Usage

### CLI Interface

Run the interactive command-line interface:

```bash
python main.py
```

This provides a menu-driven interface for:
- Starting a complete new novel workflow
- Individual operations (brainstorming, character creation, etc.)
- Editing and refinement
- Consistency checking
- Scoring and export

#### Example Workflow

Run the example workflow to see all features in action:

```bash
python example_workflow.py
```

This demonstrates:
1. Brainstorming plot ideas
2. Creating detailed plot structure
3. Generating characters (protagonist, antagonist, supporting)
4. Building world and settings
5. Creating chapter outline
6. Writing a complete chapter
7. Editing for style
8. Checking consistency
9. Scoring the chapter
10. Exporting to file

#### Programmatic Usage

```python
from novel_agent.memory.long_term_memory import LongTermMemory
from novel_agent.memory.context_manager import ContextManager
from novel_agent.modules import BrainstormingModule

# Initialize
memory = LongTermMemory()
context_manager = ContextManager(memory)
brainstormer = BrainstormingModule(context_manager)

# Generate ideas
ideas = brainstormer.generate_plot_ideas(
    genre="Fantasy",
    theme="Redemption",
    num_ideas=3
)

# Access the ideas
for idea in ideas:
    print(f"Title: {idea['title']}")
    print(f"Premise: {idea['premise']}")
```

### Web Application

#### Create Your First Novel

1. Register a new account or login
2. Click "Create New Project"
3. Fill in project details (title, genre, target word count)
4. Click "Brainstorm Ideas" to generate plot ideas
5. Select an idea and create your plot
6. Add characters and settings
7. Generate a chapter outline
8. Start writing!

### Mobile Usage

#### Access from Your Phone/Tablet

The server runs on `0.0.0.0:8000`, allowing access from any device on your local network:

**Quick Steps:**
1. Find your computer's IP address:
   ```bash
   # Linux/Mac
   hostname -I | awk '{print $1}'

   # Windows
   ipconfig
   ```

2. On your mobile device (same WiFi network):
   - Open browser
   - Go to: `http://YOUR_IP:8000` (e.g., `http://192.168.1.100:8000`)

3. If connection fails, add your IP to `.env`:
   ```bash
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,192.168.1.100
   ```
   Then restart the server.

#### Install as PWA

**On iOS (Safari):**
1. Visit the site in Safari
2. Tap the Share button
3. Tap "Add to Home Screen"
4. Tap "Add"

**On Android (Chrome):**
1. Visit the site in Chrome
2. Tap the menu (three dots)
3. Tap "Add to Home Screen"
4. Tap "Add"

The app will now open like a native app!

#### Mobile Gestures

- **Swipe right from left edge**: Open menu
- **Swipe left on menu**: Close menu
- **Pull down**: Refresh page
- **Double tap**: Prevent zoom (for better typing)

### First Novel Workflow

#### 1. Brainstorm Ideas

Via UI: Click "Brainstorm Ideas" button
- Enter genre (optional): Fantasy
- Enter theme (optional): Coming of age
- Number of ideas: 3

The AI will generate 3 plot ideas for you to choose from.

#### 2. Create Plot

Select your favorite idea and click "Create Plot". The system will generate:
- Three-act structure
- Major plot points
- Conflict and resolution

#### 3. Add Characters

Click "Create Character" and choose type:
- Protagonist
- Antagonist
- Supporting character

The AI generates detailed character profiles with:
- Name and background
- Personality traits
- Goals and motivations
- Character arc

#### 4. Build Setting

Click "Create Setting" to generate:
- Time period
- Location descriptions
- Social/political context
- Cultural details

#### 5. Generate Outline

Click "Create Outline" to generate:
- Chapter-by-chapter breakdown
- Scene descriptions
- Plot progression
- Pacing suggestions

#### 6. Write Chapters

Select a chapter from the outline and click "Write Chapter". The AI will:
- Generate the full chapter based on outline
- Match your specified style
- Maintain consistency with previous chapters

#### 7. Edit and Refine

Use the chapter editor tools:
- **Style Edit**: Improve prose quality
- **Grammar Check**: Fix errors
- **Consistency Check**: Ensure continuity
- **Expand**: Add more detail
- **Condense**: Tighten the prose

#### 8. Score Novel

When complete, click "Score Novel" to get:
- Overall score (0-100)
- Category breakdowns:
  - Story/Plot (30%)
  - Character Development (20%)
  - World-Building (15%)
  - Writing Style (20%)
  - Dialogue (10%)
  - Emotional Impact (5%)

#### 9. Export

Click "Export" to download your novel in:
- Plain text (.txt)
- Multiple languages supported

## Deployment

### Docker Deployment

#### Quick Docker Setup

```bash
# Configure environment
cp .env.example .env
# Edit .env with production values

# Build and start services
docker compose up -d

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

#### Docker Commands

```bash
# View logs
docker compose logs -f web
docker compose logs -f celery

# Restart services
docker compose restart

# Stop services
docker compose down

# Rebuild after code changes
docker compose up -d --build
```

### Production Deployment

#### Pre-Deployment Checklist

- [ ] Set `DEBUG=False` in .env
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set strong database passwords
- [ ] Configure SSL/HTTPS
- [ ] Set secure cookie flags
- [ ] Configure firewall rules
- [ ] Setup backup strategy
- [ ] Configure error monitoring (Sentry)
- [ ] Setup log aggregation

#### Environment Configuration

```bash
# Production .env
DEBUG=False
SECRET_KEY=<generate-with-python-secrets>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=novel_agent_db
DB_USER=novel_user
DB_PASSWORD=<strong-random-password>
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# OpenAI
OPENAI_API_KEY=<your-api-key>

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### Generate SECRET_KEY

```python
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### SSL Certificate Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### Cloud Platform Deployment

#### AWS (Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker novel-agent-web

# Create environment
eb create novel-agent-prod

# Deploy
eb deploy

# Configure environment variables
eb setenv SECRET_KEY=xxx OPENAI_API_KEY=xxx

# Open application
eb open
```

#### Google Cloud Platform (Cloud Run)

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/novel-agent

# Deploy to Cloud Run
gcloud run deploy novel-agent \
  --image gcr.io/PROJECT_ID/novel-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DEBUG=False,SECRET_KEY=xxx"
```

#### Heroku

```bash
# Create app
heroku create novel-agent-web

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=xxx
heroku config:set OPENAI_API_KEY=xxx
heroku config:set DEBUG=False

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

### Monitoring and Maintenance

#### Health Checks

The application provides several health check endpoints:

- `/health/` - Basic health check
- `/health/detailed/` - Detailed health with DB, Redis, Celery status
- `/readiness/` - Kubernetes readiness probe
- `/liveness/` - Kubernetes liveness probe

#### Database Backups

```bash
# Manual backup
docker compose exec db pg_dump -U novel_user novel_agent_db > backup.sql

# Restore
docker compose exec -T db psql -U novel_user novel_agent_db < backup.sql

# Automated backups (add to crontab)
0 2 * * * /path/to/backup-script.sh
```

## Internationalization

### Currently Supported Languages

1. **English** (`en`) - Default language
2. **简体中文** (`zh-hans`) - Simplified Chinese

### How to Use the Language Switcher

Users can switch languages using the language selector in the login page:
1. Visit the login page
2. Find the language dropdown at the bottom
3. Select desired language
4. The page will reload with the new language

### Adding Translations

#### Step 1: Create Translation Files

```bash
# For Docker setup
docker compose exec web python manage.py makemessages -l zh-hans

# For local setup
python manage.py makemessages -l zh-hans
```

#### Step 2: Edit Translation File

Open `locale/zh-hans/LC_MESSAGES/django.po` and add translations:

```po
#: templates/base.html:11
msgid "Novel Writing Agent"
msgstr "小说写作助手"
```

#### Step 3: Compile Translations

```bash
# For Docker setup
docker compose exec web python manage.py compilemessages

# For local setup
python manage.py compilemessages
```

#### Step 4: Restart the Application

```bash
docker compose restart web
```

### Adding a New Language

#### Update Settings

Edit `novel_web/settings.py` and add the new language to the `LANGUAGES` list:

```python
LANGUAGES = [
    ('en', 'English'),
    ('zh-hans', '简体中文'),
    ('fr', 'Français'),  # Add French
    ('ja', '日本語'),     # Add Japanese
]
```

Then follow steps 1-4 above for creating and compiling translations.

## Restarting the Application

### Quick Commands

#### Docker (Most Common)

```bash
# Quick restart (after configuration changes)
docker compose restart

# Restart specific service
docker compose restart web

# After code changes (rebuild required)
docker compose up -d --build

# Full restart (after major changes)
docker compose down
docker compose up -d
```

#### Local Development

```bash
# Stop Django (Ctrl+C in terminal), then:
python manage.py runserver 0.0.0.0:8000

# Stop Celery (Ctrl+C in terminal), then:
celery -A novel_web worker -l info
```

### Common Restart Scenarios

| What Changed | Docker Command | Local Command |
|--------------|----------------|---------------|
| Python code | `docker compose restart web` | Ctrl+C, then `python manage.py runserver 0.0.0.0:8000` |
| .env file | `docker compose restart web` | Ctrl+C, then restart runserver |
| Database models | Run migrations + restart | Same |
| Static files | Collectstatic + restart | Same |
| Celery tasks | `docker compose restart celery` | Ctrl+C Celery, then restart worker |
| Dockerfile | `docker compose up -d --build` | N/A |
| docker-compose.yml | `docker compose down && docker compose up -d` | N/A |

### Checking Service Status

```bash
# Docker: List all services
docker compose ps

# Docker: View logs
docker compose logs -f web
docker compose logs -f celery

# Check health endpoint
curl http://localhost:8000/health/
```

## Testing

### Running Tests

#### Django Unit Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test novels

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Manual API Testing

#### Authentication

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Save the token from response
TOKEN="your-token-here"
```

#### Projects

```bash
# Create project
curl -X POST http://localhost:8000/api/projects/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Novel","description":"A test novel","genre":"Fantasy","target_word_count":50000}'

# List projects
curl -X GET http://localhost:8000/api/projects/ \
  -H "Authorization: Token $TOKEN"
```

### Load Testing

#### Using Apache Bench

```bash
# Install apache2-utils
sudo apt-get install apache2-utils

# Test homepage
ab -n 1000 -c 10 http://localhost:8000/

# Test API endpoint (with authentication)
ab -n 100 -c 5 -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/projects/
```

### Security Testing

```bash
# Check security headers
curl -I http://localhost:8000

# Dependency vulnerability scan
pip install safety
safety check
```

## Project Structure

```
agent/
├── novel_agent/                 # Core novel writing agent library
│   ├── __init__.py
│   ├── cli.py                   # Interactive CLI
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Configuration
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── long_term_memory.py  # Vector store memory
│   │   └── context_manager.py   # Context management
│   ├── data/
│   │   ├── __init__.py
│   │   └── example_manager.py   # Good/bad examples
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── brainstorming.py
│   │   ├── plot_generator.py
│   │   ├── character_generator.py
│   │   ├── setting_generator.py
│   │   ├── outliner.py
│   │   ├── chapter_writer.py
│   │   ├── editor.py
│   │   └── consistency_checker.py
│   └── output/
│       ├── __init__.py
│       ├── exporter.py          # Multi-language export
│       └── scorer.py            # Scoring system
├── novel_web/                   # Django web application
│   ├── manage.py
│   ├── novel_web/               # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── novels/                  # Main Django app
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── tasks.py             # Celery tasks
│   │   ├── services.py          # Business logic
│   │   └── api/                 # REST API
│   ├── frontend/                # Frontend templates & static files
│   │   ├── templates/
│   │   └── static/
│   ├── locale/                  # Translation files
│   ├── requirements-web.txt     # Web app dependencies
│   ├── Dockerfile
│   └── docker-compose.yml
├── main.py                      # CLI entry point
├── example_workflow.py          # Example demonstration
├── requirements.txt             # Core dependencies
├── setup.py
└── README.md                    # This file
```

## Configuration

Edit `novel_agent/config/settings.py` to customize:

- Model settings (GPT model, temperature, max tokens)
- Memory directories
- Scoring category weights
- Supported languages

### Scoring Categories

Default categories and weights (can be adjusted):

| Category | Weight |
|----------|--------|
| Story/Plot | 30% |
| Character Development | 20% |
| World-Building / Setting | 15% |
| Writing Style / Language | 20% |
| Dialogue & Interactions | 10% |
| Emotional Impact / Engagement | 5% |

```python
from novel_agent.output import NovelScorer

# Custom weights
scorer = NovelScorer(custom_categories={
    "Plot": 40,
    "Characters": 30,
    "Writing": 30
})
```

### Web Application Configuration

Edit `novel_web/novel_web/settings.py` for:
- Database configuration
- Redis/Celery settings
- Security settings
- Language settings
- Static files configuration

## Extending the System

### Add a New Module

1. Create module in `novel_agent/modules/`:
```python
from langchain_openai import ChatOpenAI

class MyModule:
    def __init__(self, context_manager, memory):
        self.context_manager = context_manager
        self.memory = memory
        self.llm = ChatOpenAI(...)
```

2. Import in `novel_agent/modules/__init__.py`

3. Add to CLI in `novel_agent/cli.py`

### Add a New Scoring Category

```python
scorer.add_category("Pacing", 15)
scorer.update_weights({
    "Story/Plot": 25,  # Reduced from 30
    "Pacing": 15       # New category
})
```

## Troubleshooting

### ChromaDB Issues

If you encounter ChromaDB errors, clear the memory:
```python
memory = LongTermMemory()
memory.clear_memory()
```

### "No OpenAI API key" Error

Make sure OPENAI_API_KEY is set in your .env file.

### Celery Tasks Not Processing

Check that:
1. Redis is running: `redis-cli ping` should return "PONG"
2. Celery worker is running: check the terminal logs
3. WebSocket connection works: check browser console

### WebSocket Connection Failed

1. Ensure Redis is running
2. Check REDIS_URL in .env
3. Try refreshing the page

### Database Errors

```bash
# Reset database (WARNING: deletes all data)
python manage.py flush

# Or delete and recreate
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### "permission denied" or "vector_store_dir" Errors

These were fixed in recent updates. Make sure you have:
1. Updated to the latest code
2. Rebuilt Docker containers: `docker compose up -d --build`
3. Updated dependencies to match local environment

### Service Won't Start After Restart

```bash
# Docker: Check logs
docker compose logs web

# Docker: Check if port is in use
docker compose ps
sudo netstat -tulpn | grep 8000
```

## Future Enhancements

- [ ] More export formats (PDF, EPUB, DOCX)
- [ ] Collaborative writing support
- [ ] Version control for drafts
- [ ] Advanced plotting tools (beat sheets, story circles)
- [ ] Style transfer from favorite authors
- [ ] Automated fact-checking
- [ ] Character dialogue voice training
- [ ] More language support
- [ ] Real-time collaborative editing

## License

This project is for educational and creative purposes.

## Acknowledgments

Built with:
- LangChain for LLM orchestration
- OpenAI GPT models for generation
- ChromaDB for vector storage
- Django for web framework
- Celery for async task processing
- Rich for terminal UI (CLI)
- Channels for WebSocket support

---

## How to Restart Service to Validate Changes

After making any changes to the code, dependencies, or configuration, follow these steps to restart the service and validate the changes:

### For Docker Deployment

```bash
# Navigate to the web directory
cd /path/to/agent/novel_web

# Step 1: Stop all services
docker compose down

# Step 2: Rebuild containers with new changes
docker compose up -d --build

# Step 3: Wait for services to start (10-15 seconds)
sleep 15

# Step 4: Check service status
docker compose ps

# Step 5: Verify package versions (if dependencies were updated)
docker compose exec web pip list | grep -E "(langchain|openai)"

# Step 6: Check logs for errors
docker compose logs -f web
# Press Ctrl+C to stop following logs

# Step 7: Test the application
# Open browser and visit: http://localhost:8000
# - Login to your account
# - Create or select a project
# - Try the brainstorming feature to generate ideas
# - Verify no errors appear

# Step 8: Check health endpoints
curl http://localhost:8000/health/
curl http://localhost:8000/health/detailed/
```

### For Local Development

```bash
# Step 1: Stop all running services
# Press Ctrl+C in each terminal running Django, Celery, or Redis

# Step 2: Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Step 3: Update dependencies (if changed)
pip install -r requirements-web.txt

# Step 4: Run migrations (if models changed)
python manage.py migrate

# Step 5: Collect static files (if static files changed)
python manage.py collectstatic --noinput

# Step 6: Restart Django (Terminal 1)
python manage.py runserver 0.0.0.0:8000

# Step 7: Restart Celery (Terminal 2)
celery -A novel_web worker -l info

# Step 8: Ensure Redis is running (Terminal 3, if not running as service)
redis-server

# Step 9: Test the application
# Open browser and visit: http://localhost:8000
# Follow the same testing steps as Docker deployment above
```

### Quick Validation Checklist

After restart, verify:
- [ ] Web service is accessible at http://localhost:8000
- [ ] Admin panel loads at http://localhost:8000/admin/
- [ ] Login works correctly
- [ ] Can create new project
- [ ] Brainstorming feature generates ideas without errors
- [ ] No error messages in browser console (F12 → Console)
- [ ] No error messages in service logs
- [ ] All Docker containers show "healthy" status (Docker only)
- [ ] Language switcher works (if i18n changes were made)

### Common Issues After Restart

**Issue: "No such table" error**
```bash
# Solution: Run migrations
docker compose exec web python manage.py migrate
```

**Issue: Static files not loading**
```bash
# Solution: Collect static files
docker compose exec web python manage.py collectstatic --noinput
docker compose restart web
```

**Issue: Celery tasks not processing**
```bash
# Solution: Restart celery worker
docker compose restart celery

# Check celery logs
docker compose logs -f celery
```

**Issue: Port 8000 already in use**
```bash
# Solution: Find and kill the process
sudo lsof -i :8000
sudo kill -9 <PID>

# Or restart Docker
docker compose restart
```

---

**Happy Writing! 📚✨**
