from pathlib import Path

import pytest

from foresight_os.runtime.local_adapters import (
    LocalArtifactGenerationCapability,
    LocalDocumentReadCapability,
    bind_local_adapters,
)
from foresight_os.runtime.capabilities import prepare_capability_context
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


def test_document_reader_returns_bounded_content_and_provenance(tmp_path: Path):
    source = tmp_path / "task.md"
    source.write_text("# NCC\n" + ("evidence " * 100), encoding="utf-8")

    result = LocalDocumentReadCapability((tmp_path,))("task.md", max_chars=32)

    assert result["path"] == "task.md"
    assert result["content"].startswith("# NCC")
    assert result["truncated"] is True
    assert len(result["content"]) == 32
    assert len(result["sha256"]) == 64


def test_document_reader_rejects_paths_outside_approved_roots(tmp_path: Path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside.md"
    allowed.mkdir()
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError, match="approved document root"):
        LocalDocumentReadCapability((allowed,))(str(outside))


def test_artifact_generator_writes_only_under_workspace(tmp_path: Path):
    capability = LocalArtifactGenerationCapability(tmp_path)

    result = capability("ncc-brief", "# Draft\n", artifact_type="markdown")

    artifact = tmp_path / "artifacts" / "ncc-brief.md"
    assert artifact.read_text(encoding="utf-8") == "# Draft\n"
    assert result["path"] == "artifacts/ncc-brief.md"
    assert result["status"] == "PROVISIONAL"
    assert len(result["sha256"]) == 64

    with pytest.raises(ValueError, match="workspace"):
        capability("../escape", "bad")


def test_prepare_capability_context_activates_local_adapters_for_approved_run(tmp_path: Path):
    context = prepare_capability_context(
        ("document_read", "artifact_generation"),
        {"local_workspace": tmp_path},
        human_approved=True,
    )

    assert all(item.available for item in context["capability_resolutions"].values())
    assert context["capability_resolutions"]["document_read"].decision.value == "ADAPT_AT_BOUNDARY"
    assert context["capability_resolutions"]["artifact_generation"].decision.value == "ADAPT_AT_BOUNDARY"


def test_artifact_generation_remains_denied_without_human_approval(tmp_path: Path):
    with pytest.raises(RuntimeError, match="human approval"):
        prepare_capability_context(
            ("artifact_generation",),
            {"local_workspace": tmp_path},
            human_approved=False,
        )


def test_bind_local_adapters_requires_workspace(tmp_path: Path):
    bindings = bind_local_adapters(tmp_path, document_roots=(tmp_path,))

    assert set(bindings) == {"document_read", "artifact_generation"}


def test_agent_factory_documents_local_adapter_boundaries(tmp_path: Path):
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    context = prepare_capability_context(
        ("document_read", "artifact_generation"),
        {"local_workspace": tmp_path},
        human_approved=True,
    )
    AgentFactory(Client()).create(
        ParticipantConfig("analyst", "analyst", "read and draft", capability_ids=("document_read", "artifact_generation")),
        context,
    )

    assert "approved local source root" in captured["instructions"]
    assert "provisional local outputs" in captured["instructions"]
