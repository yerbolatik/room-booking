# Makefile for Hotel Room Booking Project
.PHONY: help build up down logs shell migrate superuser test clean restart

# Default target
help:
	@echo "Available commands:"
	@echo "  build      - Build Docker images"
	@echo "  up         - Start all services"
	@echo "  down       - Stop all services"
	@echo "  logs       - Show logs for all services"
	@echo "  shell      - Open shell in web container"
	@echo "  migrate    - Run database migrations"
	@echo "  superuser  - Create superuser"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean up containers and volumes"
	@echo "  restart    - Restart all services"

# Build Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Show logs
logs:
	docker-compose logs -f

# Show log sizes
log-sizes:
	docker system df
	docker volume ls
	@echo "Container log sizes:"
	@docker ps -q | xargs -I {} sh -c 'echo "Container {}: $(docker inspect {} --format="{{.LogPath}}" | xargs ls -lh 2>/dev/null || echo "No logs")"'

# Clean logs manually
clean-logs-manual:
	docker-compose down
	docker container prune -f
	docker image prune -f
	docker volume prune -f
	docker network prune -f
	docker system prune -f
	docker-compose up -d

# Open shell in web container
shell:
	docker-compose exec web bash

# Run database migrations
migrate:
	docker-compose exec web python manage.py migrate

# Create superuser
superuser:
	docker-compose exec web python manage.py createsuperuser

# Run tests
test:
	docker-compose exec web python -m pytest

# Clean up containers and volumes
clean:
	docker-compose down -v --rmi all
	docker system prune -f

# Clean logs and restart
clean-logs:
	./scripts/clean-logs.sh

# Restart all services
restart:
	docker-compose restart

# Restart with log cleanup
restart-clean:
	docker-compose down
	docker system prune -f
	docker-compose up -d

# Start specific service
up-web:
	docker-compose up -d web

up-celery:
	docker-compose up -d celery

up-celery-beat:
	docker-compose up -d celery-beat

# Database operations
db-shell:
	docker-compose exec db psql -U postgres -d room_booking_dev

db-reset:
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	docker-compose exec web python manage.py migrate
	docker-compose exec web python manage.py createsuperuser

# Redis operations
redis-cli:
	docker-compose exec redis redis-cli

# Development helpers
dev-up:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

dev-logs:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Production helpers
prod-build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitoring
monitor:
	docker-compose exec web celery -A config flower

# Backup and restore
backup:
	docker-compose exec db pg_dump -U postgres room_booking_dev > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore:
	@echo "Usage: make restore FILE=backup_file.sql"
	@if [ -z "$(FILE)" ]; then echo "Please specify FILE parameter"; exit 1; fi
	docker-compose exec -T db psql -U postgres room_booking_dev < $(FILE)
