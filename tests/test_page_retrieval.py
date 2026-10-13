import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from foresight_os.domain.evidence import normalize_evidence_candidate
from foresight_os.domain.validation import ValidationError
from foresight_os.runtime.page_retrieval import PageRetrievalCapability, PageRetrievalError


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/page")
            self.end_headers()
            return
        if self.path == "/missing":
            self.send_response(404)
            self.end_headers()
            return
        body = b"<html><head><title>Fixture</title><script>ignore</script></head><body>Capacity remains uncertain.</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        return


@pytest.fixture
def fixture_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_page_retrieval_returns_sanitized_text_and_adapter_proof(fixture_url):
    capability = PageRetrievalCapability(fixture_hosts={"127.0.0.1"})
    result = asyncio.run(capability(f"{fixture_url}/redirect", "capacity"))

    assert result["capability_id"] == "page_retrieval"
    assert result["retrieval_proof"].original_url.endswith("/redirect")
    assert result["retrieval_proof"].final_url.endswith("/page")
    assert "script" not in result["excerpt"]
    assert "raw_result" not in result
    evidence = normalize_evidence_candidate(result)
    assert evidence.source_locator.file_version == result["retrieval_proof"].content_hash


def test_page_retrieval_rejects_failures_and_private_targets(fixture_url):
    capability = PageRetrievalCapability(fixture_hosts={"127.0.0.1"}, max_bytes=10)
    with pytest.raises(PageRetrievalError) as oversized:
        asyncio.run(capability(f"{fixture_url}/page"))
    assert oversized.value.failure_class == "oversized_response"

    with pytest.raises(PageRetrievalError) as missing:
        asyncio.run(PageRetrievalCapability(fixture_hosts={"127.0.0.1"})(f"{fixture_url}/missing"))
    assert missing.value.failure_class == "http_error"

    with pytest.raises(PageRetrievalError) as private:
        asyncio.run(PageRetrievalCapability()("http://127.0.0.1:80/page"))
    assert private.value.failure_class == "blocked_network_target"

    with pytest.raises(PageRetrievalError) as credentials:
        asyncio.run(PageRetrievalCapability(fixture_hosts={"127.0.0.1"})("http://user:pass@127.0.0.1:80/page"))
    assert credentials.value.failure_class == "unsafe_url"


def test_search_only_external_candidate_cannot_become_durable_evidence():
    with pytest.raises(ValidationError, match="retrieval proof"):
        normalize_evidence_candidate({
            "candidate_id": "search-only",
            "capability_id": "web_search",
            "source": "search",
            "request": "capacity",
            "excerpt": "snippet",
            "provenance": {"url": "https://example.test"},
            "acquisition_kind": "web_search",
        })


def test_external_capability_cannot_bypass_proof_with_default_metadata():
    with pytest.raises(ValidationError, match="retrieval proof"):
        normalize_evidence_candidate({
            "candidate_id": "page-without-proof",
            "capability_id": "page_retrieval",
            "source": "https://example.test/source",
            "request": "capacity",
            "excerpt": "source text",
            "provenance": {"url": "https://example.test/source", "content_hash": "hash"},
        })
