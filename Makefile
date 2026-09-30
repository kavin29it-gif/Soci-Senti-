# Social Intelligence & Risk Scoring Platform Makefile
.PHONY: help up down seed test lint demo clean

PYTHON ?= .venv/bin/python
ifeq ($(OS),Windows_NT)
    PYTHON = .venv/Scripts/python.exe
endif

help:
	@echo "Available commands:"
	@echo "  make up      - Start local Supabase stack and Docker Compose infrastructure"
	@echo "  make down    - Stop all local containers and Supabase services"
	@echo "  make seed    - Generate sample dataset (>=5,000 posts) and seed database"
	@echo "  make test    - Run test suite with pytest"
	@echo "  make lint    - Run ruff linter and type checks"
	@echo "  make demo    - Run mock replay demo pipeline"

up:
	npx supabase start
	docker compose up -d

down:
	docker compose down
	npx supabase stop

seed:
	$(PYTHON) data/generate_sample.py
	npx supabase db reset --linked=false || true

test:
	$(PYTHON) -m pytest -v tests/

lint:
	$(PYTHON) -m ruff check .

demo:
	$(PYTHON) -m services.demo

clean:
	rm -rf __pycache__ .pytest_cache
