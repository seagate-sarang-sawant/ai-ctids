# AI-CTIDS Makefile for common development tasks

.PHONY: help setup install install-dev install-minimal install-service train test lint format clean docker-build docker-up docker-down deploy test-api test-api-quick test-api-prepare test-api-full

help:
	@echo "AI-CTIDS Development Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup              - Initial project setup"
	@echo "  make install            - Install all dependencies (from requirements.txt)"
	@echo "  make install-dev        - Install development dependencies"
	@echo "  make install-minimal    - Install minimal production dependencies"
	@echo "  make install-service    - Install service-specific deps (use SERVICE=name)"
	@echo ""
	@echo "Development:"
	@echo "  make train              - Train models"
	@echo "  make test               - Run tests"
	@echo "  make lint               - Run linters"
	@echo "  make format             - Format code"
	@echo "  make clean              - Clean generated files"
	@echo ""
	@echo "API Testing & Evaluation:"
	@echo "  make test-api-quick     - Quick API test (health + sample predictions)"
	@echo "  make test-api-prepare   - Prepare test datasets"
	@echo "  make test-api           - Run API evaluation with test data"
	@echo "  make test-api-full      - Run complete API evaluation suite"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build       - Build Docker images"
	@echo "  make docker-up          - Start all services"
	@echo "  make docker-down        - Stop all services"
	@echo "  make docker-logs        - View service logs"
	@echo ""
	@echo "Services:"
	@echo "  make api-dev            - Start API in dev mode"
	@echo "  make generate-data      - Generate/stream data"
	@echo "  make monitor-drift      - Start drift monitor"
	@echo "  make health-check       - Check service health"

setup:
	@echo "Setting up AI-CTIDS development environment..."
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	cp .env.example .env
	mkdir -p data models logs
	@echo "✓ Setup complete! Activate virtualenv with: source venv/bin/activate"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ All dependencies installed"

install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	@echo "✓ Development dependencies installed"

install-minimal:
	@echo "Installing minimal production dependencies..."
	pip install -r requirements-minimal.txt
	@echo "✓ Minimal dependencies installed"

install-service:
	@echo "Installing service-specific dependencies..."
	@echo "Usage: make install-service SERVICE=batch-trainer"
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE variable not set"; \
		exit 1; \
	fi
	pip install -r $(SERVICE)/requirements.txt
	@echo "✓ $(SERVICE) dependencies installed"

train:
	@echo "Training models..."
	cd batch-trainer && python train.py \
		--data-path ../data/cicids2017.csv \
		--output-dir ../models \
		--models logistic_regression xgboost ann

evaluate:
	@echo "Evaluating models..."
	cd batch-trainer && python evaluate.py \
		--model-path ../models/xgboost_model.pkl \
		--model-type xgboost \
		--test-data ../data/test_data.csv

test:
	@echo "Running tests..."
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

lint:
	@echo "Running linters..."
	flake8 shared/ batch-trainer/ inference-api/ streaming-consumer/ --max-line-length=127
	mypy shared/ --ignore-missing-imports

format:
	@echo "Formatting code..."
	black shared/ batch-trainer/ inference-api/ streaming-consumer/ data-ingestion/ drift-monitor/
	isort shared/ batch-trainer/ inference-api/ streaming-consumer/ data-ingestion/ drift-monitor/

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services..."
	docker-compose up -d

docker-down:
	@echo "Stopping services..."
	docker-compose down

docker-logs:
	docker-compose logs -f

api-dev:
	@echo "Starting inference API in dev mode..."
	cd inference-api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

generate-data:
	@echo "Ingesting data stream..."
	cd data-ingestion && python generate.py \
		--data-path ../data/cicids2017.csv \
		--mode stream \
		--rate 10 \
		--kafka-servers localhost:9092

monitor-drift:
	@echo "Starting drift monitor..."
	cd drift-monitor && python monitor.py \
		--reference-data ../data/cicids2017.csv \
		--kafka-servers localhost:9092

clean:
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf wandb/
	@echo "✓ Cleaned"

deploy-prod:
	@echo "Deploying to production..."
	@echo "Building production images..."
	docker-compose -f docker-compose.prod.yml build
	@echo "Pushing images..."
	docker-compose -f docker-compose.prod.yml push
	@echo "✓ Deployed"

requirements:
	@echo "Creating requirements.txt files..."
	pip freeze > requirements.txt

docs:
	@echo "Opening documentation..."
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Grafana: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"

health-check:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/healthz || echo "❌ Inference API down"
	@curl -s http://localhost:9090/-/healthy || echo "❌ Prometheus down"
	@curl -s http://localhost:3000/api/health || echo "❌ Grafana down"
	@echo "✓ Health check complete"

# API Testing & Evaluation
test-api-quick:
	@echo "Running quick API test..."
	python3 tests/api_evaluation/quick_test.py

test-api-prepare:
	@echo "Preparing test datasets..."
	python3 tests/api_evaluation/prepare_test_data.py \
		--data-path ./data/cicids2017.csv \
		--output-dir ./tests/api_evaluation/data \
		--n-validation 1000 \
		--n-test 1000
	python3 tests/api_evaluation/generate_simulated_data.py \
		--n-samples 500 \
		--output ./tests/api_evaluation/data/simulated_flows.csv

test-api:
	@echo "Running API evaluation with validation set..."
	python3 tests/api_evaluation/test_api.py \
		--data-path ./tests/api_evaluation/data/validation_small.csv \
		--batch-size 32 \
		--output ./tests/api_evaluation/results_validation.json

test-api-full:
	@echo "Running complete API evaluation suite..."
	python3 tests/api_evaluation/run_all_tests.py

.DEFAULT_GOAL := help
