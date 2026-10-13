import asyncio
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from foresight_os.analysis.evidence_workflow import accept_pending_evidence, run_evidence_workflow
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.page_retrieval import PageRetrievalCapability
from foresight_os.runtime.web_search import WebSearchHit
from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection
import openpyxl


class _Provider:
    name = "fixture-search"
    fingerprint = "fixture-search-v1"

    def __init__(self, url):
        self.url = url
        self.calls = 0

    async def search(self, query, *, max_results=5, freshness=None):
        self.calls += 1
        return [WebSearchHit("Capacity forecast", self.url, "A source excerpt", source=self.name)]


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body>The source reports a forecast fact.</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        return


def test_evidence_workflow_requires_explicit_acceptance_and_supports_restart(tmp_path: Path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/source"
        provider = _Provider(url)
        store = AnalysisStore(tmp_path / "case")
        rejected = asyncio.run(run_evidence_workflow(store, "capacity expansion cost", provider, retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"})))
        assert rejected.status == "rejected"
        assert provider.calls == 1
        assert rejected.analysis.revision_status.value == "REJECTED"

        provider = _Provider(url)
        store = AnalysisStore(tmp_path / "restart")
        accepted = asyncio.run(run_evidence_workflow(store, "capacity expansion cost", provider, retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"}), human_decision="ACCEPT"))
        assert accepted.status == "accepted"
        assert accepted.analysis.claims[0].evidence_ids == [accepted.evidence.id]
        assert provider.calls == 1

        pending_store = AnalysisStore(tmp_path / "pending")
        provider = _Provider(url)
        first = asyncio.run(run_evidence_workflow(pending_store, "capacity expansion cost", provider, retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"}), human_decision="PENDING"))
        assert first.status == "pending"
        assert first.analysis.revision_status.value == "PENDING_REVIEW"
        resumed = accept_pending_evidence(pending_store, human_decision="ACCEPT")
        assert resumed.status == "accepted"
        assert provider.calls == 1

        preserved_store = AnalysisStore(tmp_path / "preserved")
        accepted = asyncio.run(run_evidence_workflow(preserved_store, "capacity expansion cost", _Provider(url), retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"}), human_decision="ACCEPT"))
        rejected = asyncio.run(run_evidence_workflow(preserved_store, "capacity expansion cost", _Provider(url), retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"})))
        assert accepted.status == "accepted"
        assert rejected.status == "rejected"
        assert preserved_store.analysis_path.exists()
        assert preserved_store.load_analysis().revision_status.value == "ACCEPTED"
        assert preserved_store.load_analysis().evidence[0].id == accepted.analysis.evidence[0].id

        pending_twice = AnalysisStore(tmp_path / "pending-twice")
        first_pending = asyncio.run(run_evidence_workflow(pending_twice, "capacity expansion cost", _Provider(url), retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"}), human_decision="ACCEPT"))
        second_pending = asyncio.run(run_evidence_workflow(pending_twice, "capacity expansion cost", _Provider(url), retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"}), human_decision="PENDING"))
        third_pending = asyncio.run(run_evidence_workflow(pending_twice, "capacity expansion cost", _Provider(url), retrieval=PageRetrievalCapability(fixture_hosts={"127.0.0.1"}), human_decision="PENDING"))
        assert first_pending.status == "accepted"
        assert second_pending.status == third_pending.status == "pending"
        rejected = accept_pending_evidence(pending_twice, human_decision="REJECT")
        assert rejected.status == "rejected"
        assert pending_twice.load_analysis().revision_status.value == "ACCEPTED"
        assert pending_twice.load_analysis().evidence[0].id == first_pending.analysis.evidence[0].id
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_xlsx_finding_workflow_persists_provenance_calculation_and_restart(tmp_path: Path):
    from foresight_os.analysis.evidence_workflow import run_xlsx_finding_workflow

    source = tmp_path / "finding.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Demand"
    sheet.append(["Region", "Value"])
    sheet.append(["North", 10])
    sheet.append(["South", 20])
    sheet.tables.add(openpyxl.worksheet.table.Table(displayName="DemandTable", ref="A1:B3"))
    workbook.save(source)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    store = AnalysisStore(tmp_path / "xlsx-case")
    first = run_xlsx_finding_workflow(
        store,
        source,
        AnalysisOperation("sum", value_column="Value"),
        selection=SheetSelection(tables=(("Demand", "DemandTable"),)),
        human_decision="PENDING",
    )
    assert first.status == "pending"
    assert first.analysis.calculations[0].input_ids
    resumed = accept_pending_evidence(store, human_decision="ACCEPT")
    assert resumed.status == "accepted"
    assert resumed.analysis.calculations[0].input_ids
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
