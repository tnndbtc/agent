# Novel Writing Agent - Web Interface

A mobile-responsive web application for AI-powered novel writing, built with Django and featuring real-time progress tracking.

## Features

- **User Authentication**: Secure user registration and login
- **Project Management**: Create and manage multiple novel projects
- **AI-Powered Writing**:
  - Brainstorm plot ideas
  - Generate characters, settings, and plot structures
  - Create chapter outlines
  - Write and edit chapters with AI assistance
  - Consistency checking across your novel
  - Novel scoring system
- **Real-Time Updates**: WebSocket-based progress tracking for AI operations
- **Mobile-Optimized**: Responsive design with touch gestures and PWA support
- **Async Processing**: Long-running AI tasks handled by Celery workers

## Tech Stack

- **Backend**: Django 5.0, Django REST Framework, Django Channels
- **Database**: PostgreSQL (production) or SQLite (development)
- **Cache/Broker**: Redis
- **Task Queue**: Celery
- **AI**: OpenAI GPT models via LangChain
- **Memory**: ChromaDB vector store
- **Frontend**: Mobile-first responsive CSS, vanilla JavaScript
- **PWA**: Service Worker for offline capabilities and installability

## Prerequisites

- Python 3.11+
- PostgreSQL 16+ (for production)
- Redis 7+
- OpenAI API key

## 🚀 How to Start and Run

### Method 1: Automated Setup (Easiest)

Use the automated setup script that handles everything:

```bash
cd novel_web
chmod +x setup.sh
./setup.sh
```

The script will:
1. Create `.env` configuration file
2. Prompt you to add your OpenAI API key
3. Let you choose Docker or local setup
4. Install dependencies
5. Setup database and create admin user
6. Start all services

**After setup completes:**
- Visit http://localhost:8000
- Login with the admin credentials you created
- Click "Create New Project" to start writing!

---

### Method 2: Docker (Recommended)

**Step 1: Configure Environment**
```bash
cd novel_web
cp .env.example .env
```

Edit `.env` and set:
```bash
OPENAI_API_KEY=your-openai-api-key-here
SECRET_KEY=your-secret-key  # Generate with command below
```

Generate SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Step 2: Start Services**
```bash
# Build and start all services (PostgreSQL, Redis, Django, Celery)
docker compose up -d

# Run database migrations
docker compose exec web python manage.py migrate

# Create your admin account
docker compose exec web python manage.py createsuperuser
# Enter username, email, and password when prompted

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

**Step 3: Access the Application**
- Open http://localhost:8000 in your browser
- Login with the admin credentials you created
- Start creating your novel!

**Managing Services:**
```bash
# View logs
docker compose logs -f web

# Stop services (keeps data)
docker compose down

# Complete cleanup - removes all volumes (database, redis, media)
docker compose down -v

# Restart services
docker compose restart

# Rebuild after code changes
docker compose up -d --build
```

---

### Method 3: Local Development (Without Docker)

**Step 1: Setup Virtual Environment**
```bash
cd novel_web

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 2: Install Dependencies**
```bash
# First, install the novel_agent package from parent directory
pip install -e ../

# Then install web application dependencies
pip install -r requirements-web.txt
```

**Step 3: Configure Environment**
```bash
cp .env.example .env
```

Edit `.env` and set:
```bash
OPENAI_API_KEY=your-openai-api-key-here
SECRET_KEY=your-secret-key

# For quick testing with SQLite (no PostgreSQL needed):
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# For production with PostgreSQL:
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=novel_agent_db
# DB_USER=your_username
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
```

**Step 4: Setup Database**
```bash
# Run migrations
python manage.py migrate

# Create admin account
python manage.py createsuperuser
# Follow prompts to enter username, email, password

# Collect static files
python manage.py collectstatic --noinput
```

**Step 5: Start Services**

You need 3 terminal windows:

**Terminal 1 - Django Web Server:**
```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Celery Worker (for AI tasks):**
```bash
source venv/bin/activate
celery -A novel_web worker -l info
```

**Terminal 3 - Redis:**
```bash
# If Redis is not installed as a service:
redis-server

