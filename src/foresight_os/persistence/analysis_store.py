import json
import os
import tempfile
from pathlib import Path

import yaml
from dataclasses import replace
from filelock import FileLock

from foresight_os.domain.models import (
    AnalysisState,
    AnalyticalRecord,
    Artifact,
    Assessment,
    Basis,
    Evidence,
    CalculationRecord,
    Invalidation,
    Lifecycle,
    Relationship,
    Revision,
    RevisionStatus,
    MeasurementKey,
    SourceLocator,
    WorkBrief,
)
from foresight_os.domain.validation import migrate_analysis_dict, validate_analysis, validate_work_brief


class AnalysisStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    @property
    def brief_path(self) -> Path:
        return self.root / "brief.md"

    @property
    def analysis_path(self) -> Path:
        return self.root / "analysis.json"

    @property
    def lock_path(self) -> Path:
        return self.root / ".analysis.lock"

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
        with FileLock(str(self.lock_path)):
            self._write_validated(value)

    def commit_revision(self, state: AnalysisState, expected_revision: int, accepted: bool) -> AnalysisState:
        with FileLock(str(self.lock_path)):
            current = self.load_analysis() if self.analysis_path.exists() else None
            if current is not None and current.revision != expected_revision:
                raise ValueError(f"stale revision: expected {expected_revision}, current {current.revision}")
            status = RevisionStatus.ACCEPTED if accepted else RevisionStatus.REJECTED
            committed = replace(state, revision_status=status)
            if current is not None and committed.revision <= current.revision and current.revision_status != RevisionStatus.PENDING_REVIEW:
                number = current.revision + 1
                revision = Revision(
                    f"revision-{number}",
                    number,
                    "accepted mutation",
                    [item.id for collection in [committed.evidence, committed.claims, committed.implications, committed.recommendations, committed.artifacts] for item in collection],
                )
                committed = replace(committed, revision=number, revisions=[*current.revisions, revision])
            self._write_validated(validate_analysis(committed))
            return committed

    def save_pending(self, state: AnalysisState) -> AnalysisState:
        pending = replace(state, revision_status=RevisionStatus.PENDING_REVIEW)
        with FileLock(str(self.lock_path)):
            self._write_validated(validate_analysis(pending))
        return pending

    def load_analysis(self) -> AnalysisState:
        value = migrate_analysis_dict(json.loads(self.analysis_path.read_text(encoding="utf-8")))
        value = validate_analysis(value)
        evidence = [
            Evidence(
                item["id"],
                SourceLocator(**item["source_locator"]),
                item["version"],
                item["date"],
                item["excerpt"],
                item["limitations"],
                MeasurementKey(**item["measurement_key"]) if item.get("measurement_key") else None,
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

        calculations = [
            CalculationRecord(
                item["id"],
                MeasurementKey(**item["key"]),
                item["formula"],
                item["input_ids"],
                item["output"],
                item["units"],
                item["source_locators"],
            )
            for item in value.get("calculations", [])
        ]
        return AnalysisState(
            investigation_id=value["investigation_id"],
            revision=value["revision"],
            evidence=evidence,
            claims=[record(item) for item in value["claims"]],
            implications=[record(item) for item in value["implications"]],
            recommendations=[record(item) for item in value["recommendations"]],
            artifacts=[
                Artifact(
                    item["id"],
                    item["kind"],
                    item["path"],
                    Lifecycle(item["lifecycle"]),
                    item["relationship_ids"],
                )
                for item in value["artifacts"]
            ],
            relationships=[Relationship(**item) for item in value["relationships"]],
            revisions=[Revision(**item) for item in value["revisions"]],
            invalidation=Invalidation(**value["invalidation"]),
            schema_version=value["schema_version"],
            revision_status=RevisionStatus(value["revision_status"]),
            calculations=calculations,
        )

    def _write_validated(self, value: dict) -> None:
        self._atomic_write(self.analysis_path, json.dumps(value, indent=2) + "\n")

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
