import logging
import os
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Basic logging configuration driven by LOG_LEVEL.
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logging.getLevelName(log_level))
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt to send to the model")
    max_new_tokens: int = Field(default=200, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class GenerateResponse(BaseModel):
    text: str
    model: str
    mode: str


class BaseModelClient:
    mode: str
    model_name: Optional[str] = None

    def generate(self, prompt: str, max_new_tokens: int, temperature: float) -> str:
        raise NotImplementedError


class MockModelClient(BaseModelClient):
    def __init__(self) -> None:
        self.mode = "mock"
        self.model_name = "mock-echo"

    def generate(self, prompt: str, max_new_tokens: int, temperature: float) -> str:
        suffix = " " if not prompt.endswith(" ") else ""
        return f"{prompt}{suffix}[mock completion]"[: len(prompt) + max_new_tokens]


class TransformersModelClient(BaseModelClient):
    def __init__(self, model_name: str) -> None:
        self.mode = "transformers"
        self.model_name = model_name
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError as exc:  # pragma: no cover - import-time guard
            raise RuntimeError(
                "Install transformers and torch to use MODEL_MODE=transformers"
            ) from exc

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        logger.info("Loaded transformers model %s on %s", model_name, self.device)

    def generate(self, prompt: str, max_new_tokens: int, temperature: float) -> str:
        from torch import no_grad

        do_sample = temperature > 0
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with no_grad():
            output_tokens = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        completion = output_tokens[0]
        return self.tokenizer.decode(completion, skip_special_tokens=True)


def create_model_client() -> BaseModelClient:
    mode = os.getenv("MODEL_MODE", "mock").lower()
    if mode == "mock":
        return MockModelClient()

    model_name = os.getenv("MODEL_NAME", "sshleifer/tiny-gpt2")
    return TransformersModelClient(model_name=model_name)


@lru_cache(maxsize=1)
def get_model_client() -> BaseModelClient:
    return create_model_client()


def get_app() -> FastAPI:
    api = FastAPI(title="DeepSeek R1 Inference", version="0.1.0")

    @api.on_event("startup")
    def _load_model() -> None:
        client = get_model_client()
        logger.info("Model client ready: mode=%s model=%s", client.mode, client.model_name)

    @api.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/generate", response_model=GenerateResponse)
    def generate(req: GenerateRequest) -> GenerateResponse:
        client = get_model_client()
        try:
            text = client.generate(
                prompt=req.prompt,
                max_new_tokens=req.max_new_tokens,
                temperature=req.temperature,
            )
        except RuntimeError as exc:
            logger.exception("Model runtime error")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return GenerateResponse(text=text, model=client.model_name or "unknown", mode=client.mode)

    return api


app = get_app()
