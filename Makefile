.PHONY: help test test-cov test-watch lint format clean install dev db-up db-down

help:
@echo "Mew Assistant - Development Commands"
@echo "====================================="
@echo "make install      - Install dependencies"
@echo "make dev          - Run development server"
@echo "make test         - Run tests"
@echo "make test-cov     - Run tests with coverage"
@echo "make test-watch   - Run tests in watch mode"
@echo "make lint         - Run linters"
@echo "make format       - Format code"
@echo "make db-up        - Start PostgreSQL with Podman"
@echo "make db-down      - Stop PostgreSQL"
@echo "make clean        - Clean cache and artifacts"

install:
pip install -r requirements.txt

dev:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
pytest tests/ -v

test-cov:
pytest tests/ --cov=app --cov-report=html --cov-report=term

test-watch:
pytest-watch tests/

lint:
flake8 app/ tests/
mypy app/

format:
black app/ tests/
isort app/ tests/

db-up:
podman-compose up -d postgres

db-down:
podman-compose down

clean:
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache
rm -rf htmlcov
rm -rf .coverage
rm -rf *.db
