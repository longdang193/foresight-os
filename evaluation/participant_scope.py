from __future__ import annotations

from pathlib import Path


class ParticipantScope:
    def __init__(self, allowed_root: Path, denied_paths: tuple[Path, ...] = ()) -> None:
        self.allowed_root = Path(allowed_root).resolve()
        self.denied_paths = tuple(Path(item).resolve() for item in denied_paths)

    def resolve(self, path: Path | str) -> Path:
        candidate = Path(path).resolve()
        try:
            candidate.relative_to(self.allowed_root)
        except ValueError as error:
            raise PermissionError(f"participant path is outside allowlisted root: {candidate}") from error
        if any(candidate == denied or denied in candidate.parents for denied in self.denied_paths):
            raise PermissionError(f"participant path is denied: {candidate}")
        return candidate

    def read_bytes(self, path: Path | str) -> bytes:
        return self.resolve(path).read_bytes()

    def exists(self, path: Path | str) -> bool:
        return self.resolve(path).exists()
