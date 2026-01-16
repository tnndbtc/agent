#!/bin/bash
# Setup and management script for Novel Writing Agent web interface

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Get local IP address
get_local_ip() {
    hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost"
}

# Main menu
show_menu() {
    clear
    echo "=========================================="
    echo "  Novel Writing Agent - Setup & Management"
    echo "=========================================="
    echo ""
    echo "1)  Initial Setup (Docker)"
    echo "2)  Initial Setup (Local Development)"
    echo "3)  Run Migrations"
    echo "4)  Clean up (Remove and recreate all Docker volumes and data)"
    echo "0)  Exit"
    echo ""
    read -p "Enter choice: " choice
}

# Initial setup - Docker
setup_docker() {
    echo ""
    echo "=================================="
    echo "Docker Setup"
    echo "=================================="
    echo ""

    # Check if .env exists
    if [ ! -f .env ]; then
        log_info "Creating .env file from .env.example..."
        cp .env.example .env
    fi

    # Update .env with environment variables if they are set
    log_info "Checking for environment variables..."

    if [ ! -z "$SECRET_KEY" ]; then
        log_info "Using SECRET_KEY from environment variable"
        if grep -q "^SECRET_KEY=" .env; then
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
        else
            echo "SECRET_KEY=$SECRET_KEY" >> .env
        fi
    else
        log_warn "SECRET_KEY not found in environment. Please edit .env file to set it."
    fi

    if [ ! -z "$DB_USER" ]; then
        log_info "Using DB_USER from environment variable"
        if grep -q "^DB_USER=" .env; then
            sed -i "s|^DB_USER=.*|DB_USER=$DB_USER|" .env
        else
            echo "DB_USER=$DB_USER" >> .env
        fi
    fi

    if [ ! -z "$DB_PASSWORD" ]; then
        log_info "Using DB_PASSWORD from environment variable"
        if grep -q "^DB_PASSWORD=" .env; then
            sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|" .env
        else
            echo "DB_PASSWORD=$DB_PASSWORD" >> .env
        fi
    fi

    if [ ! -z "$ALLOWED_HOSTS" ]; then
        log_info "Using ALLOWED_HOSTS from environment variable"
        if grep -q "^ALLOWED_HOSTS=" .env; then
            sed -i "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$ALLOWED_HOSTS|" .env
        else
            echo "ALLOWED_HOSTS=$ALLOWED_HOSTS" >> .env
        fi
    fi

    if [ -z "$SECRET_KEY" ] || [ -z "$OPENAI_API_KEY" ]; then
        log_warn "IMPORTANT: Edit .env file and add missing configuration"
        [ -z "$OPENAI_API_KEY" ] && log_warn "  - OPENAI_API_KEY is required"
        [ -z "$SECRET_KEY" ] && log_warn "  - SECRET_KEY must be set for production use"
        echo ""
        read -p "Press Enter to continue after editing .env..."
    fi

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed. Please install Docker first."
        return 1
    fi

    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose not installed. Please install Docker Compose first."
        return 1
    fi

    log_info "Building Docker images..."
    docker compose build

    log_info "Starting database services..."
    docker compose up -d db redis

    log_info "Waiting for services to be ready..."
    sleep 10

    log_info "Starting web application..."
    docker compose up -d

    log_info "Waiting for web service to initialize (migrations will run automatically)..."
    sleep 5

    echo ""
    read -p "Create superuser now? (y/n): " create_super
    if [ "$create_super" = "y" ]; then
        set +e  # Temporarily disable exit on error
        docker compose exec web python manage.py createsuperuser
        if [ $? -eq 0 ]; then
            log_info "Superuser created successfully!"
        else
            log_warn "Superuser creation cancelled or failed. You can create one later with:"
            log_warn "  docker compose exec web python manage.py createsuperuser"
        fi
        set -e  # Re-enable exit on error
    fi

    local_ip=$(get_local_ip)

    echo ""
    echo "=================================="
    log_info "Setup complete!"
    echo "=================================="
    echo ""
    echo "Application URLs:"
    echo "  Local:   http://localhost:8000"
    echo "  Network: http://$local_ip:8000"
    echo "  Admin:   http://localhost:8000/admin/"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker compose logs -f"
    echo "  Stop:         docker compose down"
    echo "  Restart:      docker compose restart"
    echo ""
}

