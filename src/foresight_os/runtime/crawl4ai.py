from __future__ import annotations

import asyncio
import hashlib
import socket
from urllib.parse import urljoin, urlsplit
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from foresight_os.domain.validation import validate_evidence_candidate
from foresight_os.runtime.page_retrieval import validate_destination


class Crawl4AIError(RuntimeError):
    def __init__(self, failure_class: str, message: str):
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class CrawlRetrievalProof:
    original_url: str
    final_url: str
    retrieved_at: str
    content_hash: str
    excerpt_hash: str
    _issuer: object

    def is_valid(self) -> bool:
        return self._issuer is _PROOF_ISSUER and all((self.original_url, self.final_url, self.retrieved_at, self.content_hash, self.excerpt_hash))


_PROOF_ISSUER = object()


class Crawl4AICapability:
    capability_id = "web_crawl"

    def __init__(self, *, timeout_seconds: float = 30.0, max_content_chars: int = 4_000, fixture_hosts: set[str] | None = None):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_content_chars < 1:
            raise ValueError("max_content_chars must be positive")
        self.timeout_seconds = timeout_seconds
        self.max_content_chars = max_content_chars
        self.fixture_hosts = set(fixture_hosts or ())
        self.fingerprint = f"crawl4ai-v1:{timeout_seconds}:{max_content_chars}"

    async def __call__(self, url: str, request: str | None = None) -> dict[str, Any]:
        url = str(url).strip()
        if not url:
            raise Crawl4AIError("invalid_url", "web crawl requires a source URL")
        try:
            initial_addresses = validate_destination(url, self.fixture_hosts)
        except Exception as error:
            failure_class = getattr(error, "failure_class", "invalid_url")
            raise Crawl4AIError(failure_class, str(error)) from error
        try:
            import crawl4ai

            AsyncWebCrawler = crawl4ai.AsyncWebCrawler
            config_type = getattr(crawl4ai, "CrawlerRunConfig", None)
            try:
                from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
            except (ImportError, ModuleNotFoundError):
                AsyncPlaywrightCrawlerStrategy = None

            strategy_type = AsyncPlaywrightCrawlerStrategy
            browser_config_type = getattr(crawl4ai, "BrowserConfig", None)
        except ImportError as error:
            raise Crawl4AIError("dependency_missing", "crawl4ai is not installed") from error
        retrieved_at = datetime.now(timezone.utc).isoformat()
        try:
            crawler_kwargs = {}
            browser_config = None
            if browser_config_type is not None:
                extra_args = []
                extra_args.append("--disable-service-worker")
                if initial_addresses:
                    extra_args.append(f"--host-resolver-rules=MAP {urlsplit(url).hostname} {initial_addresses[0]}")
                browser_config = browser_config_type(
                    headless=True,
                    java_script_enabled=True,
                    verbose=False,
                    ignore_https_errors=True,
                    extra_args=extra_args,
                )
            if strategy_type is not None:
                strategy = strategy_type(browser_config=browser_config)
                origin_host = (urlsplit(url).hostname or "").lower().rstrip(".")

                async def guard_page_context(page, context=None, **_):
                    async def guard_request(route):
                        request_url = route.request.url
                        if request_url.startswith(("http://", "https://")):
                            try:
                                validate_destination(request_url, self.fixture_hosts)
                                request_host = (urlsplit(request_url).hostname or "").lower().rstrip(".")
                                if request_host != origin_host and request_host not in {item.lower().rstrip(".") for item in self.fixture_hosts}:
                                    await route.abort("blockedbyclient")
                                    return
                            except Exception:
                                await route.abort("blockedbyclient")
                                return
                        await route.continue_()

                    if context is not None:
                        await context.add_init_script(
                            """
                            (() => {
                              const serviceWorker = navigator.serviceWorker;
                              if (!serviceWorker) return;
                              try {
                                Object.defineProperty(navigator, "serviceWorker", {
                                  configurable: false,
                                  enumerable: true,
                                  value: new Proxy(serviceWorker, {
                                    get(target, property, receiver) {
                                      if (property === "register") {
                                        return () => Promise.reject(new Error("service workers disabled"));
                                      }
                                      return Reflect.get(target, property, receiver);
                                    }
                                  })
                                });
                              } catch (_) {}
                            })();
                            """
                        )
                        await context.route("**/*", guard_request)
                    else:
                        await page.route("**/*", guard_request)

                strategy.set_hook("on_page_context_created", guard_page_context)
                crawler_kwargs["crawler_strategy"] = strategy
            if browser_config is not None:
                crawler_kwargs["config"] = browser_config
            async with AsyncWebCrawler(**crawler_kwargs) as crawler:
                if config_type is not None:
                    config = config_type(
                        only_text=True,
                        process_iframes=False,
                        exclude_external_links=True,
                        exclude_external_images=True,
                        deep_crawl_strategy=None,
                        max_retries=0,
                    )
                    operation = crawler.arun(url=url, config=config)
                else:
                    operation = crawler.arun(url=url)
                result = await asyncio.wait_for(operation, timeout=self.timeout_seconds)
        except asyncio.TimeoutError as error:
            raise Crawl4AIError("timeout", "Crawl4AI exceeded its time limit") from error
        except (OSError, socket.error) as error:
            raise Crawl4AIError("network_error", "Crawl4AI failed at the network boundary") from error
        except Exception as error:
            raise Crawl4AIError("crawl_failed", f"Crawl4AI returned {type(error).__name__}") from error
        if not bool(getattr(result, "success", False)):
            raise Crawl4AIError("crawl_failed", "Crawl4AI did not produce a successful result")
        markdown = str(getattr(result, "markdown", "") or "")
        if not markdown.strip():
            raise Crawl4AIError("empty_source", "Crawl4AI returned no readable content")
        final_url = str(getattr(result, "url", "") or url)
        try:
            validate_destination(final_url, self.fixture_hosts)
        except Exception as error:
            failure_class = getattr(error, "failure_class", "unsafe_redirect")
            raise Crawl4AIError(failure_class, str(error)) from error
        content_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
        excerpt = " ".join(markdown.split())[: self.max_content_chars]
        proof = CrawlRetrievalProof(url, final_url, retrieved_at, content_hash, hashlib.sha256(excerpt.encode("utf-8")).hexdigest(), _PROOF_ISSUER)
        links = getattr(result, "links", {}) or {}
        link_values = links.values() if isinstance(links, dict) else (links,)
        for values in link_values:
            if isinstance(values, str):
                values = (values,)
            for link in values:
                if isinstance(link, str) and link.startswith(("http://", "https://")):
                    try:
                        validate_destination(urljoin(final_url, link), self.fixture_hosts)
                    except Exception as error:
                        failure_class = getattr(error, "failure_class", "unsafe_subresource")
                        raise Crawl4AIError(failure_class, str(error)) from error
        link_count = sum(len(value) for value in links.values()) if isinstance(links, dict) else len(links)
        candidate = validate_evidence_candidate(
            {
                "candidate_id": "crawl-" + hashlib.sha256(f"{final_url}\n{content_hash}".encode("utf-8")).hexdigest()[:16],
                "capability_id": self.capability_id,
                "source": final_url,
                "request": request or final_url,
                "excerpt": excerpt,
                "provenance": {
                    "url": final_url,
                    "source_version": content_hash,
                    "content_hash": content_hash,
                    "retrieved_at": retrieved_at,
                    "http_status": str(getattr(result, "status_code", "")),
                    "link_count": str(link_count),
                },
                "limitations": ["Crawled content is untrusted and source credibility requires separate review."],
                "acquisition_kind": self.capability_id,
                "retrieved_at": retrieved_at,
                "query": request or final_url,
                "context": final_url,
                "retrieval_proof": proof,
            }
        )
        output = candidate.__dict__.copy()
        output.pop("raw_result", None)
        return output


def bind_crawl4ai(capability: Crawl4AICapability):
    from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityBindingKind, CapabilityOwnership

    return CapabilityBinding(
        capability,
        kind=CapabilityBindingKind.TOOL,
        ownership=CapabilityOwnership.BORROWED,
        fingerprint=capability.fingerprint,
    )
