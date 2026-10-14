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