# If Redis is already running, you can skip this
```

**Step 6: Access the Application**
- Open http://localhost:8000
- Login with your admin credentials
- Create your first novel project!

---

### ✅ Verify Everything is Working

After starting the application, check:

1. **Health Check**: Visit http://localhost:8000/health/
   - Should return: `{"status": "healthy", "service": "novel-agent-web"}`

2. **Detailed Health**: Visit http://localhost:8000/health/detailed/
   - Should show database, Redis, and Celery status

3. **Admin Panel**: Visit http://localhost:8000/admin/
   - Login with your admin credentials

4. **Main App**: Visit http://localhost:8000
   - Should see the login/register page

### 📱 Access from Mobile Devices (Local Network)

Since the server binds to `0.0.0.0:8000`, you can access it from any device on your local network:

**Step 1: Find Your Computer's IP Address**

Use the helper script (easiest):
```bash
chmod +x show-ip.sh
./show-ip.sh
```

Or manually:

On Linux/Mac:
```bash
# Find your local IP (usually starts with 192.168.x.x)
hostname -I | awk '{print $1}'
# or
ip addr show | grep "inet " | grep -v 127.0.0.1
```

On Windows:
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

**Step 2: Update ALLOWED_HOSTS (if needed)**

Edit `.env` and add your local IP:
```bash
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,192.168.1.100
```
(Replace `192.168.1.100` with your actual IP address)

**Step 3: Restart the Server (if you changed .env)**
```bash
# Docker: restart services
docker compose restart web

# Local: Ctrl+C the runserver and restart it
```

**Step 4: Access from Mobile**

On your phone/tablet (connected to the same WiFi):
- Open browser
- Navigate to: `http://192.168.1.100:8000` (use your actual IP)
- The mobile-optimized interface will load
- Install as PWA for best experience!

**Note:** Docker users don't need to modify anything - the service already binds to `0.0.0.0:8000` and is accessible from the local network by default!

**Troubleshooting Mobile Access:**
- Ensure devices are on the same network
- Check firewall allows port 8000
- Verify `0.0.0.0` in ALLOWED_HOSTS
- Try `http://YOUR_IP:8000/health/` to test

### 🎯 First Steps After Installation

1. **Register/Login**: Create an account or use admin credentials
2. **Create Project**: Click "Create New Project"
   - Title: "My First Novel"
   - Genre: Choose any (e.g., Fantasy, Sci-Fi, Romance)
   - Target Word Count: 50000
3. **Brainstorm**: Click "Brainstorm Ideas" to generate plot ideas
4. **Watch Progress**: Progress bar shows AI generation in real-time
5. **Continue Writing**: Follow the workflow through plot, characters, outline, and chapters

### 🛑 Stopping the Application

**Docker:**
```bash
# Stop services (keeps data)
docker compose down

# Complete cleanup (removes all data including database, redis, media volumes)
docker compose down -v
```

**Note:** Use `docker compose down -v` when you want to completely reset the application and delete all database tables, Redis data, and uploaded files. This is useful for testing from a clean slate or troubleshooting persistent issues.

**Local Development:**
- Press `Ctrl+C` in each terminal window
- Deactivate virtual environment: `deactivate`

### 🔄 Restarting the Application

**Quick Restart (Docker):**
```bash
# Restart all services
docker compose restart

# Restart specific service only
docker compose restart web        # Django web server
docker compose restart celery     # Celery worker
docker compose restart db         # PostgreSQL database
docker compose restart redis      # Redis cache
```

**After Code Changes (Docker):**
```bash
# Rebuild and restart (for Python code changes)
docker compose up -d --build

# Or rebuild specific service
docker compose up -d --build web
```

**After Config Changes (Docker):**
```bash
# If you changed .env file or docker-compose.yml
docker compose down
docker compose up -d

# If you changed Django settings
docker compose restart web
```

**Local Development Restart:**
```bash
# If Django is running (Ctrl+C to stop, then):
python manage.py runserver 0.0.0.0:8000

# If Celery is running (Ctrl+C to stop, then):
celery -A novel_web worker -l info
```

**Common Restart Scenarios:**

| Scenario | Command |
|----------|---------|
| Changed Python code | `docker compose restart web` |
| Changed .env file | `docker compose restart web` |
| Changed database models | `docker compose exec web python manage.py migrate` then `docker compose restart web` |
| Changed static files | `docker compose exec web python manage.py collectstatic --noinput` then `docker compose restart web` |
| Changed Celery tasks | `docker compose restart celery` |
| Changed docker-compose.yml | `docker compose down && docker compose up -d` |
| Changed Dockerfile | `docker compose up -d --build` |
| Application not responding | `docker compose restart` |

---

## Project Structure