# Initial setup - Local
setup_local() {
    echo ""
    echo "=================================="
    echo "Local Development Setup"
    echo "=================================="
    echo ""

    # Check if .env exists
    if [ ! -f .env ]; then
        log_info "Creating .env file from .env.example..."
        cp .env.example .env
        log_warn "IMPORTANT: Edit .env file and add your OPENAI_API_KEY"
        echo ""
        read -p "Press Enter to continue after editing .env..."
    fi

    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python version: $python_version"

    # Check if virtualenv exists
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi

    log_info "Activating virtual environment..."
    source venv/bin/activate

    log_info "Installing dependencies..."
    pip install --upgrade pip

    log_info "Installing novel_agent package..."
    pip install -e ../

    log_info "Installing web application dependencies..."
    pip install -r requirements-web.txt

    log_info "Creating migration files..."
    python manage.py makemigrations || log_warn "No new migrations to create"

    log_info "Running migrations..."
    python manage.py migrate

    log_info "Collecting static files..."
    python manage.py collectstatic --noinput

    echo ""
    read -p "Create superuser now? (y/n): " create_super
    if [ "$create_super" = "y" ]; then
        set +e  # Temporarily disable exit on error
        python manage.py createsuperuser
        if [ $? -eq 0 ]; then
            log_info "Superuser created successfully!"
        else
            log_warn "Superuser creation cancelled or failed. You can create one later with:"
            log_warn "  python manage.py createsuperuser"
        fi
        set -e  # Re-enable exit on error
    fi

    echo ""
    echo "=================================="
    log_info "Setup complete!"
    echo "=================================="
    echo ""
    echo "To start the application:"
    echo ""
    echo "Terminal 1 - Django:"
    echo "  source venv/bin/activate"
    echo "  python manage.py runserver 0.0.0.0:8000"
    echo ""
    echo "Terminal 2 - Celery Worker:"
    echo "  source venv/bin/activate"
    echo "  celery -A novel_web worker -l info"
    echo ""
    log_warn "Make sure PostgreSQL and Redis are running!"
    echo ""
}

