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
    echo "1)  Setup Docker (Build and start containers)"
    echo "2)  Setup Local Development"
    echo "3)  Create Superuser"
    echo "4)  Run Migrations and Seed System Data"
    echo "5)  Clean up (Remove and recreate all Docker volumes and data)"
    echo "6)  Dump Database (Backup to file)"
    echo "7)  Restore Database (Restore from dump file)"
    echo "0)  Exit"
    echo ""
    read -p "Enter choice: " choice
}

# Setup Docker - Build and start containers only
setup_docker() {
    echo ""
    echo "=================================="
    echo "Docker Setup - Build and Start Containers"
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

    log_info "Starting all services..."
    docker compose up -d

    log_info "Waiting for services to be ready..."
    sleep 10

    local_ip=$(get_local_ip)

    echo ""
    echo "=================================="
    log_info "Docker setup complete!"
    echo "=================================="
    echo ""
    echo "Application URLs:"
    echo "  Local:   http://localhost:8000"
    echo "  Network: http://$local_ip:8000"
    echo "  Admin:   http://localhost:8000/admin/"
    echo ""
    log_warn "Next steps:"
    log_warn "  - Run option 4 to apply migrations and seed system data"
    log_warn "  - Run option 3 to create a superuser account"
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

# Create Superuser - Create Django admin superuser account
create_superuser() {
    echo ""
    echo "=================================="
    echo "Create Superuser"
    echo "=================================="
    echo ""

    # Determine which setup is being used
    if command -v docker &> /dev/null && [ -f "docker-compose.yml" ] && docker compose ps web 2>/dev/null | grep -q "Up"; then
        log_info "Using Docker setup..."

        set +e  # Temporarily disable exit on error
        docker compose exec web python manage.py createsuperuser
        if [ $? -eq 0 ]; then
            log_info "Superuser created successfully!"
        else
            log_warn "Superuser creation cancelled or failed."
        fi
        set -e  # Re-enable exit on error

    elif [ -d "venv" ]; then
        log_info "Using local setup..."
        source venv/bin/activate

        set +e  # Temporarily disable exit on error
        python manage.py createsuperuser
        if [ $? -eq 0 ]; then
            log_info "Superuser created successfully!"
        else
            log_warn "Superuser creation cancelled or failed."
        fi
        set -e  # Re-enable exit on error

    else
        log_error "No setup found. Please run option 1 (Docker) or 2 (Local) first."
        return 1
    fi

    echo ""
    echo "=================================="
    log_info "Superuser creation complete!"
    echo "=================================="
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
        log_info "Seeding system data (writing styles, techniques, policies, agent roles)..."
        docker compose exec web python manage.py seed_prompt_architecture || log_warn "Seeding completed or already done"

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
        log_info "Seeding system data (writing styles, techniques, policies, agent roles)..."
        python manage.py seed_prompt_architecture || log_warn "Seeding completed or already done"

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
    log_info "Run option 4 to apply migrations and seed data, then option 3 to create a superuser."
    echo ""
}

# Dump Database - Backup all database contents to a file
dump_database() {
    echo ""
    echo "=================================="
    echo "Dump Database (Backup)"
    echo "=================================="
    echo ""

    # Generate filename with timestamp
    timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    dump_file="dump_${timestamp}.sql"

    # Determine which setup is being used
    if command -v docker &> /dev/null && [ -f "docker-compose.yml" ] && docker compose ps db 2>/dev/null | grep -q "Up"; then
        log_info "Using Docker setup..."

        # Get database credentials from .env
        if [ -f .env ]; then
            source .env
        else
            log_error ".env file not found"
            return 1
        fi

        log_info "Dumping database to: $dump_file"

        # Use pg_dump through docker
        docker compose exec -T db pg_dump -U "${DB_USER:-novel_user}" "${DB_NAME:-novel_agent_db}" > "$dump_file"

        if [ $? -eq 0 ]; then
            file_size=$(du -h "$dump_file" | cut -f1)
            log_info "Database dump completed successfully!"
            echo ""
            echo "  File: $dump_file"
            echo "  Size: $file_size"
            echo ""
            log_info "To restore this dump, use option 7 and provide the filename."
        else
            log_error "Database dump failed!"
            rm -f "$dump_file"
            return 1
        fi

    elif [ -d "venv" ]; then
        log_info "Using local setup..."

        # Check if PostgreSQL is being used
        python_check=$(python3 -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print(db['ENGINE'])
print(db.get('NAME', ''))
print(db.get('USER', ''))
print(db.get('PASSWORD', ''))
print(db.get('HOST', 'localhost'))
print(db.get('PORT', '5432'))
" 2>/dev/null)

        if [ $? -ne 0 ]; then
            log_error "Failed to read database configuration"
            return 1
        fi

        db_engine=$(echo "$python_check" | sed -n '1p')
        db_name=$(echo "$python_check" | sed -n '2p')
        db_user=$(echo "$python_check" | sed -n '3p')
        db_password=$(echo "$python_check" | sed -n '4p')
        db_host=$(echo "$python_check" | sed -n '5p')
        db_port=$(echo "$python_check" | sed -n '6p')

        if [[ "$db_engine" == *"postgresql"* ]]; then
            log_info "Dumping PostgreSQL database to: $dump_file"

            PGPASSWORD="$db_password" pg_dump -h "$db_host" -p "$db_port" -U "$db_user" "$db_name" > "$dump_file"

            if [ $? -eq 0 ]; then
                file_size=$(du -h "$dump_file" | cut -f1)
                log_info "Database dump completed successfully!"
                echo ""
                echo "  File: $dump_file"
                echo "  Size: $file_size"
                echo ""
                log_info "To restore this dump, use option 7 and provide the filename."
            else
                log_error "Database dump failed!"
                rm -f "$dump_file"
                return 1
            fi
        else
            log_error "Only PostgreSQL databases are supported for dump/restore"
            log_error "Current engine: $db_engine"
            return 1
        fi

    else
        log_error "No setup found. Please run option 1 (Docker) or 2 (Local) first."
        return 1
    fi

    echo ""
}

# Restore Database - Restore database from a dump file
restore_database() {
    echo ""
    echo "=================================="
    echo "Restore Database from Dump"
    echo "=================================="
    echo ""

    # List available dump files
    dump_files=(dump_*.sql)

    if [ ${#dump_files[@]} -eq 0 ] || [ ! -f "${dump_files[0]}" ]; then
        log_error "No dump files found in current directory."
        log_info "Dump files should be named: dump_*.sql"
        return 1
    fi

    echo "Available dump files:"
    echo ""
    for i in "${!dump_files[@]}"; do
        file_size=$(du -h "${dump_files[$i]}" | cut -f1)
        echo "  $((i+1))) ${dump_files[$i]} ($file_size)"
    done
    echo ""

    read -p "Enter the number of the dump file to restore (or 0 to cancel): " file_choice

    if [ "$file_choice" = "0" ] || [ -z "$file_choice" ]; then
        log_info "Restore cancelled."
        return 0
    fi

    # Validate choice
    if ! [[ "$file_choice" =~ ^[0-9]+$ ]] || [ "$file_choice" -lt 1 ] || [ "$file_choice" -gt ${#dump_files[@]} ]; then
        log_error "Invalid choice."
        return 1
    fi

    selected_file="${dump_files[$((file_choice-1))]}"

    echo ""
    log_warn "WARNING: This will REPLACE all current database data with the dump file:"
    log_warn "  File: $selected_file"
    echo ""

    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled."
        return 0
    fi

    # Determine which setup is being used
    if command -v docker &> /dev/null && [ -f "docker-compose.yml" ] && docker compose ps db 2>/dev/null | grep -q "Up"; then
        log_info "Using Docker setup..."

        # Get database credentials from .env
        if [ -f .env ]; then
            source .env
        else
            log_error ".env file not found"
            return 1
        fi

        log_info "Dropping existing database..."
        docker compose exec -T db psql -U "${DB_USER:-novel_user}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME:-novel_agent_db};" 2>/dev/null

        log_info "Creating new database..."
        docker compose exec -T db psql -U "${DB_USER:-novel_user}" -d postgres -c "CREATE DATABASE ${DB_NAME:-novel_agent_db};" 2>/dev/null

        log_info "Restoring database from: $selected_file"
        cat "$selected_file" | docker compose exec -T db psql -U "${DB_USER:-novel_user}" "${DB_NAME:-novel_agent_db}" > /dev/null 2>&1

        if [ $? -eq 0 ]; then
            log_info "Database restore completed successfully!"
            echo ""
            log_info "You may need to restart the web container:"
            log_info "  docker compose restart web"
        else
            log_error "Database restore failed!"
            return 1
        fi

    elif [ -d "venv" ]; then
        log_info "Using local setup..."

        # Check if PostgreSQL is being used
        python_check=$(python3 -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_web.settings')
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print(db['ENGINE'])
print(db.get('NAME', ''))
print(db.get('USER', ''))
print(db.get('PASSWORD', ''))
print(db.get('HOST', 'localhost'))
print(db.get('PORT', '5432'))
" 2>/dev/null)

        if [ $? -ne 0 ]; then
            log_error "Failed to read database configuration"
            return 1
        fi

        db_engine=$(echo "$python_check" | sed -n '1p')
        db_name=$(echo "$python_check" | sed -n '2p')
        db_user=$(echo "$python_check" | sed -n '3p')
        db_password=$(echo "$python_check" | sed -n '4p')
        db_host=$(echo "$python_check" | sed -n '5p')
        db_port=$(echo "$python_check" | sed -n '6p')

        if [[ "$db_engine" == *"postgresql"* ]]; then
            log_info "Dropping existing database..."
            PGPASSWORD="$db_password" psql -h "$db_host" -p "$db_port" -U "$db_user" -d postgres -c "DROP DATABASE IF EXISTS $db_name;" 2>/dev/null

            log_info "Creating new database..."
            PGPASSWORD="$db_password" psql -h "$db_host" -p "$db_port" -U "$db_user" -d postgres -c "CREATE DATABASE $db_name;" 2>/dev/null

            log_info "Restoring database from: $selected_file"
            PGPASSWORD="$db_password" psql -h "$db_host" -p "$db_port" -U "$db_user" "$db_name" < "$selected_file" > /dev/null 2>&1

            if [ $? -eq 0 ]; then
                log_info "Database restore completed successfully!"
                echo ""
                log_info "You may need to restart your Django server."
            else
                log_error "Database restore failed!"
                return 1
            fi
        else
            log_error "Only PostgreSQL databases are supported for dump/restore"
            log_error "Current engine: $db_engine"
            return 1
        fi

    else
        log_error "No setup found. Please run option 1 (Docker) or 2 (Local) first."
        return 1
    fi

    echo ""
}

# Main loop
while true; do
    show_menu
    case $choice in
        1) setup_docker; read -p "Press Enter to continue..." ;;
        2) setup_local; read -p "Press Enter to continue..." ;;
        3) create_superuser; read -p "Press Enter to continue..." ;;
        4) run_migrations; read -p "Press Enter to continue..." ;;
        5) cleanup_docker; read -p "Press Enter to continue..." ;;
        6) dump_database; read -p "Press Enter to continue..." ;;
        7) restore_database; read -p "Press Enter to continue..." ;;
        0) echo "Exiting..."; exit 0 ;;
        *) log_error "Invalid choice. Try again."; read -p "Press Enter to continue..." ;;
    esac
done
