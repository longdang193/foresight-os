from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


INLINE_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REFERENCE_DEFINITION = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))")
REFERENCE_LINK = re.compile(r"(?<!!)\[([^\]]+)\](?:\[([^\]]*)\])")


def _target(value: str) -> str:
    value = value.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    return value.split()[0] if value else ""


def _is_ignored(value: str) -> bool:
    lowered = value.lower()
    return not value or value.startswith("#") or lowered.startswith(("http:", "https:", "mailto:"))


def _reference_targets(lines: list[str]) -> dict[str, str]:
    references: dict[str, str] = {}
    for line in lines:
        match = REFERENCE_DEFINITION.match(line)
        if match:
            references[match.group(1).strip().lower()] = _target(match.group(2) or match.group(3) or "")
    return references


def _links(lines: list[str]):
    references = _reference_targets(lines)
    for line_number, line in enumerate(lines, 1):
        for match in INLINE_LINK.finditer(line):
            yield line_number, _target(match.group(1))
        for match in REFERENCE_LINK.finditer(line):
            label = (match.group(2) or match.group(1)).strip().lower()
            target = references.get(label)
            if target is not None:
                yield line_number, target


def check_files(paths: list[Path], repo_root: Path | None = None) -> list[str]:
    root = (repo_root or Path.cwd()).resolve()
    errors: list[str] = []
    seen: set[Path] = set()
    for path in paths:
        source = path if path.is_absolute() else root / path
        source = source.resolve()
        if source in seen:
            continue
        seen.add(source)
        if not source.is_file():
            errors.append(f"{source}: file does not exist")
            continue
        lines = source.read_text(encoding="utf-8").splitlines()
        for line_number, raw_target in _links(lines):
            target = raw_target.split("#", 1)[0]
            if _is_ignored(raw_target) or _is_ignored(target):
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{source}:{line_number}: missing local target {raw_target}")
    return errors


def _tracked_docs(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--", "docs"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [root / line for line in result.stdout.splitlines() if line.lower().endswith(".md")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local Markdown links without network access.")
    parser.add_argument("paths", nargs="*", type=Path, help="Markdown files to inspect")
    parser.add_argument("--tracked-docs", action="store_true", help="also inspect every tracked Markdown file under docs/")
    args = parser.parse_args(argv)
    root = Path.cwd()
    paths = list(args.paths)
    if args.tracked_docs:
        paths.extend(_tracked_docs(root))
    if not paths:
        parser.error("at least one Markdown path or --tracked-docs is required")
    errors = check_files(paths, root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"checked {len({path.resolve() for path in paths})} Markdown path(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