```
novel_web/
├── novel_web/              # Django project settings
│   ├── settings.py         # Main configuration
│   ├── celery.py          # Celery configuration
│   ├── asgi.py            # ASGI config for WebSockets
│   └── urls.py            # URL routing
├── novels/                 # Main application
│   ├── models.py          # Database models
│   ├── services.py        # Business logic layer
│   ├── views.py           # REST API views
│   ├── serializers.py     # DRF serializers
│   ├── tasks.py           # Celery async tasks
│   ├── consumers.py       # WebSocket consumers
│   └── routing.py         # WebSocket routing
├── frontend/              # Frontend templates and static files
│   ├── templates/         # HTML templates
│   │   ├── base.html
│   │   ├── novels/
│   │   │   ├── dashboard.html
│   │   │   ├── project_detail.html
│   │   │   └── chapter_detail.html
│   │   └── registration/
│   │       ├── login.html
│   │       └── register.html
│   └── static/            # CSS, JS, PWA files
│       ├── css/mobile.css
│       ├── js/
│       │   ├── api.js
│       │   ├── mobile-ui.js
│       │   └── project.js
│       ├── manifest.json
│       └── sw.js          # Service Worker
├── requirements-web.txt   # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-container orchestration
├── nginx.conf             # Nginx reverse proxy config
└── .env.example           # Environment variables template
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (returns token)
- `POST /api/auth/logout/` - Logout

### Projects
- `GET /api/projects/` - List user's projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}/` - Get project details
- `PUT /api/projects/{id}/` - Update project
- `DELETE /api/projects/{id}/` - Delete project

### AI Operations (All return task_id for tracking)
- `POST /api/projects/{id}/brainstorm/` - Generate plot ideas
- `POST /api/projects/{id}/create_plot/` - Create plot structure
- `POST /api/projects/{id}/create_characters/` - Generate characters
- `POST /api/projects/{id}/create_setting/` - Create world setting
- `POST /api/projects/{id}/create_outline/` - Generate chapter outline
- `POST /api/projects/{id}/score/` - Score complete novel

### Chapters
- `GET /api/projects/{id}/chapters/` - List chapters
- `POST /api/chapters/` - Create chapter
- `GET /api/chapters/{id}/` - Get chapter
- `PUT /api/chapters/{id}/` - Update chapter
- `POST /api/chapters/{id}/write/` - AI write chapter
- `POST /api/chapters/{id}/edit/` - AI edit suggestions
- `POST /api/chapters/{id}/check_consistency/` - Check consistency

### Tasks
- `GET /api/tasks/{id}/` - Get task status and progress

### WebSocket
- `ws://localhost:8000/ws/generate/{task_id}/` - Real-time progress updates

## Mobile Features

### Progressive Web App (PWA)
The application can be installed on mobile devices:
1. Open in mobile browser
2. Tap "Add to Home Screen" (iOS) or "Install" (Android)
3. Use like a native app

### Touch Gestures
- **Swipe right from left edge**: Open menu
- **Swipe left on open menu**: Close menu
- **Pull down at top**: Refresh page
- **Double tap**: Zoom in/out (on supported elements)

### Offline Support
- Static files cached for offline use
- Service Worker enables basic offline functionality
- Sync queued when back online

## Configuration

### Environment Variables

See `.env.example` for all available options. Key variables:

```bash
# Required
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key

# Database (production)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=novel_agent_db
DB_USER=novel_user
DB_PASSWORD=secure-password
DB_HOST=db

# Redis
REDIS_URL=redis://redis:6379/0

# Novel Agent Settings
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.7
MAX_TOKENS=2000
```

### Scoring Weights

Customize scoring categories in `.env`:
```bash
SCORING_STORY_PLOT_WEIGHT=30
SCORING_CHARACTER_DEV_WEIGHT=20
SCORING_WORLD_BUILDING_WEIGHT=15
SCORING_WRITING_STYLE_WEIGHT=20
SCORING_DIALOGUE_WEIGHT=10
SCORING_EMOTIONAL_IMPACT_WEIGHT=5
# Must sum to 100
```

## Troubleshooting

### Complete Cleanup and Fresh Start

If you're experiencing persistent issues and want to start completely fresh:

```bash
cd novel_web

# Complete cleanup - removes all Docker volumes (database, redis, media)
docker compose down -v

# Rebuild and restart
./setup.sh
```

This deletes all data including:
- All PostgreSQL database tables and data
- All Redis cache data
- All uploaded media files (vector stores, exports, etc.)

Use this when:
- Migrations are corrupted or failing
- Database is in an inconsistent state
- Testing from a clean slate
- Troubleshooting persistent configuration issues

### "no such table: novels_novelproject" Error

**Quick Fix:**
```bash
# Run the database fix script
chmod +x fix-database.sh
./fix-database.sh
```

This error means database migrations haven't been run. **Solution:**

**Docker:**
```bash
# Run migrations
docker compose exec web python manage.py migrate

# Verify tables created
docker compose exec web python manage.py showmigrations
```

**Local:**
```bash
python manage.py migrate
```

