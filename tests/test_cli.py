from pathlib import Path

from foresight_os.cli import main
from foresight_os.persistence.analysis_store import AnalysisStore
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
