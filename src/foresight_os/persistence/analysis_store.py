import json
import os
import tempfile
import uuid
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
    ResearchNeed,
    ResearchNeedKind,
    SourceLocator,
    WorkStage,
    WorkBrief,
)
from foresight_os.domain.challenge import ChallengeObjection, ObjectionDisposition, ReviewOutcome, ReviewRecord
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
    def pending_analysis_path(self) -> Path:
        return self.root / "analysis.pending.json"

    @property
    def pending_tokens_path(self) -> Path:
        return self.root / "analysis.pending.tokens.json"

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
        value = validate_work_brief(yaml.safe_load(frontmatter))
        stages = []
        for stage in value.get("stages", []):
            needs = []
            for need in stage.get("research_needs", []):
                kind = need["kind"]
                try:
                    kind = ResearchNeedKind(kind)
                except ValueError:
                    pass
                needs.append(ResearchNeed(kind, need["query"], need.get("source_hint")))
            stages.append(WorkStage(
                stage["stage_id"],
                stage["objective"],
                stage.get("participants", []),
                stage.get("subtasks", []),
                stage.get("dependencies", []),
                stage.get("expected_result", ""),
                needs,
                stage.get("skill_ids", []),
                stage.get("execution_pattern_override"),
                stage.get("limits", {}),
            ))
        return WorkBrief(**{**value, "stages": stages})

    def save_analysis(self, state: AnalysisState) -> None:
        value = validate_analysis(state)
        with FileLock(str(self.lock_path)):
            self._write_validated(value)

    def commit_revision(self, state: AnalysisState, expected_revision: int, accepted: bool) -> AnalysisState:
        with FileLock(str(self.lock_path)):
            current = self._load_path(self.analysis_path) if self.analysis_path.exists() else None
            pending = self._load_path(self.pending_analysis_path) if self.pending_analysis_path.exists() else None
            if pending is not None and state.revision != expected_revision:
                raise ValueError(f"stale pending revision: expected {expected_revision}, pending {state.revision}")
            if pending is not None and pending.revision != expected_revision:
                raise ValueError(f"stale pending snapshot: expected {expected_revision}, persisted {pending.revision}")
            if pending is not None and (not state.pending_token or state.pending_token != pending.pending_token):
                raise ValueError("stale pending identity")
            consumed_tokens = self._load_consumed_pending_tokens()
            if pending is None and state.pending_token and state.pending_token in consumed_tokens:
                raise ValueError("stale pending identity")
            if pending is None and current is not None and current.revision != expected_revision:
                raise ValueError(f"stale revision: expected {expected_revision}, current {current.revision}")
            if pending is not None and current is not None and not accepted:
                self._remember_consumed_pending_token(pending.pending_token)
                self.pending_analysis_path.unlink(missing_ok=True)
                return current
            status = RevisionStatus.ACCEPTED if accepted else RevisionStatus.REJECTED
            committed = replace(pending or state, revision_status=status, pending_token=None)
            if pending is not None and current is not None and accepted:
                committed = self._merge_states(current, committed)
            elif current is not None and current.revision_status != RevisionStatus.PENDING_REVIEW and committed.revision <= current.revision:
                number = current.revision + 1
                revision = Revision(
                    f"revision-{number}",
                    number,
                    "accepted mutation" if accepted else "rejected mutation",
                    [item.id for collection in [committed.evidence, committed.claims, committed.implications, committed.recommendations, committed.artifacts] for item in collection] + [item.id for item in committed.calculations],
                )
                committed = replace(committed, revision=number, revisions=[*current.revisions, revision])
            self._write_validated(validate_analysis(committed))
            if pending is not None:
                self._remember_consumed_pending_token(pending.pending_token)
            self.pending_analysis_path.unlink(missing_ok=True)
            return committed

    def save_pending(self, state: AnalysisState) -> AnalysisState:
        pending = replace(state, revision_status=RevisionStatus.PENDING_REVIEW, pending_token=uuid.uuid4().hex)
        with FileLock(str(self.lock_path)):
            current = self._load_path(self.analysis_path) if self.analysis_path.exists() else None
            existing_pending = self._load_path(self.pending_analysis_path) if self.pending_analysis_path.exists() else None
            if current is not None:
                number = current.revision + 1
                revision = Revision(
                    f"revision-{number}",
                    number,
                    "pending mutation",
                    [item.id for collection in [pending.evidence, pending.claims, pending.implications, pending.recommendations, pending.artifacts] for item in collection] + [item.id for item in pending.calculations],
                )
                pending = replace(pending, revision=number, revisions=[*current.revisions, revision])
                pending = self._merge_states(current, pending)
            self._write_validated(validate_analysis(pending), self.pending_analysis_path)
            if existing_pending is not None:
                self._remember_consumed_pending_token(existing_pending.pending_token)
        return pending

    def load_pending(self) -> AnalysisState:
        return self.load_analysis()

    def load_analysis(self) -> AnalysisState:
        path = self.pending_analysis_path if self.pending_analysis_path.exists() else self.analysis_path
        return self._load_path(path)

    def _load_path(self, path: Path) -> AnalysisState:
        value = migrate_analysis_dict(json.loads(path.read_text(encoding="utf-8")))
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
                tuple(item.get("assumptions", ())),
                tuple(item.get("uncertainty", ())),
                item.get("confidence_rationale", ""),
                tuple(item.get("disconfirmation_conditions", ())),
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
        review_records = [
            ReviewRecord(
                review_id=item["review_id"],
                target_ids=tuple(item.get("target_ids", ())),
                reviewed_state_revision=item["reviewed_state_revision"],
                input_fingerprint=item["input_fingerprint"],
                skill_ids=tuple(item.get("skill_ids", ())),
                skill_versions=tuple(item.get("skill_versions", ())),
                objections=tuple(
                    ChallengeObjection(
                        kind=objection["kind"],
                        target_id=objection["target_id"],
                        statement=objection["statement"],
                        evidence_ids=tuple(objection.get("evidence_ids", ())),
                        disposition=ObjectionDisposition(objection.get("disposition", "UNRESOLVED")),
                    )
                    for objection in item.get("objections", ())
                ),
                outcome=ReviewOutcome(item.get("outcome", "PROVISIONAL")),
                limitations=tuple(item.get("limitations", ())),
                unresolved_issues=tuple(item.get("unresolved_issues", ())),
            )
            for item in value.get("review_records", ())
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
            pending_token=value.get("pending_token"),
            review_records=review_records,
        )

    def _write_validated(self, value: dict, path: Path | None = None) -> None:
        self._atomic_write(path or self.analysis_path, json.dumps(value, indent=2) + "\n")

    def _load_consumed_pending_tokens(self) -> set[str]:
        if not self.pending_tokens_path.exists():
            return set()
        value = json.loads(self.pending_tokens_path.read_text(encoding="utf-8"))
        return {item for item in value if isinstance(item, str)} if isinstance(value, list) else set()

    def _remember_consumed_pending_token(self, token: str | None) -> None:
        if not token:
            return
        tokens = self._load_consumed_pending_tokens()
        tokens.add(token)
        self._atomic_write(self.pending_tokens_path, json.dumps(sorted(tokens), indent=2) + "\n")

    @staticmethod
    def _merge_states(current: AnalysisState, pending: AnalysisState) -> AnalysisState:
        def merge(items):
            result = list(items[0])
            seen = {getattr(item, "id", getattr(item, "review_id", None)) for item in result}
            for collection in items[1:]:
                for item in collection:
                    item_id = getattr(item, "id", getattr(item, "review_id", None))
                    if item_id not in seen:
                        result.append(item)
                        seen.add(item_id)
            return result

        return replace(
            pending,
            evidence=merge((current.evidence, pending.evidence)),
            claims=merge((current.claims, pending.claims)),
            implications=merge((current.implications, pending.implications)),
            recommendations=merge((current.recommendations, pending.recommendations)),
            artifacts=merge((current.artifacts, pending.artifacts)),
            relationships=merge((current.relationships, pending.relationships)),
            calculations=merge((current.calculations, pending.calculations)),
            review_records=merge((current.review_records, pending.review_records)),
            invalidation=current.invalidation,
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
