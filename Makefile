PYTHON ?= python3
VENV ?= .venv
ACTIVATE = source $(VENV)/bin/activate
R1_PATH = services/r1_inference
R1_MODULE = services.r1_inference.app.main
RAG_PATH = services/rag_api
RAG_MODULE = services.rag_api.app.main

.PHONY: help install lint format test run-r1 build-r1-image
 .PHONY: install-rag test-rag run-rag lint-rag format-rag

help:
	@echo "Common targets:"
	@echo "  make install        - create venv and install r1-inference deps"
	@echo "  make lint           - run ruff and black on r1-inference"
	@echo "  make test           - run pytest for r1-inference"
	@echo "  make install-rag    - create venv and install rag-api deps"
	@echo "  make test-rag       - run pytest for rag-api"
	@echo "  make run-rag        - start rag-api dev server"
	@echo "  make run-r1         - start FastAPI dev server (uses .env if present)"
	@echo "  make build-r1-image - docker build r1-inference image"

install:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install -U pip
	$(ACTIVATE) && pip install -r $(R1_PATH)/requirements.txt

lint:
	$(ACTIVATE) && ruff check $(R1_PATH)
	$(ACTIVATE) && black --check $(R1_PATH)

format:
	$(ACTIVATE) && black $(R1_PATH)

test:
	$(ACTIVATE) && pytest $(R1_PATH)/tests

run-r1:
	$(ACTIVATE) && env $$(grep -v '^#' .env 2>/dev/null | xargs) uvicorn $(R1_MODULE):app --reload --host $${HOST:-0.0.0.0} --port $${PORT:-8000}

build-r1-image:
	docker build -t deepseek-r1 $(R1_PATH)

install-rag:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install -U pip
	$(ACTIVATE) && pip install -r $(RAG_PATH)/requirements.txt

test-rag:
	$(ACTIVATE) && pytest $(RAG_PATH)/tests

lint-rag:
	$(ACTIVATE) && ruff check $(RAG_PATH)
	$(ACTIVATE) && black --check $(RAG_PATH)

format-rag:
	$(ACTIVATE) && black $(RAG_PATH)

run-rag:
	$(ACTIVATE) && env $$(grep -v '^#' .env 2>/dev/null | xargs) uvicorn $(RAG_MODULE):app --reload --host $${HOST:-0.0.0.0} --port $${RAG_PORT:-8100}
