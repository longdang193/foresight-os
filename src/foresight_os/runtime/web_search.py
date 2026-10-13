from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from foresight_os.domain.validation import validate_evidence_candidate


class WebSearchError(RuntimeError):
    pass


class WebSearchConfigurationError(WebSearchError):
    pass


class WebSearchProvider(Protocol):
    name: str
    fingerprint: str

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        freshness: str | None = None,
    ) -> Sequence[Mapping[str, Any] | "WebSearchHit"]: ...


@dataclass(frozen=True)
class WebSearchHit:
    title: str
    url: str
    snippet: str
    published_at: str = ""
    source: str = ""


class ConfiguredWebSearchProvider:
    def __init__(self, endpoint: str, token: str | None = None, timeout_seconds: float = 15.0) -> None:
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise WebSearchConfigurationError("FORESIGHT_WEB_SEARCH_URL must be an HTTP(S) endpoint")
        self.endpoint = endpoint
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.name = "configured-web-search"
        self.fingerprint = f"{self.name}:{parsed.scheme}://{parsed.netloc}{parsed.path}"

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        freshness: str | None = None,
    ) -> Sequence[Mapping[str, Any]]:
        return await asyncio.to_thread(self._search_sync, query, max_results, freshness)

    def _search_sync(self, query: str, max_results: int, freshness: str | None) -> Sequence[Mapping[str, Any]]:
        payload = {"query": query, "max_results": max_results}
        if freshness:
            payload["freshness"] = freshness
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                document = json.loads(response.read(2_000_000).decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            raise WebSearchError(f"web search provider request failed: {type(error).__name__}") from error
        results = document.get("results") if isinstance(document, dict) else None
        if not isinstance(results, list):
            raise WebSearchError("web search provider returned an invalid results envelope")
        return results


class SearxngWebSearchProvider:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout_seconds: float = 15.0,
        categories: str = "general",
        language: str | None = None,
    ) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise WebSearchConfigurationError("FORESIGHT_WEB_SEARCH_URL must be an HTTP(S) endpoint")
        normalized_url = base_url.rstrip("/")
        self.endpoint = normalized_url if parsed.path.rstrip("/").endswith("/search") else f"{normalized_url}/search"
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.categories = categories.strip()
        self.language = language.strip() if language else None
        self.name = "searxng"
        endpoint_parts = urlsplit(self.endpoint)
        self.fingerprint = f"{self.name}:{endpoint_parts.scheme}://{endpoint_parts.netloc}{endpoint_parts.path}"

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        freshness: str | None = None,
    ) -> Sequence[Mapping[str, Any]]:
        return await asyncio.to_thread(self._search_sync, query, max_results, freshness)

    def _search_sync(self, query: str, max_results: int, freshness: str | None) -> Sequence[Mapping[str, Any]]:
        parameters = {"q": query, "format": "json", "pageno": "1"}
        if self.categories:
            parameters["categories"] = self.categories
        if self.language:
            parameters["language"] = self.language
        if freshness in {"day", "week", "month", "year"}:
            parameters["time_range"] = freshness
        request = Request(
            f"{self.endpoint}?{urlencode(parameters)}",
            headers={"Accept": "application/json", **self._authorization_header()},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                document = json.loads(response.read(2_000_000).decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            raise WebSearchError(f"SearXNG provider request failed: {type(error).__name__}") from error
        results = document.get("results") if isinstance(document, dict) else None
        if not isinstance(results, list):
            raise WebSearchError("SearXNG provider returned an invalid results envelope")
        hits: list[Mapping[str, Any]] = []
        for result in results:
            if not isinstance(result, Mapping):
                continue
            url = str(result.get("url", ""))
            title = str(result.get("title", ""))
            snippet = str(result.get("content", result.get("snippet", "")))
            if not url or not title and not snippet:
                continue
            engine = str(result.get("engine", "")).strip()
            hits.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "published_at": str(result.get("publishedDate", result.get("published_at", result.get("date", ""))) or ""),
                    "source": f"{self.name}:{engine}" if engine else self.name,
                }
            )
            if len(hits) >= max_results:
                break
        return hits

    def _authorization_header(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}


