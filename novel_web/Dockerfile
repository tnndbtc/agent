# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Copy and install novel_agent package from parent directory
# Build context is now parent directory, so paths are relative to that
COPY novel_agent /tmp/novel_agent
COPY requirements.txt /tmp/novel_agent_requirements.txt
COPY setup.py /tmp/setup.py
WORKDIR /tmp
RUN pip install --upgrade pip && \
    pip install -e .

# Install web application dependencies
WORKDIR /app
COPY novel_web/requirements-web.txt /app/
RUN pip install -r requirements-web.txt

# Copy entrypoint script
COPY novel_web/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Copy project files
COPY novel_web /app/

# Create necessary directories
RUN mkdir -p /app/media/vector_stores /app/staticfiles

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /tmp/novel_agent
USER appuser

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/', timeout=5)"

# Default command (can be overridden in docker-compose)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "novel_web.asgi:application"]
