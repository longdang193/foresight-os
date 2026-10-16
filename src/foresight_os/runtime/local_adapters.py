from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping
import zipfile
import xml.etree.ElementTree as ET

from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityBindingKind, CapabilityOwnership


_DOCUMENT_EXTENSIONS = {".csv", ".json", ".md", ".txt", ".xml", ".yaml", ".yml"}
_ARTIFACT_TYPES = {
    "json": ".json",
    "markdown": ".md",
    "text": ".txt",
}
_MAX_DOCUMENT_BYTES = 2_000_000
_MAX_DOCUMENT_CHARS = 100_000
_MAX_ARTIFACT_BYTES = 2_000_000


def _resolved_roots(roots: Iterable[str | Path]) -> tuple[Path, ...]:
    resolved = tuple(dict.fromkeys(Path(root).expanduser().resolve() for root in roots))
    if not resolved:
        raise ValueError("at least one approved document root is required")
    return resolved


def _resolve_under_roots(path: str | Path, roots: tuple[Path, ...]) -> tuple[Path, Path]:
    candidate = Path(path).expanduser()
    candidates = (candidate,) if candidate.is_absolute() else tuple(root / candidate for root in roots)
    for item in candidates:
        resolved = item.resolve()
        for root in roots:
            if resolved == root or root in resolved.parents:
                return resolved, root
    raise ValueError("document path is outside the approved document root(s)")


def _read_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            document = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as error:
        raise ValueError("document is not a readable DOCX file") from error
    root = ET.fromstring(document)
    paragraphs: list[str] = []
    for paragraph in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        text = "".join(node.text or "" for node in paragraph.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


class LocalDocumentReadCapability:
    def __init__(self, roots: Iterable[str | Path], *, max_bytes: int = _MAX_DOCUMENT_BYTES) -> None:
        self.roots = _resolved_roots(roots)
        self.max_bytes = max(1, int(max_bytes))

    def __call__(self, path: str, max_chars: int = 12_000) -> dict[str, Any]:
        source, display_root = _resolve_under_roots(path, self.roots)
        if not source.is_file():
            raise ValueError("document path does not identify a file")
        if source.stat().st_size > self.max_bytes:
            raise ValueError("document exceeds the local reader byte limit")
        suffix = source.suffix.lower()
        if suffix == ".docx":
            content = _read_docx(source)
        elif suffix in _DOCUMENT_EXTENSIONS:
            content = source.read_text(encoding="utf-8")
        else:
            raise ValueError(f"unsupported document format: {suffix or '<none>'}")
        limit = min(max(1, int(max_chars)), _MAX_DOCUMENT_CHARS)
        truncated = len(content) > limit
        return {
            "path": source.relative_to(display_root).as_posix(),
            "content": content[:limit],
            "content_type": suffix.lstrip(".") or "text",
            "bytes": source.stat().st_size,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "truncated": truncated,
        }


class LocalArtifactGenerationCapability:
    def __init__(self, workspace: str | Path, *, max_bytes: int = _MAX_ARTIFACT_BYTES) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.max_bytes = max(1, int(max_bytes))

    def __call__(self, name: str, content: str | Mapping[str, Any], artifact_type: str = "text") -> dict[str, Any]:
        kind = str(artifact_type).lower()
        if kind not in _ARTIFACT_TYPES:
            raise ValueError(f"unsupported local artifact type: {kind}")
        relative = Path("artifacts") / Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("artifact path must stay inside the workspace")
        if relative.suffix.lower() != _ARTIFACT_TYPES[kind]:
            relative = relative.with_suffix(_ARTIFACT_TYPES[kind])
        target = (self.workspace / relative).resolve()
        if target != self.workspace and self.workspace not in target.parents:
            raise ValueError("artifact path must stay inside the workspace")
        if isinstance(content, Mapping):
            rendered = json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        else:
            rendered = str(content)
        payload = rendered.encode("utf-8")
        if len(payload) > self.max_bytes:
            raise ValueError("artifact exceeds the local generation byte limit")
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".artifact-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return {
            "path": target.relative_to(self.workspace).as_posix(),
            "status": "PROVISIONAL",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "artifact_type": kind,
        }


def bind_local_adapters(
    workspace: str | Path,
    *,
    document_roots: Iterable[str | Path] | None = None,
) -> dict[str, CapabilityBinding]:
    workspace_path = Path(workspace).expanduser().resolve()
    roots = tuple(document_roots or (workspace_path,))
    return {
        "document_read": CapabilityBinding(
            LocalDocumentReadCapability(roots),
            kind=CapabilityBindingKind.TOOL,
            ownership=CapabilityOwnership.OWNED,
            fingerprint="local-document-reader-v1",
        ),
        "artifact_generation": CapabilityBinding(
            LocalArtifactGenerationCapability(workspace_path),
            kind=CapabilityBindingKind.TOOL,
            ownership=CapabilityOwnership.OWNED,
            fingerprint="local-artifact-generation-v1",
        ),
    }
