"""Search client abstraction for ResearcherAgent."""

import json
from typing import Any
from urllib import error, request

from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client skeleton."""

    _TAVILY_ENDPOINT = "https://api.tavily.com/search"

    def __init__(
        self,
        settings: Settings | None = None,
        timeout_seconds: int | None = None,
        max_retries: int = 3,
    ) -> None:
        self.settings = settings or get_settings()
        self.timeout_seconds = timeout_seconds or self.settings.timeout_seconds
        self.max_retries = max(1, max_retries)

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Uses Tavily API when configured, with retry and normalized output.
        Falls back to a local placeholder source if provider is unavailable.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            return self._fallback_documents(query="", reason="empty query")

        if not self.settings.tavily_api_key:
            return self._fallback_documents(query=cleaned_query, reason="TAVILY_API_KEY is missing")

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                retry=retry_if_exception_type((error.URLError, TimeoutError, json.JSONDecodeError)),
                reraise=True,
            ):
                with attempt:
                    documents = self._search_tavily(cleaned_query, max_results=max_results)
                    if documents:
                        return documents
                    return self._fallback_documents(query=cleaned_query, reason="provider returned no results")
        except Exception as exc:
            return self._fallback_documents(query=cleaned_query, reason=f"provider error: {type(exc).__name__}")

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "max_results": max(1, max_results),
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
        }
        raw_body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=self._TAVILY_ENDPOINT,
            data=raw_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
            payload_obj = json.loads(response_body)

        results: list[dict[str, Any]] = payload_obj.get("results", [])
        documents: list[SourceDocument] = []
        for item in results:
            title = str(item.get("title") or "Untitled source")
            url = item.get("url")
            snippet_raw = item.get("content") or item.get("snippet") or ""
            snippet = str(snippet_raw).strip() or "No snippet returned by provider."
            documents.append(
                SourceDocument(
                    title=title,
                    url=str(url) if url else None,
                    snippet=snippet[:800],
                    metadata={
                        "provider": "tavily",
                        "score": item.get("score"),
                        "published_date": item.get("published_date"),
                    },
                )
            )
        return documents

    def _fallback_documents(self, query: str, reason: str) -> list[SourceDocument]:
        summary = query if len(query) <= 180 else f"{query[:177]}..."
        return [
            SourceDocument(
                title="Fallback local research note",
                url=None,
                snippet=(
                    "Search provider unavailable. "
                    f"Reason: {reason}. "
                    f"Requested query: {summary}"
                ),
                metadata={"provider": "fallback", "reason": reason},
            )
        ]
