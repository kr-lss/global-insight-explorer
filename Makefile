.PHONY: help install run test clean docker-build docker-run docker-stop lint format

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make run          - Run the application"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove temporary files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-stop  - Stop Docker container"
	@echo "  make lint         - Run linter"
	@echo "  make format       - Format code"

install:
	pip install -r requirements.txt
	pip install -e .

run:
	python -m app.main

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

lint:
	@echo "Run linting with flake8..."
	@pip install flake8 2>/dev/null || true
	@flake8 app/ --max-line-length=100 --exclude=__pycache__

format:
	@echo "Format code with black..."
	@pip install black 2>/dev/null || true
	@black app/ tests/

dev:
	@echo "Starting development server..."
	export DEBUG=True && python -m app.main
