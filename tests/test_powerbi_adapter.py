import json
from pathlib import Path

import pytest

from foresight_os.analysis.powerbi import PowerBIProjectError, PowerBIReadLimits, read_powerbi_project
from foresight_os.runtime.local_toolbelt import bind_local_toolbelt


def _write_project(root: Path) -> Path:
    project_file = root / "Demo.pbip"
    project_file.write_text(json.dumps({"version": "1.0", "artifacts": []}), encoding="utf-8")
    report_root = root / "Demo.Report" / "definition" / "pages" / "Overview" / "visuals" / "VisualA"
    report_root.mkdir(parents=True)
    (root / "Demo.Report" / "definition.pbir").write_text(json.dumps({"datasetReference": {"byPath": {"path": "../Demo.SemanticModel"}}}), encoding="utf-8")
    (report_root / "visual.json").write_text(json.dumps({"name": "VisualA", "singleVisual": {}}), encoding="utf-8")
    model_root = root / "Demo.SemanticModel" / "definition"
    model_root.mkdir(parents=True)
    (model_root / "model.tmdl").write_text(
        "table 'Sales'\n    measure 'Total Sales' = SUM(Sales[Amount])\nrelationship SalesToDate\n",
        encoding="utf-8",
    )
    return project_file


def test_reads_pbip_metadata_with_deterministic_provenance(tmp_path: Path):
    project_file = _write_project(tmp_path)

    result = read_powerbi_project(project_file)

    assert result.format == "PBIP"
    assert result.project_file == "Demo.pbip"
    assert result.tables == ("Sales",)
    assert result.measures == ("Total Sales",)
    assert result.relationships == ("SalesToDate",)
    assert result.pages == ("Overview",)
    assert result.visual_count == 1
    assert len(result.source_sha256) == 64
    assert "metadata-only" in result.limitations[0]
    assert result.to_dict()["files"]


def test_reads_pbir_when_no_pbip_project_is_available(tmp_path: Path):
    report = tmp_path / "Report" / "definition.pbir"
    report.parent.mkdir()
    report.write_text(json.dumps({"datasetReference": {"byConnection": {}}}), encoding="utf-8")

    result = read_powerbi_project(report)

    assert result.format == "PBIR"
    assert result.project_file == "definition.pbir"


def test_rejects_unsupported_or_unbounded_inputs(tmp_path: Path):
    unsupported = tmp_path / "report.pbix"
    unsupported.write_bytes(b"not supported")
    with pytest.raises(PowerBIProjectError, match=".pbip or .pbir"):
        read_powerbi_project(unsupported)

    project_file = _write_project(tmp_path)
    with pytest.raises(PowerBIProjectError, match="per-file limit"):
        read_powerbi_project(project_file, limits=PowerBIReadLimits(max_file_bytes=1))


def test_local_toolbelt_exposes_powerbi_reader():
    assert "powerbi_project_read" in bind_local_toolbelt()
