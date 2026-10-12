import json
import os
import tempfile
from pathlib import Path

import yaml

from foresight_os.domain.models import (
    AnalysisState,
    AnalyticalRecord,
    Artifact,
    Assessment,
    Basis,
    Evidence,
    Invalidation,
    Lifecycle,
    Relationship,
    Revision,
    SourceLocator,
    WorkBrief,
)
from foresight_os.domain.validation import validate_analysis, validate_work_brief


class AnalysisStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    @property
    def brief_path(self) -> Path:
        return self.root / "brief.md"

    @property
    def analysis_path(self) -> Path:
        return self.root / "analysis.json"

    def save_brief(self, brief: WorkBrief) -> None:
        value = validate_work_brief(brief)
        body = "# Work Brief\n\n" + value["current_direction"] + "\n"
        text = "---\n" + yaml.safe_dump(value, sort_keys=False) + "---\n\n" + body
        self._atomic_write(self.brief_path, text)

    def load_brief(self) -> WorkBrief:
        text = self.brief_path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError("brief.md must contain YAML front matter")
        frontmatter = text[4:].split("\n---\n", 1)[0]
        return WorkBrief(**validate_work_brief(yaml.safe_load(frontmatter)))

    def save_analysis(self, state: AnalysisState) -> None:
        value = validate_analysis(state)
        self._atomic_write(self.analysis_path, json.dumps(value, indent=2) + "\n")

    def load_analysis(self) -> AnalysisState:
        value = validate_analysis(json.loads(self.analysis_path.read_text(encoding="utf-8")))
        evidence = [
            Evidence(
                item["id"],
                SourceLocator(**item["source_locator"]),
                item["version"],
                item["date"],
                item["excerpt"],
                item["limitations"],
            )
            for item in value["evidence"]
        ]

        def record(item: dict) -> AnalyticalRecord:
            return AnalyticalRecord(
                item["id"],
                item["statement"],
                Basis(item["basis"]),
                Assessment(item["assessment"]),
                Lifecycle(item["lifecycle"]),
                item["evidence_ids"],
                item["relationship_ids"],
            )

        return AnalysisState(
            value["investigation_id"],
            value["revision"],
            evidence,
            [record(item) for item in value["claims"]],
            [record(item) for item in value["implications"]],
            [record(item) for item in value["recommendations"]],
            [
                Artifact(
                    item["id"],
                    item["kind"],
                    item["path"],
                    Lifecycle(item["lifecycle"]),
                    item["relationship_ids"],
                )
                for item in value["artifacts"]
            ],
            [Relationship(**item) for item in value["relationships"]],
            [Revision(**item) for item in value["revisions"]],
            Invalidation(**value["invalidation"]),
        )

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            Path(temporary).replace(path)
        finally:
            temporary_path = Path(temporary)
            if temporary_path.exists():
                temporary_path.unlink()
