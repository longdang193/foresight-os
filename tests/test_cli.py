from pathlib import Path
import json

from types import SimpleNamespace

import openpyxl

from foresight_os.cli import main
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.capabilities import CapabilityUnavailableError
from foresight_os.wayfinding import create_work_brief


def _xlsx(path: Path) -> None:
    workbook = openpyxl.Workbook()
    workbook.active.title = "Data"
    workbook.active.append(["Value"])
    workbook.save(path)


def test_analyze_xlsx_requires_explicit_or_single_brief_domain(tmp_path: Path, capsys):
    workbook = tmp_path / "input.xlsx"
    _xlsx(workbook)

    assert main(["analyze", "--workbook", str(workbook), "--work-dir", str(tmp_path / "case")]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED_INPUT"


def test_analyze_xlsx_dispatches_explicit_domain_without_filename_guessing(tmp_path: Path, capsys, monkeypatch):
    workbook = tmp_path / "arbitrary-name.xlsx"
    _xlsx(workbook)
    seen = {}

    def fake_workflow(store, source, **kwargs):
        seen.update({"source": source, **kwargs})
        return SimpleNamespace(status="accepted", failure=None)

    monkeypatch.setattr("foresight_os.cli.run_portfolio_resilience_workflow", fake_workflow)

    assert main([
        "analyze",
        "--workbook",
        str(workbook),
        "--work-dir",
        str(tmp_path / "case"),
        "--domain",
        "portfolio_resilience",
        "--accept",
    ]) == 0
    assert json.loads(capsys.readouterr().out) == {"accepted": True, "status": "accepted"}
    assert seen["source"] == workbook
    assert seen["human_decision"] == "ACCEPT"


def test_brief_command_renders_only_human_body_without_creating_state(tmp_path: Path, capsys):
    work_dir = tmp_path / "brief-command"
    store = AnalysisStore(work_dir)
    store.save_brief(create_work_brief("Question", investigation_id="brief-command"))
    before = {path.relative_to(work_dir) for path in work_dir.rglob("*") if path.is_file()}

    assert main(["brief", "--work-dir", str(work_dir)]) == 0
    output = capsys.readouterr().out

    after = {path.relative_to(work_dir) for path in work_dir.rglob("*") if path.is_file()}
    assert output.startswith("# Work Brief")
    assert not output.startswith("---")
    assert "Generated from the canonical WorkBrief fields." in output
    assert before == after


def test_execute_requires_explicit_provider_configuration(tmp_path: Path, capsys):
    work_dir = tmp_path / "execute-command"

    assert main([
        "execute",
        "--work-dir",
        str(work_dir),
        "--prompt",
        "run",
        "--env-file",
        str(tmp_path / "missing.env"),
        "--config-file",
        str(tmp_path / "missing.toml"),
    ]) == 2
    output = capsys.readouterr().out

    assert '"status": "BLOCKED_EXTERNAL"' in output
    assert "missing.toml" not in output


def test_execute_reports_unavailable_capability_without_traceback(tmp_path: Path, capsys, monkeypatch):
    async def blocked(*args, **kwargs):
        raise CapabilityUnavailableError("participant analyst capabilities unavailable")

    monkeypatch.setattr("foresight_os.cli.build_configured_client", lambda *args: object())
    monkeypatch.setattr("foresight_os.cli.execute_approved_investigation", blocked)

    assert main([
        "execute",
        "--work-dir",
        str(tmp_path / "execute-command"),
        "--prompt",
        "run",
    ]) == 2
    output = capsys.readouterr().out

    assert output.strip() == '{"status": "BLOCKED_EXTERNAL", "error": "required capability is unavailable"}'


def test_execute_reports_distinct_statuses_without_inferring_completion(tmp_path: Path, capsys, monkeypatch):
    class Metrics:
        settled = True
        runtime_status = "SETTLED"
        persistence_status = "PERSISTED"
        analysis_status = "PENDING_REVIEW"
        deliverable_status = {"executive report": "NOT_STARTED"}

    class Result:
        run_id = "run-1"
        outputs = ("output",)
        metrics = Metrics()

    async def completed(*args, **kwargs):
        return Result()

    monkeypatch.setattr("foresight_os.cli.build_configured_client", lambda *args: object())
    monkeypatch.setattr("foresight_os.cli.execute_approved_investigation", completed)

    assert main(["execute", "--work-dir", str(tmp_path), "--prompt", "run"]) == 0
    output = capsys.readouterr().out
    assert '"runtime_status": "SETTLED"' in output
    assert '"analysis_status": "PENDING_REVIEW"' in output
    assert '"deliverable_status": {"executive report": "NOT_STARTED"}' in output
    assert '"complete"' not in output


def test_execute_builds_configured_client_once(tmp_path: Path, capsys, monkeypatch):
    calls = 0

    class Metrics:
        settled = True
        runtime_status = "SETTLED"
        persistence_status = "NOT_STARTED"
        analysis_status = "NOT_STARTED"
        deliverable_status = {}

    class Result:
        run_id = "run-once"
        outputs = ()
        metrics = Metrics()

    def build_client(*args):
        nonlocal calls
        calls += 1
        return object()

    async def completed(*args, **kwargs):
        return Result()

    monkeypatch.setattr("foresight_os.cli.build_configured_client", build_client)
    monkeypatch.setattr("foresight_os.cli.execute_approved_investigation", completed)

    assert main(["execute", "--work-dir", str(tmp_path), "--prompt", "run"]) == 0
    capsys.readouterr()

    assert calls == 1


def test_execute_binds_web_search_provider_from_env_file(tmp_path: Path, capsys, monkeypatch):
    env_file = tmp_path / "runtime.env"
    env_file.write_text(
        "FORESIGHT_WEB_SEARCH_PROVIDER=searxng\n"
        "FORESIGHT_WEB_SEARCH_URL=http://127.0.0.1:8888\n",
        encoding="utf-8",
    )
    seen = {}

    class Metrics:
        settled = True
        runtime_status = "SETTLED"
        persistence_status = "NOT_STARTED"
        analysis_status = "NOT_STARTED"
        deliverable_status = {}

    class Result:
        run_id = "run-web-search"
        outputs = ()
        metrics = Metrics()

    def build_client(*args):
        return object()

    async def completed(*args, **kwargs):
        seen.update(kwargs)
        return Result()

    monkeypatch.setattr("foresight_os.cli.build_configured_client", build_client)
    monkeypatch.setattr("foresight_os.cli.execute_approved_investigation", completed)

    assert main([
        "execute",
        "--work-dir",
        str(tmp_path / "execute-command"),
        "--prompt",
        "run",
        "--env-file",
        str(env_file),
    ]) == 0
    capsys.readouterr()

    assert type(seen["run_context"]["web_search_provider"]).__name__ == "SearxngWebSearchProvider"
