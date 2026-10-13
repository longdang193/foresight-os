from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class PowerBIProjectError(ValueError):
    pass


@dataclass(frozen=True)
class PowerBIReadLimits:
    max_files: int = 1_000
    max_total_bytes: int = 50_000_000
    max_file_bytes: int = 10_000_000


@dataclass(frozen=True)
class PowerBIFile:
    relative_path: str
    kind: str
    size: int
    sha256: str


@dataclass(frozen=True)
class PowerBIProjectReadResult:
    source_path: str
    project_root: str
    format: str
    project_file: str
    source_sha256: str
    files: tuple[PowerBIFile, ...]
    tables: tuple[str, ...]
    measures: tuple[str, ...]
    relationships: tuple[str, ...]
    pages: tuple[str, ...]
    visual_count: int
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SUPPORTED_SUFFIXES = frozenset({".bim", ".json", ".pbip", ".pbir", ".tmdl"})
_TABLE_RE = re.compile(r"^\s*table\s+(?:'([^']+)'|([^\s\r\n]+))")
_MEASURE_RE = re.compile(r"^\s*measure\s+(?:'([^']+)'|([^\s=]+))\s*=")
_RELATIONSHIP_RE = re.compile(r"^\s*relationship(?:\s+(?:'([^']+)'|([^\s\r\n]+)))?")


def _identifier(match: re.Match[str]) -> str:
    return (match.group(1) or match.group(2) or "").strip()


def _find_project_file(source: Path) -> tuple[Path, Path, str]:
    if source.is_file():
        suffix = source.suffix.lower()
        if suffix not in {".pbip", ".pbir"}:
            raise PowerBIProjectError("Power BI input must be a .pbip or .pbir file")
        if suffix == ".pbip":
            return source.parent, source, "PBIP"
        for parent in (source.parent, *source.parents):
            candidates = sorted(parent.glob("*.pbip"))
            if candidates:
                return parent, candidates[0], "PBIP"
        return source.parent, source, "PBIR"
    if not source.is_dir():
        raise PowerBIProjectError("Power BI input path does not exist")
    pbip_files = sorted(source.glob("*.pbip"))
    if pbip_files:
        return source, pbip_files[0], "PBIP"
    pbir_files = sorted(source.glob("*.pbir"))
    if pbir_files:
        return source, pbir_files[0], "PBIR"
    raise PowerBIProjectError("Power BI directory must contain a .pbip or .pbir file")


def _iter_project_files(root: Path, limits: PowerBIReadLimits) -> tuple[PowerBIFile, ...]:
    resolved_root = root.resolve()
    discovered: list[PowerBIFile] = []
    total_bytes = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in _SUPPORTED_SUFFIXES:
            continue
        try:
            relative_path = path.resolve().relative_to(resolved_root).as_posix()
        except ValueError as error:
            raise PowerBIProjectError("Power BI project contains a path outside its root") from error
        size = path.stat().st_size
        if size > limits.max_file_bytes:
            raise PowerBIProjectError(f"Power BI file exceeds the per-file limit: {relative_path}")
        total_bytes += size
        if total_bytes > limits.max_total_bytes:
            raise PowerBIProjectError("Power BI project exceeds the total input limit")
        if len(discovered) >= limits.max_files:
            raise PowerBIProjectError("Power BI project exceeds the file-count limit")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        kind = path.suffix.lower().lstrip(".")
        if "visuals" in path.parts:
            kind = "visual"
        elif "pages" in path.parts:
            kind = "page"
        discovered.append(PowerBIFile(relative_path, kind, size, digest))
    if not discovered:
        raise PowerBIProjectError("Power BI project contains no supported definition files")
    return tuple(discovered)