class WebSearchCapability:
    capability_id = "web_search"

    def __init__(self, provider: WebSearchProvider) -> None:
        self.provider = provider
        self.fingerprint = str(getattr(provider, "fingerprint", getattr(provider, "name", "web-search")))

    async def __call__(self, query: str, max_results: int = 5, freshness: str | None = None) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            raise WebSearchError("web search query cannot be empty")
        if len(query) > 500:
            raise WebSearchError("web search query exceeds 500 characters")
        if not 1 <= max_results <= 20:
            raise WebSearchError("web search max_results must be between 1 and 20")
        results = self.provider.search(query, max_results=max_results, freshness=freshness)
        if inspect.isawaitable(results):
            results = await results
        retrieved_at = datetime.now(timezone.utc).isoformat()
        candidates: list[dict[str, Any]] = []
        for index, result in enumerate(results[:max_results]):
            hit = self._normalize_hit(result)
            candidate_id = "web-" + hashlib.sha256(f"{query}\n{hit.url}\n{index}".encode("utf-8")).hexdigest()[:16]
            candidate = validate_evidence_candidate(
                {
                    "candidate_id": candidate_id,
                    "capability_id": self.capability_id,
                    "source": hit.source or str(getattr(self.provider, "name", "web-search")),
                    "request": query,
                    "excerpt": hit.snippet or hit.title,
                    "provenance": {
                        "source_version": hit.url,
                        "date": hit.published_at or retrieved_at,
                        "title": hit.title,
                        "url": hit.url,
                    },
                    "limitations": ["Search result excerpt; verify the source before acceptance."],
                    "acquisition_kind": "web_search",
                    "retrieved_at": retrieved_at,
                    "query": query,
                    "context": hit.url,
                    "retrieval_proof": None,
                }
            )
            candidates.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "capability_id": candidate.capability_id,
                    "source": candidate.source,
                    "request": candidate.request,
                    "excerpt": candidate.excerpt,
                    "provenance": candidate.provenance,
                    "limitations": candidate.limitations,
                    "acquisition_kind": candidate.acquisition_kind,
                    "retrieved_at": candidate.retrieved_at,
                    "query": candidate.query,
                    "context": candidate.context,
                }
            )
        return candidates

    @staticmethod
    def _normalize_hit(result: Mapping[str, Any] | WebSearchHit) -> WebSearchHit:
        if isinstance(result, WebSearchHit):
            hit = result
        elif isinstance(result, Mapping):
            hit = WebSearchHit(
                title=str(result.get("title", "")),
                url=str(result.get("url", "")),
                snippet=str(result.get("snippet", result.get("description", ""))),
                published_at=str(result.get("published_at", result.get("date", ""))),
                source=str(result.get("source", "")),
            )
        else:
            raise WebSearchError("web search provider returned a malformed result")
        if not hit.url or not hit.title and not hit.snippet:
            raise WebSearchError("web search provider returned a result without source identity or excerpt")
        return hit


def bind_web_search(provider: WebSearchProvider):
    from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityBindingKind, CapabilityOwnership

    capability = WebSearchCapability(provider)
    return CapabilityBinding(
        capability,
        kind=CapabilityBindingKind.TOOL,
        ownership=CapabilityOwnership.BORROWED,
        fingerprint=capability.fingerprint,
    )


def load_configured_web_search_provider(
    environ: Mapping[str, str] | None = None,
) -> ConfiguredWebSearchProvider | SearxngWebSearchProvider:
    values = os.environ if environ is None else environ
    endpoint = values.get("FORESIGHT_WEB_SEARCH_URL", "").strip()
    if not endpoint:
        raise WebSearchConfigurationError("FORESIGHT_WEB_SEARCH_URL is not configured")
    provider_kind = values.get("FORESIGHT_WEB_SEARCH_PROVIDER", "json-post").strip().lower()
    token = values.get("FORESIGHT_WEB_SEARCH_TOKEN")
    if provider_kind in {"searxng", "sear-xng"}:
        return SearxngWebSearchProvider(
            endpoint,
            token,
            categories=values.get("FORESIGHT_SEARXNG_CATEGORIES", "general"),
            language=values.get("FORESIGHT_SEARXNG_LANGUAGE"),
        )
    if provider_kind not in {"", "json-post", "configured"}:
        raise WebSearchConfigurationError(f"unsupported FORESIGHT_WEB_SEARCH_PROVIDER: {provider_kind}")
    return ConfiguredWebSearchProvider(endpoint, token)
