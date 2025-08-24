# Voice Log - Makefile
.PHONY: help build up down restart logs shell clean status init-db native-init native-run install-deps

# Variables
IMAGE_NAME := voice-log
CONTAINER_NAME := voice-log-app

# Default target
help: ## Show this help message
	@echo "Voice Log - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make build          # Build the Docker image"
	@echo "  make up             # Start the application"
	@echo "  make logs           # View application logs"
	@echo "  make native-init    # Set up native development environment"

## Docker Management
build: ## Build Docker image
	@echo "Building Voice Log Docker image..."
	docker build -t $(IMAGE_NAME) .

up: ## Start application with Docker Compose
	@echo "Starting Voice Log application..."
	docker-compose up -d
	@echo "Application started. Visit http://localhost:5010"

down: ## Stop and remove containers
	@echo "Stopping Voice Log application..."
	docker-compose down

restart: ## Restart the application
	@echo "Restarting Voice Log application..."
	docker-compose restart

logs: ## Show application logs
	@echo "Showing Voice Log logs (Ctrl+C to exit)..."
	docker-compose logs -f

shell: ## Open shell in running container
	@echo "Opening shell in Voice Log container..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

clean: ## Remove containers and images
	@echo "Cleaning up Voice Log containers and images..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

status: ## Show container status
	@echo "Voice Log container status:"
	@docker-compose ps
	@echo ""
	@echo "Docker images:"
	@docker images | grep $(IMAGE_NAME) || echo "No Voice Log images found"

## Database Operations
init-db: ## Initialize database with tables and sample data
	@echo "Initializing Voice Log database..."
	@if [ -f "data/voice_log.db" ]; then \
		echo "Database already exists. Use 'make backup' before reinitializing."; \
		read -p "Continue anyway? [y/N] " -n 1 -r; \
		echo; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then exit 1; fi; \
	fi
	@mkdir -p data uploads logs cache backups
	@if command -v docker >/dev/null 2>&1 && docker-compose ps | grep -q "$(CONTAINER_NAME)"; then \
		docker exec $(CONTAINER_NAME) python -c "from app.services.database import init_database; init_database('data/voice_log.db')"; \
	else \
		python -c "from app.services.database import init_database; init_database('data/voice_log.db')"; \
	fi
	@echo "Database initialized successfully!"

backup: ## Create application backup
	@echo "Creating Voice Log backup..."
	@mkdir -p backups
	@DATE=$$(date +%Y%m%d_%H%M%S); \
	tar -czf backups/voice_log_backup_$$DATE.tar.gz data/ uploads/ || true
	@echo "Backup created in backups/ directory"

## Native Development
native-init: ## Set up native development environment
	@echo "Setting up native Voice Log development environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv || python3.10 -m venv venv || python3.9 -m venv venv || python3 -m venv venv; \
	fi
	@echo "Activating virtual environment and installing dependencies..."
	@. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "Creating directories..."
	@mkdir -p data uploads logs cache backups static/icons
	@echo "Copying environment file..."
	@if [ ! -f ".env" ]; then cp .env.example .env; fi
	@echo ""
	@echo "✅ Native development environment set up!"
	@echo "Next steps:"
	@echo "  1. Activate the virtual environment: source venv/bin/activate"
	@echo "  2. Edit .env file with your configuration"
	@echo "  3. Initialize database: make init-db"
	@echo "  4. Run the application: make native-run"

native-run: ## Run application natively (requires native-init)
	@echo "Starting Voice Log natively..."
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make native-init' first."; \
		exit 1; \
	fi
	@if [ ! -f "data/voice_log.db" ]; then \
		echo "⚠️  Database not found. Initializing..."; \
		$(MAKE) init-db; \
	fi
	@echo "Starting development server..."
	@. venv/bin/activate && python voice_log.py

install-deps: ## Install additional dependencies
	@echo "Installing additional dependencies..."
	@if command -v docker >/dev/null 2>&1 && docker-compose ps | grep -q "$(CONTAINER_NAME)"; then \
		echo "Installing in Docker container..."; \
		docker exec $(CONTAINER_NAME) pip install $(DEPS); \
	else \
		echo "Installing in native environment..."; \
		if [ -d "venv" ]; then \
			. venv/bin/activate && pip install $(DEPS); \
		else \
			pip install $(DEPS); \
		fi; \
	fi

## Configuration
config-check: ## Check configuration and requirements
	@echo "Checking Voice Log configuration..."
	@echo "Python version: $$(python3 --version)"
	@echo "Docker version: $$(docker --version 2>/dev/null || echo 'Docker not installed')"
	@echo "Docker Compose version: $$(docker-compose --version 2>/dev/null || echo 'Docker Compose not installed')"
	@echo ""
	@if [ -f ".env" ]; then \
		echo "✅ Environment file exists"; \
	else \
		echo "⚠️  Environment file not found. Copy .env.example to .env"; \
	fi
	@if [ -f "data/voice_log.db" ]; then \
		echo "✅ Database exists"; \
	else \
		echo "⚠️  Database not found. Run 'make init-db'"; \
	fi
	@if [ -d "uploads" ]; then \
		echo "✅ Upload directory exists"; \
	else \
		echo "⚠️  Upload directory not found. Run 'mkdir uploads'"; \
	fi

## Development Helpers
dev: ## Quick start for development (build + up + logs)
	@echo "Starting Voice Log development environment..."
	@$(MAKE) build
	@$(MAKE) up
	@sleep 3
	@$(MAKE) logs

reset: ## Reset everything (clean + build + up)
	@echo "Resetting Voice Log environment..."
	@$(MAKE) down
	@$(MAKE) clean
	@$(MAKE) build
	@$(MAKE) up
	@echo "Environment reset complete!"

test: ## Run tests (if available)
	@echo "Running Voice Log tests..."
	@if [ -d "tests" ]; then \
		if [ -d "venv" ]; then \
			. venv/bin/activate && python -m pytest tests/; \
		else \
			python -m pytest tests/; \
		fi; \
	else \
		echo "No tests directory found"; \
	fi

## Quick Actions
quick-backup: backup ## Alias for backup
quick-clean: clean ## Alias for clean
quick-status: status ## Alias for status

# Health check
health: ## Check application health
	@echo "Checking Voice Log health..."
	@if command -v curl >/dev/null 2>&1; then \
		curl -f http://localhost:5010/api/stats >/dev/null 2>&1 && \
		echo "✅ Application is healthy" || \
		echo "❌ Application is not responding"; \
	else \
		echo "curl not available for health check"; \
	fi