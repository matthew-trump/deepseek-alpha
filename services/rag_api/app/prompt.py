from typing import Iterable, List

from services.rag_api.app.retrieval import RetrievedChunk


def build_prompt(user_prompt: str, contexts: Iterable[RetrievedChunk]) -> str:
    context_blocks: List[str] = []
    for chunk in contexts:
        context_blocks.append(f"Source: {chunk.source}\nScore: {chunk.score}\n{chunk.content}")
    context_text = "\n\n".join(context_blocks) if context_blocks else "(no context)"

    return (
        "You are a helpful assistant. Use the retrieved context when relevant.\n"
        f"Context:\n{context_text}\n\n"
        f"User: {user_prompt}\nAssistant:"
    )
