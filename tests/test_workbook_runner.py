from dataclasses import dataclass
from pathlib import Path

import openpyxl

from foresight_os.analysis.workbook_engine import DomainAnalysis
from foresight_os.analysis.workbook_runner import WorkbookWorkflowRunner
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.domain.models import AnalysisState, Revision, RevisionStatus
from foresight_os.persistence.analysis_store import AnalysisStore
from tests.test_review_records import make_state


@dataclass(frozen=True)
class _DomainOutput:
    state: AnalysisState


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "runner.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(["Entity", "Value"])
    sheet.append(["North", 10])
    workbook.save(source)
    return source


def _contract() -> AnalysisInputContract:
    return AnalysisInputContract(domain="runner", required_tables=("Data",))


def _analyzer(material, contract):
    state = make_state()
    return DomainAnalysis(result=_DomainOutput(state), state=state)


def test_runner_publishes_reviews_accepts_and_renders_only_after_acceptance(tmp_path):
    store = AnalysisStore(tmp_path / "accepted")
    report_calls = []

    def render(path, result, state):
        report_calls.append((path, state.revision_status))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("accepted", encoding="utf-8")

    outcome = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        _contract(),
        _analyzer,
        human_decision="ACCEPT",
        render_report=render,
    )

    assert outcome.status == "accepted"
    assert outcome.state is not None
    assert outcome.state.revision_status == RevisionStatus.ACCEPTED
    assert outcome.report_path is not None and outcome.report_path.exists()
    assert report_calls == [(outcome.report_path, RevisionStatus.ACCEPTED)]
    assert outcome.metrics["review_calls"] == 1
    assert outcome.metrics["acceptance_status"] == 1
    assert not store.pending_analysis_path.exists()


def test_runner_keeps_pending_state_without_rendering(tmp_path):
    store = AnalysisStore(tmp_path / "pending")
    report_calls = []
    outcome = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        _contract(),
        _analyzer,
        human_decision="PENDING",
        render_report=lambda *args: report_calls.append(args),
    )

    assert outcome.status == "pending"
    assert outcome.state is not None
    assert outcome.state.revision_status == RevisionStatus.PENDING_REVIEW
    assert report_calls == []
    assert store.pending_analysis_path.exists()


def test_runner_keeps_accepted_state_when_report_rendering_fails(tmp_path):
    store = AnalysisStore(tmp_path / "artifact-failure")

    def render(*args):
        raise OSError("renderer unavailable")

    outcome = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        _contract(),
        _analyzer,
        human_decision="ACCEPT",
        render_report=render,
    )

    assert outcome.status == "accepted"
    assert outcome.artifact_status == "failed"
    assert "renderer unavailable" in (outcome.artifact_error or "")
    assert store.load_analysis().revision_status == RevisionStatus.ACCEPTED


def test_runner_rejects_without_rendering(tmp_path):
    store = AnalysisStore(tmp_path / "rejected")
    report_calls = []
    outcome = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        _contract(),
        _analyzer,
        human_decision="REJECT",
        render_report=lambda *args: report_calls.append(args),
    )

    assert outcome.status == "rejected"
    assert outcome.state is not None
    assert outcome.state.revision_status == RevisionStatus.REJECTED
    assert report_calls == []
    assert not store.pending_analysis_path.exists()


def test_runner_maps_engine_failures_without_persisting(tmp_path):
    store = AnalysisStore(tmp_path / "blocked")
    outcome = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        AnalysisInputContract(domain="runner", required_tables=("Missing",)),
        _analyzer,
    )

    assert outcome.status == "blocked_input"
    assert outcome.state is None
    assert not store.pending_analysis_path.exists()


def test_runner_reuses_existing_lifecycle_for_repeated_source_and_contract(tmp_path):
    store = AnalysisStore(tmp_path / "repeat")
    source = _source(tmp_path)
    first = WorkbookWorkflowRunner(store).run(source, _contract(), _analyzer, human_decision="ACCEPT")
    second = WorkbookWorkflowRunner(store).run(source, _contract(), _analyzer, human_decision="ACCEPT")

    assert first.status == second.status == "accepted"
    assert first.source_fingerprint == second.source_fingerprint
    assert first.contract_fingerprint == second.contract_fingerprint
    assert second.state is not None and second.state.revision > first.state.revision


def test_runner_preserves_explicit_empty_effective_contract(tmp_path):
    store = AnalysisStore(tmp_path / "explicit-empty")
    contract = AnalysisInputContract(domain="runner", required_tables=())

    outcome = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        contract,
        _analyzer,
        human_decision="REJECT",
    )

    assert outcome.status == "rejected"
    assert outcome.contract_fingerprint == contract.fingerprint


def test_runner_cancellation_settles_before_persistence(tmp_path):
    store = AnalysisStore(tmp_path / "cancelled")
    outcome = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        _contract(),
        _analyzer,
        human_decision="ACCEPT",
        cancel_check=lambda: True,
    )

    assert outcome.status == "cancelled"
    assert outcome.metrics["cancellation_settled"] == 1
    assert outcome.state is None
    assert not store.pending_analysis_path.exists()
    assert not store.analysis_path.exists()


def test_runner_retry_render_does_not_repeat_analysis_or_review(tmp_path, monkeypatch):
    store = AnalysisStore(tmp_path / "retry")
    analyzer_calls = 0
    review_calls = 0

    def analyzer(material, contract):
        nonlocal analyzer_calls
        analyzer_calls += 1
        return _analyzer(material, contract)

    import foresight_os.analysis.workbook_runner as runner_module

    original_review = runner_module.review_analysis_state

    def review(state):
        nonlocal review_calls
        review_calls += 1
        return original_review(state)

    monkeypatch.setattr(runner_module, "review_analysis_state", review)
    first = WorkbookWorkflowRunner(store).run(
        _source(tmp_path),
        _contract(),
        analyzer,
        human_decision="ACCEPT",
        render_report=lambda *args: (_ for _ in ()).throw(OSError("renderer unavailable")),
    )

    assert first.status == "accepted"
    assert first.artifact_status == "failed"
    assert analyzer_calls == 1
    assert review_calls == 1

    calls = []

    def retry_renderer(path, value, state):
        calls.append((path, value, state.revision))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("retry", encoding="utf-8")

    retried = WorkbookWorkflowRunner(store).retry_render(first, render_report=retry_renderer)

    assert retried.status == "accepted"
    assert retried.artifact_status == "accepted"
    assert retried.artifact_error is None
    assert retried.report_path is not None and retried.report_path.read_text(encoding="utf-8") == "retry"
    assert len(calls) == 1
    assert analyzer_calls == 1
    assert review_calls == 1
