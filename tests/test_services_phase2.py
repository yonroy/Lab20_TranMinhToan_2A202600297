import json
from typing import Any

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


def test_llm_client_fallback_without_api_key() -> None:
    settings = Settings.model_validate({"OPENAI_API_KEY": None})
    client = LLMClient(settings=settings)

    response = client.complete(system_prompt="you are helpful", user_prompt="Explain GraphRAG")

    assert "Fallback LLM response" in response.content
    assert response.cost_usd == 0.0


def test_llm_client_fallback_after_provider_error(monkeypatch: Any) -> None:
    settings = Settings.model_validate({"OPENAI_API_KEY": "dummy-key"})
    client = LLMClient(settings=settings, max_retries=2)

    def _boom(system_prompt: str, user_prompt: str) -> None:
        raise RuntimeError("provider down")

    monkeypatch.setattr(client, "_complete_openai", _boom)
    response = client.complete(system_prompt="sys", user_prompt="user")

    assert "provider error" in response.content
    assert response.cost_usd == 0.0


def test_search_client_fallback_without_tavily_key() -> None:
    settings = Settings.model_validate({"TAVILY_API_KEY": None})
    client = SearchClient(settings=settings)

    docs = client.search("state of the art GraphRAG", max_results=3)

    assert len(docs) >= 1
    assert docs[0].metadata["provider"] == "fallback"


def test_search_client_normalizes_tavily_results(monkeypatch: Any) -> None:
    settings = Settings.model_validate({"TAVILY_API_KEY": "dummy-key"})
    client = SearchClient(settings=settings)

    class _FakeHTTPResponse:
        def __enter__(self) -> "_FakeHTTPResponse":
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        def read(self) -> bytes:
            payload = {
                "results": [
                    {
                        "title": "GraphRAG Survey",
                        "url": "https://example.com/graphrag",
                        "content": "GraphRAG combines retrieval with graph structure.",
                        "score": 0.91,
                    }
                ]
            }
            return json.dumps(payload).encode("utf-8")

    def _fake_urlopen(req: object, timeout: int) -> _FakeHTTPResponse:
        return _FakeHTTPResponse()

    monkeypatch.setattr("multi_agent_research_lab.services.search_client.request.urlopen", _fake_urlopen)
    docs = client.search("GraphRAG", max_results=1)

    assert len(docs) == 1
    assert docs[0].title == "GraphRAG Survey"
    assert docs[0].url == "https://example.com/graphrag"
    assert docs[0].metadata["provider"] == "tavily"
