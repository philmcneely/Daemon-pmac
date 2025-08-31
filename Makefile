.PHONY: help install dev test lint format clean docker-build docker-run backup restore

# Default target
help:
	@echo "Daemon Development Commands"
	@echo "================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install     Install dependencies"
	@echo "  dev         Start development server"
	@echo "  setup-pi    Run Raspberry Pi setup script"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test        Run all tests"
	@echo "  lint        Run code linting"
	@echo "  format      Format code with black and isort"
	@echo "  typecheck   Run type checking with mypy"
	@echo ""
	@echo "Database:"
	@echo "  db-init     Initialize database"
	@echo "  db-reset    Reset database (WARNING: deletes all data)"
	@echo "  backup      Create database backup"
	@echo "  restore     Restore from backup"
	@echo ""
	@echo "Resume:"
	@echo "  check-resume   Check resume file status"
	@echo "  import-resume  Import resume from file"
	@echo "  show-resume    Show current resume data"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"
	@echo "  docker-stop  Stop Docker containers"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       Clean temporary files"
	@echo "  logs        View application logs"
	@echo "  status      Show system status"

# Installation and setup
install:
	pip install -r requirements.txt
	python -m app.cli db init

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black isort flake8 mypy pre-commit

dev:
	python dev.py

setup-pi:
	chmod +x setup-pi.sh
	./setup-pi.sh

# Testing and quality
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

format:
	black app/ tests/
	isort app/ tests/

typecheck:
	mypy app/

# Database operations
db-init:
	python -m app.cli db init

db-reset:
	python -m app.cli db reset

backup:
	python -m app.cli backup create

restore:
	@echo "Available backups:"
	@python -m app.cli backup list
	@echo ""
	@read -p "Enter backup filename: " backup_file; \
	python -m app.cli backup restore $$backup_file

# Resume management
check-resume:
	python -m app.cli resume check

import-resume:
	python -m app.cli resume import-file --replace

show-resume:
	python -m app.cli resume show

# User management
create-user:
	@read -p "Username: " username; \
	read -p "Email: " email; \
	read -s -p "Password: " password; echo; \
	read -p "Make admin? (y/N): " admin; \
	if [ "$$admin" = "y" ] || [ "$$admin" = "Y" ]; then \
		python -m app.cli user create $$username $$email --password=$$password --admin; \
	else \
		python -m app.cli user create $$username $$email --password=$$password; \
	fi

list-users:
	python -m app.cli user list

# Endpoint management
create-endpoint:
	@read -p "Endpoint name: " name; \
	read -p "Description: " desc; \
	python -m app.cli endpoint create "$$name" "$$desc"

list-endpoints:
	python -m app.cli endpoint list

# Docker operations
docker-build:
	docker build -t daemon-pmac .

docker-run:
	docker-compose up -d

docker-run-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Production deployment
deploy-systemd:
	sudo cp daemon-pmac.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable daemon-pmac
	sudo systemctl start daemon-pmac

setup-ssl:
	chmod +x setup-ssl.sh
	./setup-ssl.sh

# Monitoring and logs
logs:
	journalctl -u daemon-pmac -f

status:
	python -m app.cli status

health:
	curl -f http://localhost:8000/health | python -m json.tool

# Data operations
export-data:
	@read -p "Endpoint name: " endpoint; \
	read -p "Format (json/csv): " format; \
	read -p "Output file (optional): " output; \
	if [ -n "$$output" ]; then \
		python -m app.cli data export $$endpoint --format=$$format --output=$$output; \
	else \
		python -m app.cli data export $$endpoint --format=$$format; \
	fi

import-data:
	@read -p "Endpoint name: " endpoint; \
	read -p "Input file: " input; \
	read -p "Format (json/csv): " format; \
	python -m app.cli data import-data $$endpoint $$input --format=$$format

# Security
generate-secret:
	python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Development utilities
serve-docs:
	@echo "Starting documentation server at http://localhost:8000/docs"
	python -m http.server 8080 --directory docs/ &

api-test:
	@echo "Testing API endpoints..."
	curl -f http://localhost:8000/health
	@echo "\n✓ Health check passed"
	curl -f http://localhost:8000/api/v1/endpoints
	@echo "\n✓ Endpoints accessible"

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf build/
	rm -rf dist/

clean-db:
	rm -f daemon.db*
	rm -rf backups/*.db

# Release preparation
check-release:
	python -m pytest
	python -m flake8 app/
	python -m black --check app/
	python -m mypy app/
	@echo "✓ All checks passed - ready for release"

# Performance testing
load-test:
	@echo "Running basic load test..."
	@command -v ab >/dev/null 2>&1 || { echo "apache2-utils required for load testing"; exit 1; }
	ab -n 1000 -c 10 http://localhost:8000/health

# Raspberry Pi specific
pi-status:
	@echo "=== Raspberry Pi System Status ==="
	@echo "Temperature: $$(vcgencmd measure_temp)"
	@echo "Memory: $$(free -h | grep Mem)"
	@echo "Disk: $$(df -h / | tail -1)"
	@echo "Uptime: $$(uptime)"
	@echo ""
	@echo "=== Service Status ==="
	systemctl status daemon-pmac --no-pager -l

pi-optimize:
	@echo "Optimizing for Raspberry Pi..."
	sudo apt-get update
	sudo apt-get upgrade -y
	sudo apt-get autoremove -y
	sudo apt-get autoclean
	@echo "✓ System optimized"

# Development workflow shortcuts
quick-test:
	pytest tests/test_api.py -v

full-check: format lint typecheck test
	@echo "✓ Full quality check completed"

reset-dev: clean db-reset
	python -m app.cli db init
	@echo "✓ Development environment reset"
