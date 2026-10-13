import argparse
import asyncio
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from foresight_os.analysis.evidence_workflow import run_evidence_workflow
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.page_retrieval import PageRetrievalCapability
from foresight_os.runtime.web_search import WebSearchHit


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body>A deterministic forecast fact.</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        return


class _Provider:
    name = "fixture-search"
    fingerprint = "fixture-search-v1"

    def __init__(self, url):
        self.url = url

    async def search(self, query, *, max_results=5, freshness=None):
        return [WebSearchHit("Fixture source", self.url, "discovery excerpt", source=self.name)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "work" / "toolbelt-probes")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        store = AnalysisStore(args.output_root / "evidence-workflow")
        result = asyncio.run(run_evidence_workflow(store, "capacity", _Provider(f"http://127.0.0.1:{server.server_port}/source"), retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"}), human_decision="ACCEPT"))
        receipt = {
            "mode": "evidence-workflow",
            "status": "verified" if result.status == "accepted" else "failed",
            "candidate_count": len(result.candidates),
            "tool_calls": list(result.tool_calls),
            "claim_evidence_linked": bool(result.claim and result.evidence and result.claim.evidence_ids == [result.evidence.id]),
            "revision_status": result.analysis.revision_status.value if result.analysis else None,
            "raw_payload_retained": False,
        }
    finally:
        server.shutdown()
        thread.join(timeout=2)
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "evidence-workflow-probe.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
