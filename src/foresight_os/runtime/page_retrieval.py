import asyncio
import hashlib
import ipaddress
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from foresight_os.domain.models import EvidenceCandidate
from foresight_os.domain.validation import ValidationError, validate_evidence_candidate


class PageRetrievalError(RuntimeError):
    def __init__(self, failure_class: str, message: str):
        super().__init__(message)
        self.failure_class = failure_class


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "template"}:
            self._ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "template"} and self._ignored:
            self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored:
            value = " ".join(data.split())
            if value:
                self.parts.append(value)


@dataclass(frozen=True)
class SourceRetrievalProof:
    original_url: str
    final_url: str
    retrieved_at: str
    content_hash: str
    _issuer: object

    def is_valid(self) -> bool:
        return self._issuer is _PROOF_ISSUER and all((self.original_url, self.final_url, self.retrieved_at, self.content_hash))


_PROOF_ISSUER = object()
_AUTHORITY_MARKERS = ("change capabilities", "change permissions", "grant authority", "increase budget")


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _is_fixture_host(hostname: str, fixture_hosts: set[str]) -> bool:
    return hostname.lower().rstrip(".") in {item.lower().rstrip(".") for item in fixture_hosts}


def validate_destination(url: str, fixture_hosts: set[str]) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise PageRetrievalError("invalid_url", "page retrieval accepts only HTTP(S) URLs")
    if parsed.username or parsed.password:
        raise PageRetrievalError("unsafe_url", "page retrieval rejects URL credentials")
    hostname = parsed.hostname
    if _is_fixture_host(hostname, fixture_hosts):
        return
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
    except OSError as error:
        raise PageRetrievalError("dns_failure", "page retrieval could not resolve the hostname") from error
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or not ip.is_global:
            raise PageRetrievalError("blocked_network_target", "page retrieval rejected a non-public network target")


class PageRetrievalCapability:
    capability_id = "page_retrieval"

    def __init__(self, *, timeout_seconds: float = 5.0, max_bytes: int = 1_000_000, max_redirects: int = 3, fixture_hosts: set[str] | None = None):
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects
        self.fixture_hosts = set(fixture_hosts or ())
        self.fingerprint = f"page-retrieval-v1:{max_bytes}:{max_redirects}"

    def _fetch(self, url: str) -> tuple[str, str, bytes, str]:
        original = url
        current = url
        opener = build_opener(ProxyHandler({}), _NoRedirectHandler())
        for _ in range(self.max_redirects + 1):
            validate_destination(current, self.fixture_hosts)
            request = Request(current, headers={"User-Agent": "foresight-os/page-retrieval"})
            try:
                with opener.open(request, timeout=self.timeout_seconds) as response:
                    status = getattr(response, "status", response.getcode())
                    final_url = response.geturl()
                    if status >= 400:
                        raise PageRetrievalError("http_error", f"page retrieval returned HTTP {status}")
                    content_type = response.headers.get_content_type()
                    if content_type not in {"text/html", "text/plain", "application/xhtml+xml"}:
                        raise PageRetrievalError("unsupported_content_type", "page retrieval requires text content")
                    declared = response.headers.get("Content-Length")
                    if declared and int(declared) > self.max_bytes:
                        raise PageRetrievalError("oversized_response", "page retrieval response exceeds the byte limit")
                    body = response.read(self.max_bytes + 1)
                    if len(body) > self.max_bytes:
                        raise PageRetrievalError("oversized_response", "page retrieval response exceeds the byte limit")
                    return original, final_url, body, content_type
            except HTTPError as error:
                if error.code in {301, 302, 303, 307, 308}:
                    location = error.headers.get("Location")
                    if not location:
                        raise PageRetrievalError("unsafe_redirect", "redirect response omitted a location") from error
                    current = urljoin(current, location)
                    continue
                raise PageRetrievalError("http_error", f"page retrieval returned HTTP {error.code}") from error
            except (TimeoutError, socket.timeout) as error:
                raise PageRetrievalError("timeout", "page retrieval timed out") from error
            except URLError as error:
                raise PageRetrievalError("network_error", "page retrieval failed at the network boundary") from error
        raise PageRetrievalError("too_many_redirects", "page retrieval exceeded the redirect limit")

    async def __call__(self, candidate: dict[str, Any] | str, request: str | None = None) -> dict[str, Any]:
        url = candidate if isinstance(candidate, str) else str(candidate.get("url", ""))
        if not url:
            raise PageRetrievalError("invalid_url", "page retrieval requires a source URL")
        original_url, final_url, body, content_type = await asyncio.to_thread(self._fetch, url)
        try:
            decoded = body.decode("utf-8", errors="replace")
            if content_type in {"text/html", "application/xhtml+xml"}:
                parser = _TextExtractor()
                parser.feed(decoded)
                text = " ".join(parser.parts)
            else:
                text = " ".join(decoded.split())
        except Exception as error:
            raise PageRetrievalError("malformed_content", "page retrieval could not parse the source") from error
        if not text:
            raise PageRetrievalError("empty_source", "page retrieval returned no readable text")
        if any(marker in text.lower() for marker in _AUTHORITY_MARKERS):
            raise PageRetrievalError("authority_altering_content", "retrieved content attempted to alter runtime authority")
        retrieved_at = datetime.now(timezone.utc).isoformat()
        proof = SourceRetrievalProof(original_url, final_url, retrieved_at, hashlib.sha256(body).hexdigest(), _PROOF_ISSUER)
        candidate_id = "page-" + hashlib.sha256(f"{final_url}\n{proof.content_hash}".encode()).hexdigest()[:16]
        result = validate_evidence_candidate({
            "candidate_id": candidate_id,
            "capability_id": self.capability_id,
            "source": final_url,
            "request": request or final_url,
            "excerpt": text[:4000],
            "provenance": {
                "url": final_url,
                "source_version": proof.content_hash,
                "retrieved_at": retrieved_at,
                "content_hash": proof.content_hash,
            },
            "limitations": ["Retrieved content is untrusted and source credibility requires separate review."],
            "acquisition_kind": self.capability_id,
            "retrieved_at": retrieved_at,
            "query": request or final_url,
            "context": final_url,
            "retrieval_proof": proof,
        })
        output = result.__dict__.copy()
        output.pop("raw_result", None)
        return output


def bind_page_retrieval(capability: PageRetrievalCapability):
    from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityBindingKind, CapabilityOwnership
    return CapabilityBinding(capability, kind=CapabilityBindingKind.TOOL, ownership=CapabilityOwnership.BORROWED, fingerprint=capability.fingerprint)

