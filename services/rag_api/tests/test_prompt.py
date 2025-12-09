from services.rag_api.app.prompt import build_prompt
from services.rag_api.app.retrieval import RetrievedChunk


def test_build_prompt_includes_context_and_user_prompt():
    contexts = [RetrievedChunk(content="ctx", source="stub", score=0.9)]
    prompt = build_prompt("Hello", contexts)
    assert "ctx" in prompt
    assert "Hello" in prompt
    assert "Source: stub" in prompt
