FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.development
ENV POSTGRES_HOST=db

# Set work directory
WORKDIR /app

# Install dependencies (cached layer — only re-runs when requirements.txt changes)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Create a non-root user
RUN groupadd -r django && useradd -r -g django django

# Change ownership of the app directory
RUN chown -R django:django /app

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Default command
CMD ["./entrypoint.sh"]