# Run migrations with database diagnosis and error fixing
run_migrations() {
    echo ""
    echo "=================================="
    echo "Running Migrations"
    echo "=================================="
    echo ""

    # Determine which setup is being used
    if command -v docker &> /dev/null && [ -f "docker-compose.yml" ] && docker compose ps web 2>/dev/null | grep -q "Up"; then
        log_info "Using Docker setup..."

        # Diagnose database
        echo ""
        log_info "Step 1: Diagnosing database..."
        echo ""

        log_info "Container status:"
        docker compose ps

        echo ""
        log_info "Database configuration:"
        docker compose exec web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print('  Engine:', db['ENGINE'])
print('  Name:', db['NAME'])
print('  User:', db.get('USER', 'N/A'))
print('  Host:', db.get('HOST', 'N/A'))
" 2>&1

        echo ""
        log_info "Current migration status:"
        docker compose exec web python manage.py showmigrations 2>&1 | head -30

        # Check and fix database issues
        echo ""
        log_info "Step 2: Checking for database issues..."

        set +e  # Temporarily disable exit on error
        docker compose exec web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from novels.models import NovelProject
print('✓ NovelProject model accessible')
" 2>/dev/null

        if [ $? -ne 0 ]; then
            log_warn "Database issues detected. Attempting to fix..."
            echo ""

            log_info "Creating migration files..."
            docker compose exec web python manage.py makemigrations

            log_info "Applying migrations..."
            docker compose exec web python manage.py migrate --verbosity 2

            log_info "Verifying fix..."
            docker compose exec web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from novels.models import NovelProject
print('✓ NovelProject model accessible')
print('✓ Database tables exist')
" && log_info "Database issues resolved!" || log_error "Database issues persist. Please check configuration."
        else
            log_info "No database issues detected."

            log_info "Creating migration files (if any)..."
            docker compose exec web python manage.py makemigrations || log_warn "No new migrations to create"

            log_info "Running migrations..."
            docker compose exec web python manage.py migrate --verbosity 2
        fi
        set -e  # Re-enable exit on error

        echo ""
        log_info "Step 3: Final migration status:"
        docker compose exec web python manage.py showmigrations | head -20

        echo ""
        log_info "Database tables:"
        docker compose exec web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from django.db import connection
from django.conf import settings
cursor = connection.cursor()
if 'sqlite' in settings.DATABASES['default']['ENGINE']:
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
else:
    cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';\")
tables = cursor.fetchall()
print(f'Total tables: {len(tables)}')
for table in tables[:10]:
    print('  -', table[0])
if len(tables) > 10:
    print(f'  ... and {len(tables) - 10} more tables')
" 2>&1

    elif [ -d "venv" ]; then
        log_info "Using local setup..."
        source venv/bin/activate

        # Diagnose database
        echo ""
        log_info "Step 1: Diagnosing database..."
        echo ""

        log_info "Database configuration:"
        python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print('  Engine:', db['ENGINE'])
print('  Name:', db['NAME'])
print('  User:', db.get('USER', 'N/A'))
print('  Host:', db.get('HOST', 'N/A'))
" 2>&1

        echo ""
        log_info "Current migration status:"
        python manage.py showmigrations 2>&1 | head -30

        # Check and fix database issues
        echo ""
        log_info "Step 2: Checking for database issues..."

        set +e  # Temporarily disable exit on error
        python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from novels.models import NovelProject
print('✓ NovelProject model accessible')
" 2>/dev/null

        if [ $? -ne 0 ]; then
            log_warn "Database issues detected. Attempting to fix..."
            echo ""

            log_info "Creating migration files..."
            python manage.py makemigrations

            log_info "Applying migrations..."
            python manage.py migrate --verbosity 2

            log_info "Verifying fix..."
            python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from novels.models import NovelProject
print('✓ NovelProject model accessible')
print('✓ Database tables exist')
" && log_info "Database issues resolved!" || log_error "Database issues persist. Please check configuration."
        else
            log_info "No database issues detected."

            log_info "Creating migration files (if any)..."
            python manage.py makemigrations || log_warn "No new migrations to create"

            log_info "Running migrations..."
            python manage.py migrate --verbosity 2
        fi
        set -e  # Re-enable exit on error

        echo ""
        log_info "Step 3: Final migration status:"
        python manage.py showmigrations | head -20

    else
        log_error "No setup found. Run initial setup first (option 1 or 2)."
        return 1
    fi

    echo ""
    echo "=================================="
    log_info "Migrations completed successfully!"
    echo "=================================="
}

# Clean up - Remove all Docker volumes and data
cleanup_docker() {
    echo ""
    echo "=================================="
    echo "Clean Up Docker Environment"
    echo "=================================="
    echo ""

    log_warn "WARNING: This will completely remove all data including:"
    log_warn "  - All database tables and data"
    log_warn "  - All Redis cache data"
    log_warn "  - All Docker volumes"
    log_warn "  - All Docker containers"
    echo ""

    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Clean up cancelled."
        return 0
    fi

    echo ""
    read -p "Type 'DELETE ALL DATA' to confirm: " final_confirm

    if [ "$final_confirm" != "DELETE ALL DATA" ]; then
        log_info "Clean up cancelled."
        return 0
    fi

    echo ""
    log_info "Stopping and removing all containers and volumes..."

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed."
        return 1
    fi

    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose not installed."
        return 1
    fi

    # Run docker compose down with volume removal
    docker compose down -v

    echo ""
    log_info "All containers, networks, and volumes have been removed."
    echo ""

    log_info "Recreating containers..."
    docker compose up -d

    log_info "Waiting for services to be ready..."
    sleep 10

    echo ""
    log_info "Clean up and recreation completed!"
    echo ""
    log_info "New containers have been created with fresh databases."
    log_info "You may need to run migrations (option 3) and create a superuser."
    echo ""
}

# Main loop
while true; do
    show_menu
    case $choice in
        1) setup_docker; read -p "Press Enter to continue..." ;;
        2) setup_local; read -p "Press Enter to continue..." ;;
        3) run_migrations; read -p "Press Enter to continue..." ;;
        4) cleanup_docker; read -p "Press Enter to continue..." ;;
        0) echo "Exiting..."; exit 0 ;;
        *) log_error "Invalid choice. Try again."; read -p "Press Enter to continue..." ;;
    esac
done
