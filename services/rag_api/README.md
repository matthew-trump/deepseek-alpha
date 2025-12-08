# rag-api service

FastAPI stub that forwards `/chat` and `/reason` to the inference service. Uses `INFERENCE_URL` (default `http://localhost:8000/generate`) to call the backend.

## Quickstart
1) Create env + install deps:
```bash
make install-rag
```
2) Copy env defaults and set the inference URL if needed:
```bash
cp .env.example .env
# export INFERENCE_URL=http://127.0.0.1:8000/generate
```
3) Run locally:
```bash
make run-rag
```
4) Call the API:
```bash
curl -X POST http://localhost:8100/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_new_tokens": 32}'
```

## Testing
- Run tests: `make test-rag`.
- Lint/format: `make lint-rag` / `make format-rag`.

## Notes
- The stub simply forwards prompts; add retrieval/prompt-building as the RAG layer evolves.
- Set `RAG_PORT` in `.env` if you need a different port.
