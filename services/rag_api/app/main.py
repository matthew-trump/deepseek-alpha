import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .inference import get_inference_client, InferenceClient
from .prompt import build_prompt
from .retrieval import get_retriever, Retriever

log_level = "INFO"
logging.basicConfig(level=logging.getLevelName(log_level))
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    max_new_tokens: int = Field(default=200, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    text: str
    source: str


class ReasonRequest(ChatRequest):
    depth: Optional[int] = Field(default=None, ge=1, le=5, description="Hint for reasoning depth")


class ReasonResponse(ChatResponse):
    depth: Optional[int]


def get_app() -> FastAPI:
    api = FastAPI(title="RAG API Stub", version="0.1.0")

    @api.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/chat", response_model=ChatResponse)
    def chat(
        req: ChatRequest,
        client: InferenceClient = Depends(get_inference_client),
        retriever: Retriever = Depends(get_retriever),
    ) -> ChatResponse:
        contexts = retriever.fetch(req.prompt)
        prompt = build_prompt(req.prompt, contexts)
        try:
            text = client.generate(prompt, req.max_new_tokens, req.temperature)
        except Exception as exc:  # pragma: no cover - httpx wraps detail
            logger.exception("Inference call failed")
            raise HTTPException(status_code=502, detail="Inference backend error") from exc

        return ChatResponse(text=text, source="inference")

    @api.post("/reason", response_model=ReasonResponse)
    def reason(
        req: ReasonRequest,
        client: InferenceClient = Depends(get_inference_client),
        retriever: Retriever = Depends(get_retriever),
    ) -> ReasonResponse:
        contexts = retriever.fetch(req.prompt)
        prompt = build_prompt(req.prompt, contexts)
        try:
            text = client.generate(prompt, req.max_new_tokens, req.temperature)
        except Exception as exc:  # pragma: no cover
            logger.exception("Inference call failed")
            raise HTTPException(status_code=502, detail="Inference backend error") from exc

        return ReasonResponse(text=text, source="inference", depth=req.depth)

    return api


app = get_app()