def _parse_tmdl(path: Path) -> tuple[set[str], set[str], set[str]]:
    tables: set[str] = set()
    measures: set[str] = set()
    relationships: set[str] = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        for pattern, target in ((_TABLE_RE, tables), (_MEASURE_RE, measures), (_RELATIONSHIP_RE, relationships)):
            match = pattern.match(line)
            if match is None:
                continue
            identifier = _identifier(match)
            if pattern is _RELATIONSHIP_RE and not identifier:
                identifier = f"relationship:{len(relationships) + 1}"
            if identifier:
                target.add(identifier)
            break
    return tables, measures, relationships


def _parse_bim(value: Any) -> tuple[set[str], set[str], set[str]]:
    model = value.get("model", value) if isinstance(value, dict) else {}
    tables: set[str] = set()
    measures: set[str] = set()
    relationships: set[str] = set()
    for table in model.get("tables", []) if isinstance(model, dict) else []:
        if not isinstance(table, dict):
            continue
        if table.get("name"):
            tables.add(str(table["name"]))
        for measure in table.get("measures", []):
            if isinstance(measure, dict) and measure.get("name"):
                measures.add(str(measure["name"]))
    for relationship in model.get("relationships", []) if isinstance(model, dict) else []:
        if not isinstance(relationship, dict):
            continue
        name = relationship.get("name")
        if name:
            relationships.add(str(name))
        else:
            relationships.add(
                f"{relationship.get('fromTable', '?')}.{relationship.get('fromColumn', '?')}"
                f"->{relationship.get('toTable', '?')}.{relationship.get('toColumn', '?')}"
            )
    return tables, measures, relationships


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PowerBIProjectError(f"invalid Power BI JSON definition: {path.name}") from error


def _report_parts(files: tuple[PowerBIFile, ...]) -> tuple[tuple[str, ...], int]:
    pages: set[str] = set()
    visual_count = 0
    for item in files:
        parts = Path(item.relative_path).parts
        if "pages" in parts:
            page_index = parts.index("pages")
            if page_index + 1 < len(parts):
                pages.add(parts[page_index + 1])
        if item.kind == "visual":
            visual_count += 1
    return tuple(sorted(pages)), visual_count


def read_powerbi_project(source: Path | str, limits: PowerBIReadLimits | None = None) -> PowerBIProjectReadResult:
    """Read PBIP/PBIR definitions without executing DAX or loading model data."""
    resolved_source = Path(source)
    effective_limits = limits or PowerBIReadLimits()
    root, project_file, project_format = _find_project_file(resolved_source)
    project_definition = _read_json(project_file)
    if not isinstance(project_definition, dict):
        raise PowerBIProjectError("Power BI project definition must be a JSON object")
    files = _iter_project_files(root, effective_limits)
    tables: set[str] = set()
    measures: set[str] = set()
    relationships: set[str] = set()
    file_digests = hashlib.sha256()
    for item in files:
        file_digests.update(item.relative_path.encode("utf-8"))
        file_digests.update(b"\0")
        file_digests.update(item.sha256.encode("ascii"))
        path = root / Path(item.relative_path)
        if path.suffix.lower() == ".tmdl":
            parsed = _parse_tmdl(path)
        elif path.suffix.lower() in {".bim", ".json"} and (
            path.suffix.lower() == ".bim"
            or any(part.lower() in {"model", "semanticmodel", "semantic model"} for part in path.parts)
        ):
            parsed = _parse_bim(_read_json(path))
        else:
            continue
        tables.update(parsed[0])
        measures.update(parsed[1])
        relationships.update(parsed[2])
    pages, visual_count = _report_parts(files)
    limitations = (
        "metadata-only adapter; it does not extract PBIX binaries, execute DAX, or load model data",
        "report visuals are indexed by definition path; visual query results require a connected model boundary",
    )
    return PowerBIProjectReadResult(
        source_path=str(resolved_source),
        project_root=str(root),
        format=project_format,
        project_file=project_file.relative_to(root).as_posix(),
        source_sha256=file_digests.hexdigest(),
        files=files,
        tables=tuple(sorted(tables)),
        measures=tuple(sorted(measures)),
        relationships=tuple(sorted(relationships)),
        pages=pages,
        visual_count=visual_count,
        limitations=limitations,
    )