**Note:** The `entrypoint.sh` automatically runs migrations when Docker containers start. If you see this error:
1. Migrations might have failed during startup
2. Check logs: `docker compose logs web`
3. Or container started before database was ready

**See [BUGFIX_DATABASE.md](BUGFIX_DATABASE.md) for complete guide.**

### "relation does not exist" Error (PostgreSQL)

**Error Example:**
```
ProgrammingError: relation "novels_novelproject" does not exist
```

**Why This Happens:**
- PostgreSQL uses the term "relation" for tables
- After switching from SQLite to PostgreSQL, the new database is empty
- Migrations need to be run to create the tables

**Solution:**
```bash
# Ensure PostgreSQL is running
docker compose up -d db
sleep 10

# Run migrations
docker compose exec web python manage.py migrate --verbosity 2

# Verify tables exist
docker compose exec db psql -U novel_user -d novel_agent_db -c "\dt"

# Test application
curl http://localhost:8000/health/
```

**See [BUGFIX_POSTGRESQL.md](BUGFIX_POSTGRESQL.md) for complete PostgreSQL troubleshooting guide.**

### "curl returns nothing" or Can't Access from Mobile

**Quick Diagnosis:**
```bash
# Run the network test script
chmod +x test-network.sh
./test-network.sh
```

Your server IS working if `curl` returns a redirect (302). The issue is that curl doesn't follow redirects by default:

```bash
# ❌ This returns "nothing" (empty 302 response)
curl http://192.168.86.29:8000

# ✅ This works (follows redirect to login page)
curl -L http://192.168.86.29:8000

# ✅ Or test health endpoint (no redirect)
curl http://192.168.86.29:8000/health/
# Should return: {"status": "healthy", "service": "novel-agent-web"}
```

**Common Solutions:**

1. **Access from browser instead of curl**:
   - Browser: `http://192.168.86.29:8000` → Shows login page ✅
   - curl without -L: Returns empty (but server works!) ⚠️

2. **Add your IP to ALLOWED_HOSTS** (if you see "Bad Request 400"):
   ```bash
   # Edit .env
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,192.168.86.29

   # Restart
   docker compose restart web
   ```

3. **Check firewall** (if connection refused):
   ```bash
   sudo ufw allow 8000/tcp
   ```

**See [NETWORK_TROUBLESHOOTING.md](NETWORK_TROUBLESHOOTING.md) for complete guide.**

### WebSocket Connection Failed
- Check Redis is running: `docker compose ps redis`
- Verify REDIS_URL in settings
- Check browser console for errors

### Celery Tasks Not Processing
- Verify celery worker is running: `docker compose logs celery`
- Check Redis connection
- Ensure OpenAI API key is valid

### Static Files Not Loading
- Run collectstatic: `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL in settings
- In production, ensure nginx is serving static files

### Database Migration Errors
- Check database connection settings
- Ensure database exists: `createdb novel_agent_db`
- Try: `python manage.py migrate --run-syncdb`

### 429 OpenAI API Errors
- You've exceeded your API quota
- Check your OpenAI account billing
- Reduce request frequency in development

## Development

### Running Tests

```bash
python manage.py test novels
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Shell

```bash
python manage.py shell
>>> from novels.models import NovelProject
>>> projects = NovelProject.objects.all()
```

### Celery Monitoring

```bash
# Flower (optional web UI)
pip install flower
celery -A novel_web flower
# Visit http://localhost:5555
```

## Production Deployment

### Security Checklist

1. Set `DEBUG=False` in production
2. Generate strong `SECRET_KEY`
3. Set proper `ALLOWED_HOSTS`
4. Use HTTPS (configure nginx with SSL certificates)
5. Set secure cookie flags:
   ```bash
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```
6. Use PostgreSQL, not SQLite
7. Set strong database passwords
8. Configure firewall rules
9. Enable Sentry for error tracking (optional)
10. Regular backups of database and media files

### Scaling

For high traffic:
- Increase Celery workers: `--concurrency=4`
- Use multiple web containers
- Add load balancer
- Use managed PostgreSQL (RDS, Cloud SQL)
- Use managed Redis (ElastiCache, Memory Store)
- Configure CDN for static files

## License

This project integrates with the Novel Agent CLI application. See main project documentation for licensing details.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs: `docker compose logs`
3. Check Django documentation: https://docs.djangoproject.com/
4. Check Celery documentation: https://docs.celeryq.dev/

## API Rate Limits

Default rate limits (configured in nginx.conf):
- API endpoints: 10 requests/second (burst: 20)
- General endpoints: 30 requests/second (burst: 50)

Adjust in nginx.conf for your needs.
