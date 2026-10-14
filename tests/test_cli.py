from pathlib import Path

from foresight_os.cli import main
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.capabilities import CapabilityUnavailableError
from foresight_os.wayfinding import create_work_brief


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
