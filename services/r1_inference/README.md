# r1-inference service

Local-first FastAPI wrapper around a language model. Default mode is `mock` for fast testing; set `MODEL_MODE=transformers` to load a real model (e.g., `sshleifer/tiny-gpt2` for small local runs or a DeepSeek variant when GPUs are available).

## Quickstart
1) Create env + install deps:
```bash
make install
```
2) Copy env defaults and adjust as needed:
```bash
cp .env.example .env
# set MODEL_MODE=transformers and MODEL_NAME=<hf-model> when ready
```
3) Run locally (uses `.env`):
```bash
make run-r1
```
4) Call the endpoint:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_new_tokens": 32}'
```

## Testing
- Default tests run in mock mode: `make test`.
- Lint/format: `make lint` / `make format`.

## Docker
Build and run the container locally (mock mode by default):
```bash
make build-r1-image
# or
cd services/r1_inference && docker build -t deepseek-r1 .
docker run -p 8000:8000 --env MODEL_MODE=mock deepseek-r1
```

## Notes
- For real inference, install GPU-friendly deps (PyTorch) and set `MODEL_MODE=transformers` with an appropriate `MODEL_NAME`. Torch is not pinned in `requirements.txt`; install a CUDA build that matches your driver.
- Avoid committing downloaded weights or caches; use `.gitignore` patterns and prefer a shared model cache directory.
