from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RetrievedChunk:
    content: str
    source: str
    score: float


class Retriever:
    def __init__(self, top_k: int = 3) -> None:
        self.top_k = top_k

    def fetch(self, query: str) -> List[RetrievedChunk]:
        # Placeholder retrieval; replace with vector DB call.
        return [
            RetrievedChunk(
                content=f"Context for: {query}",
                source="stub",
                score=1.0,
            )
        ]


_default_retriever: Optional[Retriever] = None


def get_retriever() -> Retriever:
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = Retriever()
    return _default_retriever
