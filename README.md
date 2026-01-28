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
- [Vector Memory Architecture](#vector-memory-architecture)
- [5-Layer Prompt Architecture](#5-layer-prompt-architecture)
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

5. **Writing**
   - Write chapters paragraph-by-paragraph
   - Generate dialogue, descriptions, and action scenes
   - Multi-language support (English, Chinese, French, Spanish, etc.)

6. **Editing & Refinement**
   - Style improvements
   - Pacing adjustments
   - Grammar and mechanics checking
   - Dialogue enhancement
   - Text compression

7. **Consistency Checking**
   - Character trait consistency
   - Setting and world-building consistency
   - Timeline verification
   - Plot consistency

8. **Scoring System**
   - Adjustable scoring categories and weights
   - Detailed feedback for each category
   - Overall grade and recommendations

9. **Example Management**
    - Store good and bad writing examples
    - Learn from examples during generation
    - Category-based organization

10. **Multi-Language Export**
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
5. Writing a complete chapter
6. Editing for style
7. Checking consistency
8. Scoring the chapter
9. Exporting to file

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
7. Start writing chapters!

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

#### 5. Write Chapters

Click "Write Chapter" to have the AI:
- Generate full chapters based on your plot and acts
- Match your specified style
- Maintain consistency with previous chapters

#### 6. Edit and Refine

Use the chapter editor tools:
- **Style Edit**: Improve prose quality
- **Grammar Check**: Fix errors
- **Consistency Check**: Ensure continuity
- **Expand**: Add more detail
- **Condense**: Tighten the prose

#### 7. Score Novel

When complete, click "Score Novel" to get:
- Overall score (0-100)
- Category breakdowns:
  - Story/Plot (30%)
  - Character Development (20%)
  - World-Building (15%)
  - Writing Style (20%)
  - Dialogue (10%)
  - Emotional Impact (5%)

#### 8. Export

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
2. **简体中文** (`zh-Hans`) - Simplified Chinese

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
docker compose exec web python manage.py makemessages -l zh_Hans

# For local setup
python manage.py makemessages -l zh_Hans
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

## Vector Memory Architecture

### Overview

The Novel Writing Agent uses **vector memory** (embeddings and semantic search) to maintain long-term context across the entire novel project. This enables the AI to write Chapter 10 with full awareness of events, characters, and themes from Chapters 1-9, even when those details exceed the LLM's context window.

**Core Technology Stack:**
- **Vector Database**: ChromaDB (persistent vector storage)
- **Embeddings**: OpenAI Embeddings API (1536-dimensional vectors)
- **Framework**: LangChain for vector operations
- **Storage Location**: `/app/media/vector_stores/` (project-specific collections)

### The Problem Vector Memory Solves

Traditional LLMs have limited context windows (8K-32K tokens). When writing a novel:
- Chapter 10 needs to remember events from Chapter 1
- Characters must maintain consistent personalities across 50+ chapters
- Plot threads introduced early must pay off later
- World-building rules must remain consistent

**Without vector memory**: The LLM only sees the current prompt (limited context).

**With vector memory**: The LLM gets **semantically relevant context** retrieved from the entire project history via similarity search.

---

### How It Works: Chapter Generation Workflow

#### 1. Content Storage (`novel_agent/memory/long_term_memory.py`)

When project content is created, it's converted to embeddings and stored:

```python
# Each project gets its own ChromaDB collection
collection_name = f"project_{project_id}_hex"

# Storage methods automatically embed and store content:
memory.store_character(name="Alice", profile="...")     # → Embedded & stored
memory.store_plot(plot_data)                            # → Embedded & stored
memory.store_chapter(chapter_number=1, content="...")   # → Chunked, embedded & stored
memory.store_setting(name="Magic System", details="...") # → Embedded & stored
```

**Document Chunking**: Large chapters are split into 1000-character chunks with 200-char overlap for better retrieval precision.

**Metadata Storage**: Each document includes:
- `type`: "character", "plot", "chapter", "setting"
- `name`/`title`: Item identifier
- `timestamp`: Creation time
- `chapter_number`: For chapters
- `chunk_index`: For chunked documents

#### 2. Chapter Generation Request Flow

```
User clicks "Write Chapter"
    ↓
write_chapter_task() [Celery async task]
    ↓
ChapterWriter.write_chapter()
    ↓
[CONTEXT BUILDING PHASE] ← Vector memory retrieval happens here
    ↓
ContextManager.build_context_for_task("writing")
```

#### 3. Semantic Context Retrieval (`context_manager.py:27-114`)

Before generating any chapter content, the system retrieves relevant context using **semantic similarity search**:

**A. Plot Summary**
```python
plot = memory.get_plot_summary()  # Retrieves all documents with type="plot"
# Returns: Main plot arc, themes, story structure
```

**B. Character Profiles**
```python
characters = memory.get_all_characters()  # Up to 5 most relevant characters
# Returns: Personalities, motivations, relationships, character arcs
```

**C. World/Setting Details**
```python
settings = memory.retrieve_by_type("setting", k=3)
# Returns: Top 3 relevant setting details (magic systems, geography, culture)
```

**D. Previous Chapter Context** (KEY SEMANTIC SEARCH)
```python
recent_chapters = memory.retrieve_context(
    query=f"Chapter {chapter_number} - {chapter_title}",
    k=2,
    filter_type="chapter"
)
# Returns: 2 most semantically similar previous chapters
# Uses vector similarity to find relevant past content!
```

**Example**:
- Writing Chapter 10: "Alice confronts the villain"
- Vector search finds:
  - Chapter 3: "Alice discovers the villain's identity" (semantically similar)
  - Chapter 7: "Alice trains for battle" (semantically similar)
- These become context even though they're not adjacent chapters

#### 4. Context Assembly for LLM

Retrieved content is formatted into a context string:

```python
context_string = f"""
Plot Summary: {plot_summary}

Characters:
{character_profiles}

World-Building:
{setting_details}

Previous Chapter Context:
{semantically_relevant_chapters}
"""
```

This context (truncated to ~1500 chars) is prepended to the LLM prompt, giving it awareness of relevant project history.

#### 5. Scene Writing with Vector Context

For each scene in the chapter:

```python
def _write_scene(scene, act, context, good_examples, ...):
    prompt = f"""
    You are writing Chapter {number}.

    **Context from vector memory:**
    {context}  # ← Plot, characters, settings, previous chapters

    **Good writing examples:**
    {good_examples}

    **Write the following scene:**
    {scene_description}
    """

    return llm.generate(prompt)
```

The LLM generates content **informed by** all retrieved vector context, ensuring consistency and continuity.

#### 6. Storing Generated Content

After chapter generation:

```python
memory.store_chapter(
    chapter_number=10,
    content=generated_content,
    metadata={
        "type": "chapter",
        "title": chapter_title,
        "timestamp": datetime.now()
    }
)
```

The new chapter is embedded and stored, becoming part of the vector memory for future chapters.

---

### Key Benefits of Vector Memory

#### 1. **Semantic Context Retrieval**
- Not just "previous 3 chapters" but **semantically relevant** chapters
- If Chapter 15 is about a wedding, vector search finds Chapter 2 where the couple met
- Maintains thematic consistency across non-adjacent chapters

#### 2. **Character Consistency** (`consistency_checker.py:30-86`)
```python
characters = memory.get_all_characters()  # Retrieves all character profiles
# Checks new content against stored character traits
# Catches: personality changes, forgotten characteristics, contradictions
```

#### 3. **Plot Continuity**
- Maintains story arcs across many chapters
- Remembers plot threads introduced earlier (Chekhov's gun)
- Ensures foreshadowing payoff

#### 4. **World-Building Validation**
- Consistent magic system rules
- Accurate geography and setting details
- Maintained cultural/social norms

#### 5. **Long-Term Memory Beyond Token Limits**
- LLM context window: 8K-32K tokens (limited)
- Vector store: **Unlimited** - entire project history available
- Semantic search retrieves only what's relevant for current task

---

### Project Isolation with ChromaDB Collections

Each novel project gets its own isolated ChromaDB collection:

```python
# novels/models.py:188-220
class NovelProject(models.Model):
    chroma_collection_name = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        if not self.chroma_collection_name:
            # Generate unique collection name
            self.chroma_collection_name = f"project_{self.id.hex[:16]}"
        super().save(*args, **kwargs)
```

**Result**: Novel A's characters don't pollute Novel B's context. Each project has completely independent vector memory.

---

### File Locations & Key Functions

| Component | File Path | Key Method | Lines |
|-----------|-----------|-----------|-------|
| **Vector Storage** | `novel_agent/memory/long_term_memory.py` | `store_chapter()` | 88-114 |
| **Vector Retrieval** | `novel_agent/memory/long_term_memory.py` | `retrieve_context()` | 158-179 |
| **Context Building** | `novel_agent/memory/context_manager.py` | `build_context_for_task()` | 27-114 |
| **Chapter Writer** | `novel_agent/modules/chapter_writer.py` | `write_chapter()` | 39-108 |
| **Scene Writing** | `novel_agent/modules/chapter_writer.py` | `_write_scene()` | 275-332 |
| **Consistency Check** | `novel_agent/modules/consistency_checker.py` | `check_character_consistency()` | 30-86 |
| **Celery Task** | `novels/tasks.py` | `write_chapter_task()` | 163-316 |
| **Project Service** | `novels/services.py` | `ProjectService.__init__()` | 73-98 |
| **Django Model** | `novels/models.py` | `NovelProject.chroma_collection_name` | 188-220 |

---

### Vector Memory Storage Configuration

Storage location is configured in Django settings:

```python
# novel_web/settings.py:199-206
NOVEL_AGENT = {
    'VECTOR_STORE_DIR': Path(MEDIA_ROOT) / 'vector_stores',
    'EXAMPLES_DIR': Path(MEDIA_ROOT) / 'examples',
    'OUTPUT_DIR': Path(MEDIA_ROOT) / 'exports',
}
```

In Docker: `/app/media/vector_stores/`

---

### Embedding Process Details

1. **Embedding Creation**: OpenAI API generates 1536-dimensional vector embeddings
2. **Storage**: Embeddings stored in ChromaDB with document metadata
3. **Retrieval**: Semantic similarity search via cosine similarity
4. **Filtering**: Results can be filtered by document type (character, plot, chapter, etc.)

### Vector Search Query Example

```python
# Find chapters semantically similar to "Alice defeats the dragon"
similar_chapters = memory.retrieve_context(
    query="Alice defeats the dragon",
    k=3,  # Return top 3 most similar
    filter_type="chapter"  # Only search chapter documents
)

# ChromaDB performs cosine similarity search on 1536-dim vectors
# Returns chapters with highest semantic similarity scores
```

---

### In Summary

Vector memory transforms chapter generation from:
- ❌ **Without**: "Write Chapter 10 with only this prompt and 8K token limit"

To:
- ✅ **With**: "Write Chapter 10 with semantic awareness of all relevant plot points, character development, world-building details, and previous chapters across the entire 50-chapter project"

The LLM receives **intelligent, contextually-relevant information** via semantic search instead of trying to fit everything into the limited token context window. This enables truly consistent, coherent long-form novel generation.

## 5-Layer Prompt Architecture

### Overview

The Novel Writing Agent uses a **5-layer prompt architecture** that separates concerns and provides a composable, maintainable system for AI prompt generation. This architecture enables multi-language support, reusable writing styles, and consistent AI behavior across different tasks.

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│  Layer 5: User Prompt (Short-Lived)        │  ← Task-specific instructions
├─────────────────────────────────────────────┤
│  Layer 4: Project Memory (Long-Term)       │  ← Plot, characters, settings
├─────────────────────────────────────────────┤
│  Layer 3: Style & Techniques (Composable)  │  ← Writing styles, techniques
├─────────────────────────────────────────────┤
│  Layer 2: Role Definition (Agent Identity) │  ← Agent-specific prompts
├─────────────────────────────────────────────┤
│  Layer 1: System Policy (Immutable Rules)  │  ← Safety, copyright rules
└─────────────────────────────────────────────┘
```

### Layer 1: System Policy (Immutable Rules)

**Purpose**: Enforce unchanging constraints across all AI operations

**Model**: `SystemPolicy` with `SystemPolicyTranslation`

**Examples**:
- Safety guidelines (no harmful content)
- Copyright compliance
- Output format constraints
- Behavioral boundaries

**Properties**:
- `name_key`: Unique identifier
- `policy_type`: safety | copyright | output | behavior
- `priority`: Lower number = higher priority
- `is_active`: Whether policy is enforced

**Management**: System-wide, managed by administrators via Django admin

**API Endpoint**: `GET /api/system-policies/` (read-only)

---

### Layer 2: Agent Role (Agent Identity)

**Purpose**: Define specific AI agent personalities and capabilities

**Model**: `AgentRole` with `AgentRoleTranslation`

**Examples**:
- Brainstormer: Creative idea generation
- Plotter: Story structure development
- Writer: Chapter composition
- Text Modifier: Content editing and refinement

**Properties**:
- `name_key`: Unique identifier (e.g., 'brainstormer', 'plotter')
- `module_name`: Associated module name
- `is_active`: Whether role is available

**Management**: System-wide, managed by administrators via Django admin

**API Endpoint**: `GET /api/agent-roles/` (read-only)

---

### Layer 3: Style & Techniques (Composable)

**Purpose**: Provide reusable writing styles and techniques

#### Writing Styles

**Model**: `WritingStyle` with `WritingStyleTranslation`

**Examples**:
- Literary Fiction: Slow pacing, long paragraphs, low dialogue
- Action Thriller: Fast pacing, short paragraphs, high dialogue
- Romance: Medium pacing, medium paragraphs, high dialogue

**Properties**:
- `name_key`: Unique identifier
- `is_system`: True for predefined system styles
- `public`: Whether publicly available
- `pacing`: slow | medium | fast
- `tone`: Description of tone (e.g., "dark", "humorous")
- `paragraph_length`: short | medium | long
- `dialogue_ratio`: low | medium | high
- `cliffhanger_enabled`: Boolean

**API Endpoints**:
- `GET /api/writing-styles/` - List accessible styles
- `POST /api/writing-styles/` - Create custom style
- `PUT /api/writing-styles/{id}/` - Update own style
- `DELETE /api/writing-styles/{id}/` - Delete own style

#### Writing Techniques

**Model**: `WritingTechnique` with `WritingTechniqueTranslation`

**Examples**:
- Show Don't Tell: Narrative technique
- Foreshadowing: Narrative technique
- Active Voice: Description technique
- Subtext in Dialogue: Dialogue technique

**Properties**:
- `name_key`: Unique identifier
- `is_system`: True for predefined system techniques
- `public`: Whether publicly available
- `category`: narrative | dialogue | description | pacing | character

**API Endpoints**:
- `GET /api/writing-techniques/` - List accessible techniques
- `POST /api/writing-techniques/` - Create custom technique
- `PUT /api/writing-techniques/{id}/` - Update own technique
- `DELETE /api/writing-techniques/{id}/` - Delete own technique

**Composition**: Multiple techniques can be combined with a single style for a project

---

### Layer 4: Project Memory (Long-Term Context)

**Purpose**: Provide project-specific context to AI operations

**Context Types**:
- `plot`: Plot premise, themes, structure, acts
- `character`: Key characters (protagonist, antagonist, mentor)
- `chapter`: Existing chapter content
- `brainstorm`: Idea generation context

**Dynamically Assembled**: Built from project data (Plot, Characters, Settings)

**Example Context**:
```
**Premise:** A young wizard discovers their true heritage
**Themes:** Coming of age, power vs responsibility
**Story Structure:**
- Act 1 (Setup, 25%): Introduction to magical world
- Act 2 (Confrontation, 50%): Learning magic, facing challenges
- Act 3 (Resolution, 25%): Final battle and acceptance

**Key Characters:**
- Alex (protagonist): Orphan with hidden magical powers
- Morgan (antagonist): Dark wizard seeking revenge

**Primary Setting:** Thornwood Academy - Ancient magical school
```

---

### Layer 5: User Prompt (Short-Lived)

**Purpose**: Task-specific instructions for current operation

**Examples**:
- "Generate 3 creative plot ideas for the Fantasy genre"
- "Write Chapter 5 based on the act"
- "Modify this text to be more dramatic"

**Lifespan**: Single operation only

---

### Multi-Language Support

The architecture supports multiple languages through translation models:

**Supported Languages** (as of current implementation):
- English (`en`)
- Simplified Chinese (`zh-hans`)

**Extensibility**: Easy to add new languages by:
1. Adding language code to `LANGUAGE_CHOICES` in models
2. Creating translations for SystemPolicy, AgentRole, WritingStyle, WritingTechnique
3. Running the seed command: `python manage.py seed_prompt_architecture`

**Language Selection**:
- Projects have a `target_language` field (defaults to 'en')
- PromptAssemblyService uses this to fetch correct translations
- Fallback mechanism: If translation not found, falls back to English

**Language Output Instruction**: Automatically appended to user message when language is not English:
```
**IMPORTANT:** Generate all output in [Language Name].
```

---

### PromptAssemblyService

**File**: `novels/prompt_assembly.py`

#### Core Methods

**`build_system_prompt(agent_role_key, language_code='en')`**

Builds Layer 1 + Layer 2: System policies + Agent role

```python
system_prompt = PromptAssemblyService.build_system_prompt(
    agent_role_key='brainstormer',
    language_code='zh-hans'
)
```

Returns concatenated string of:
1. Active system policies (in priority order)
2. Agent role system prompt

---

**`build_style_instructions(project, language_code='en')`**

Builds Layer 3: Style + Techniques instructions

```python
style_instructions = PromptAssemblyService.build_style_instructions(
    project=my_project,
    language_code='en'
)
```

Returns concatenated string of:
1. Writing style instructions (project default or chapter override)
2. All selected technique instructions

---

**`build_context_prompt(project, context_type, **kwargs)`**

Builds Layer 4: Project memory context

```python
context = PromptAssemblyService.build_context_prompt(
    project=my_project,
    context_type='chapter'  # plot | character | chapter | brainstorm
)
```

Returns formatted context including:
- Plot context (premise, themes, acts)
- Character context (key characters)
- Setting context (primary location)

---

**`assemble_full_prompt(...)`**

**Master Method**: Assembles all 5 layers into final (system_message, user_message)

```python
system_message, user_message = PromptAssemblyService.assemble_full_prompt(
    agent_role_key='writer',
    user_prompt='Write Chapter 5 based on the act',
    project=my_project,
    language_code='zh-hans',
    context_type='chapter',
    act=act,
    include_context=True
)
```

**Returns**:
- `system_message`: Layer 1 + Layer 2
- `user_message`: Layer 4 + Layer 3 + Layer 5 (+ language instruction)

---

### Usage Examples

#### Example 1: Brainstorming Ideas

```python
from novels.prompt_assembly import PromptAssemblyService
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Assemble prompt
system_msg, user_msg = PromptAssemblyService.assemble_full_prompt(
    agent_role_key='brainstormer',
    user_prompt='Generate 3 creative plot ideas for the Fantasy genre',
    project=project,
    language_code='en',
    context_type='brainstorm',
    include_context=False  # No need for project context when brainstorming
)

# Call LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
response = llm.invoke([
    SystemMessage(content=system_msg),
    HumanMessage(content=user_msg)
])
```

---

#### Example 2: Writing a Chapter

```python
# Assemble prompt with full context
system_msg, user_msg = PromptAssemblyService.assemble_full_prompt(
    agent_role_key='writer',
    user_prompt='Write Chapter 5 based on the act',
    project=project,
    language_code='zh-hans',  # Output in Simplified Chinese
    context_type='chapter',
    act=act,
    include_context=True  # Include plot, characters, settings
)

# Call LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
response = llm.invoke([
    SystemMessage(content=system_msg),
    HumanMessage(content=user_msg)
])
```

---

#### Example 3: Modifying Text

```python
# Text modification uses a different approach
from novels.services import AIModificationService

result = AIModificationService.modify_text_selection(
    user=user,
    original_text="The hero walked into the room.",
    user_prompt="Make this more dramatic",
    content_type='chapter'
)

# Returns: {
#     'original_text': '...',
#     'modified_text': '...',
#     'user_prompt': '...',
#     'token_usage': {...}
# }
```

---

### Database Schema

#### Core Models

```
SystemPolicy                      AgentRole
├── SystemPolicyTranslation      ├── AgentRoleTranslation

WritingStyle                     WritingTechnique
├── WritingStyleTranslation      ├── WritingTechniqueTranslation

NovelProject
├── default_style (FK → WritingStyle)
├── selected_techniques (M2M → WritingTechnique)
├── target_language (CharField)
```

#### Translation Models Pattern

All translation models follow this pattern:
- Foreign key to parent model with `related_name='translations'`
- `language_code`: Choice field with supported languages
- Content fields (e.g., `content`, `system_prompt`, `instructions`)
- `unique_together` constraint on `(parent, language_code)`
- Index on `language_code` for fast lookups

---

### Seeding Data

The system includes a management command to populate initial data:

```bash
python manage.py seed_prompt_architecture
```

**What it does**:
1. Creates system policies (safety, copyright, output, behavior)
2. Creates agent roles (brainstormer, plotter, writer, text_modifier)
3. Creates writing styles (literary, action, romance, mystery)
4. Creates writing techniques (show_dont_tell, foreshadowing, etc.)
5. Creates translations for English and Simplified Chinese

**File**: `novels/management/commands/seed_prompt_architecture.py`

---

### Migration

The 5-layer architecture was introduced in migration `0019_add_prompt_architecture.py`

**Changes**:
1. Added `target_language` field to `NovelProject`
2. Created `SystemPolicy` and `SystemPolicyTranslation` models
3. Created `AgentRole` and `AgentRoleTranslation` models
4. Created `WritingStyle` and `WritingStyleTranslation` models
5. Created `WritingTechnique` and `WritingTechniqueTranslation` models
6. Added relationships to `NovelProject`

---

### Best Practices

#### For Developers

1. **Always use PromptAssemblyService**: Never construct prompts manually
2. **Respect language settings**: Always pass `project.target_language` to assembly methods
3. **Test with multiple languages**: Ensure translations exist for all supported languages
4. **Use context appropriately**: Match `context_type` to the operation being performed
5. **Handle missing translations**: PromptAssemblyService falls back to English

#### For Content Creators

1. **System items are protected**: Cannot modify `is_system=True` items
2. **Share wisely**: Set `public=True` only for well-tested styles/techniques
3. **Provide translations**: Create translations for all languages you support
4. **Test combinations**: Try different style + technique combinations
5. **Use descriptive names**: Make `name_key` and display names clear and intuitive

---

### API Endpoints Summary

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/system-policies/` | GET | List active system policies | Required |
| `/api/agent-roles/` | GET | List active agent roles | Required |
| `/api/writing-styles/` | GET | List accessible writing styles | Required |
| `/api/writing-styles/` | POST | Create custom writing style | Required |
| `/api/writing-styles/{id}/` | PUT | Update own writing style | Required |
| `/api/writing-styles/{id}/` | DELETE | Delete own writing style | Required |
| `/api/writing-techniques/` | GET | List accessible writing techniques | Required |
| `/api/writing-techniques/` | POST | Create custom writing technique | Required |
| `/api/writing-techniques/{id}/` | PUT | Update own writing technique | Required |
| `/api/writing-techniques/{id}/` | DELETE | Delete own writing technique | Required |

---

### Refactored Services

The following services have been refactored to use the 5-layer prompt architecture:

#### All Phases Completed ✅

- **AIModificationService** - Text modification using PromptAssemblyService
- **BrainstormService** - Idea generation using agent_role_key='brainstormer'
- **PlotService** - Plot creation using agent_role_key='plotter'
- **WritingService** - Chapter writing using agent_role_key='writer'
- **CharacterService** - Character creation using agent_role_key='character_creator'
- **SettingService** - Setting/location creation using agent_role_key='setting_creator'
- **EditingService** - Content editing using agent_role_key='editor'
- **ConsistencyService** - Consistency checking using agent_role_key='consistency_checker'

**All major content generation and editing services have been refactored!**

The Novel Writing Agent now uses the 5-layer prompt architecture consistently across all core operations:
- Brainstorming & Ideation
- Plot & Structure
- Character Development
- Setting & World-Building
- Content Writing
- Editing & Refinement
- Consistency Checking

---

### Prompt Architecture Future Enhancements

#### Short-term
- Add more languages (Spanish, French, German, Japanese)
- Create web UI for managing styles and techniques
- Add versioning for system policies and roles
- User-specific style libraries

#### Long-term
- Community marketplace for styles/techniques
- A/B testing different prompt combinations
- Analytics on which styles/techniques perform best
- Machine learning to optimize prompt effectiveness

---

### Prompt Architecture Troubleshooting

#### Issue: Translations not showing up

**Solution**:
1. Check that translation exists: `WritingStyle.objects.get(name_key='...').translations.all()`
2. Verify language code matches: Use exact codes like 'zh-hans', not 'zh'
3. Run seed command if system data is missing

#### Issue: Empty system prompt

**Symptom**: Log shows "Built system prompt for X: 0 chars"

**Solution**:
1. Check that agent role exists: `AgentRole.objects.filter(name_key='brainstormer', is_active=True)`
2. Check that translation exists: `role.translations.filter(language_code='en').first()`
3. Run seed command to populate data

#### Issue: Style not applying

**Solution**:
1. Check project has `default_style` set: `project.default_style`
2. Verify style has translations for the project's `target_language`

---

### References

- **Django Models**: `novels/models.py`
- **Prompt Assembly**: `novels/prompt_assembly.py`
- **Serializers**: `novels/serializers.py`
- **ViewSets**: `novels/views.py`
- **API Routes**: `novels/api_urls.py`
- **Admin Config**: `novels/admin.py`
- **Seed Command**: `novels/management/commands/seed_prompt_architecture.py`
- **Migration**: `novels/migrations/0019_add_prompt_architecture.py`

---

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
