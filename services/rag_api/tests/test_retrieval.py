from services.rag_api.app.retrieval import Retriever


def test_retriever_returns_stub_context():
    retriever = Retriever(top_k=2)
    results = retriever.fetch("hello")
    assert len(results) >= 1
    assert "hello" in results[0].content
