import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.rag_api.app.inference import get_inference_client, InferenceClient

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
    def chat(req: ChatRequest, client: InferenceClient = Depends(get_inference_client)) -> ChatResponse:
        try:
            text = client.generate(req.prompt, req.max_new_tokens, req.temperature)
        except Exception as exc:  # pragma: no cover - httpx wraps detail
            logger.exception("Inference call failed")
            raise HTTPException(status_code=502, detail="Inference backend error") from exc

        return ChatResponse(text=text, source="inference")

    @api.post("/reason", response_model=ReasonResponse)
    def reason(req: ReasonRequest, client: InferenceClient = Depends(get_inference_client)) -> ReasonResponse:
        try:
            text = client.generate(req.prompt, req.max_new_tokens, req.temperature)
        except Exception as exc:  # pragma: no cover
            logger.exception("Inference call failed")
            raise HTTPException(status_code=502, detail="Inference backend error") from exc

        return ReasonResponse(text=text, source="inference", depth=req.depth)

    return api


app = get_app()
