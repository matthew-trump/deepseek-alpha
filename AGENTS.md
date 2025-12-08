# Repository Guidelines

## Project Structure & Module Organization
- Root holds `README.md`; code is grouped by domain: `infra/` (Terraform), `services/` (`r1-inference/`, `rag-api/`), `frontend/` (`web/`), and `.github/workflows/` for CI. Keep ingestion assets in `data/` (not committed) and architecture notes in `docs/`.
- Place Python app code under `services/*/app/`; split FastAPI routers, model loaders, and utilities into clear submodules. Mirror this layout in tests for fast lookup.

## Build, Test, and Development Commands
- Install deps per service: `cd services/rag-api && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (repeat for `r1-inference`).
- Format/lint: `make lint` (black, isort, ruff) or run tools directly inside each service.
- Tests: `make test` at repo root (aggregates pytest) or `pytest` inside a specific service. Mark GPU-only tests with `-m gpu`.
- Containers: `docker build -t deepseek-r1 services/r1-inference` and `docker build -t rag-api services/rag-api`; tag with git SHA before pushing to ECR. Local check: `docker run --gpus all -p 8000:8000 deepseek-r1` then POST to `/generate`.

## Coding Style & Naming Conventions
- Python: 4-space indent, type hints for public functions, prefer pure helpers and small modules.
- Naming: snake_case for modules/functions, UpperCamelCase for classes, SCREAMING_SNAKE for constants. Route paths kebab-case; env vars upper snake case (e.g., `MODEL_NAME`).
- Use black + isort for formatting and ruff for linting; enable pre-commit hooks when available.

## Testing Guidelines
- Framework: pytest. Put tests in `services/*/tests/` matching package paths. Name files `test_<module>.py` and group with `Test*` classes when helpful.
- Cover prompt shaping, RAG retrieval fallbacks, and GPU-specific paths. Use fixtures for sample docs/embeddings; avoid checking large artifacts into git. Record expected curl examples for API routes.

## Commit & Pull Request Guidelines
- Commits are imperative; Conventional Commit prefixes (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`) encouraged for CI tagging.
- PRs: concise description, test evidence (`pytest`/`make test` output), linked issues/ADRs, and infra impacts (Terraform plan, new env vars, AWS resources). Include curl snippets or screenshots for API/UI changes and note rollout steps (migration, backfill, cache warm-up).

## Security & Configuration Tips
- Never commit secrets; use `.env.example` and store real values in AWS Secrets Manager/SSM. Keep model caches and data exports out of git via `.gitignore`.
- Expose `/generate` only to internal networks; front with ALB/WAF. Add structured logging (request id, user id, latency, token counts) and redact prompts with PII.
