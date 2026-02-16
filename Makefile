.PHONY: help install run test clean docker-build docker-up docker-down

help:
	@echo "NUGU + OpenClaw + Home Assistant Integration"
	@echo ""
	@echo "Available targets:"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run webhook server"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean cache and logs"
	@echo "  make docker-build - Build Docker containers"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make format       - Format Python code"
	@echo "  make lint         - Run linting"

install:
	@echo "Installing dependencies..."
	cd webhook-server && python -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt

run:
	@echo "Starting webhook server..."
	cd webhook-server && python app.py

test:
	@echo "Running tests..."
	cd webhook-server && python -m pytest tests/

clean:
	@echo "Cleaning..."
	rm -rf webhook-server/venv
	rm -rf webhook-server/__pycache__
	rm -rf webhook-server/logs/*
	rm -rf .pytest_cache

docker-build:
	@echo "Building Docker containers..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	docker-compose logs -f nugu-webhook

format:
	@echo "Formatting Python code..."
	cd webhook-server && black app.py

lint:
	@echo "Linting Python code..."
	cd webhook-server && flake8 app.py
