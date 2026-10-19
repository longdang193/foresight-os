import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Mapping

import yaml
from dataclasses import asdict, dataclass, replace
from filelock import FileLock

from foresight_os.domain.models import (
    AnalysisState,
    AnalyticalRecord,
    Artifact,
    Assessment,
    Basis,
    Evidence,
    CalculationRecord,
    CalculationVerificationStatus,
    Invalidation,
    Lifecycle,
    Relationship,
    Revision,
    RevisionStatus,
    MeasurementKey,
    MethodProvenance,
    ResearchNeed,
    ResearchNeedKind,
    SourceLocator,
    WorkStage,
    WorkBrief,
    ExecutionIntent,
)
from foresight_os.domain.approval import ApprovalRecord
from foresight_os.artifacts.brief import render_work_brief_markdown
from foresight_os.controller.recipes import ExecutionRecipe
from foresight_os.domain.challenge import ChallengeObjection, ObjectionDisposition, ReviewCheckResult, ReviewOutcome, ReviewRecord, ReviewSlotStatus
from foresight_os.domain.validation import migrate_analysis_dict, validate_analysis, validate_approval_record, validate_execution_recipe, validate_work_brief
from foresight_os.persistence.ids import canonical_json_hash


@dataclass(frozen=True)
class StageReceipt:
    stage_id: str
    input_fingerprint: str
    execution_policy_fingerprint: str = ""
    skill_hashes: tuple[str, ...] = ()
    capability_fingerprints: tuple[str, ...] = ()
    model_config_fingerprint: str = ""
    authorization_scope_fingerprint: str = ""
    result_references: tuple[str, ...] = ()
    result_hashes: tuple[str, ...] = ()
    status: str = "incomplete"
    committed: bool = False
    provenance_complete: bool = False
    source_revision: str = ""
    created_at: str = ""
    reuse_decision: str = "reuse"
    analyzer_fingerprints: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "StageReceipt":
        return cls(
            stage_id=str(value["stage_id"]),
            input_fingerprint=str(value["input_fingerprint"]),
            execution_policy_fingerprint=str(value.get("execution_policy_fingerprint", "")),
            skill_hashes=tuple(value.get("skill_hashes", ())),
            capability_fingerprints=tuple(value.get("capability_fingerprints", ())),
            model_config_fingerprint=str(value.get("model_config_fingerprint", "")),
            authorization_scope_fingerprint=str(value.get("authorization_scope_fingerprint", "")),
            analyzer_fingerprints=tuple(
                (str(domain), str(fingerprint))
                for domain, fingerprint in dict(value.get("analyzer_fingerprints", {})).items()
            ),
            result_references=tuple(value.get("result_references", ())),
            result_hashes=tuple(value.get("result_hashes", ())),
            status=str(value.get("status", "incomplete")),
            committed=bool(value.get("committed", False)),
            provenance_complete=bool(value.get("provenance_complete", False)),
            source_revision=str(value.get("source_revision", "")),
            created_at=str(value.get("created_at", "")),
            reuse_decision=str(value.get("reuse_decision", "reuse")),
        )

    def reusable(self) -> bool:
        return self.status == "committed" and self.committed and self.provenance_complete and bool(self.result_references) and bool(self.result_hashes)

    def reusable_for(
        self,
        *,
        input_fingerprint: str,
        source_revision: str | None = None,
        execution_policy_fingerprint: str = "",
        skill_hashes: tuple[str, ...] = (),
        capability_fingerprints: tuple[str, ...] = (),
        model_config_fingerprint: str = "",
        authorization_scope_fingerprint: str = "",
        analyzer_fingerprints: tuple[tuple[str, str], ...] = (),
        result_hashes: tuple[str, ...] = (),
    ) -> bool:
        return bool(
            self.reusable()
            and self.input_fingerprint == input_fingerprint
            and self.execution_policy_fingerprint == execution_policy_fingerprint
            and self.skill_hashes == tuple(skill_hashes)
            and self.capability_fingerprints == tuple(capability_fingerprints)
            and self.model_config_fingerprint == model_config_fingerprint
            and self.authorization_scope_fingerprint == authorization_scope_fingerprint
            and self.analyzer_fingerprints == tuple(analyzer_fingerprints)
            and (source_revision in (None, "") or self.source_revision == source_revision)
            and (not result_hashes or self.result_hashes == tuple(result_hashes))
        )


@dataclass(frozen=True)
class LoadedRecipe:
    raw: dict[str, object]
    recipe: ExecutionRecipe
    persisted_fingerprint: str


@dataclass
class AnalysisStoreStats:
    load_count: int = 0
    load_time_ms: float = 0.0
    merge_count: int = 0
    merge_time_ms: float = 0.0
    validation_count: int = 0
    validation_time_ms: float = 0.0
    pending_write_count: int = 0
    pending_write_bytes: int = 0
    pending_write_time_ms: float = 0.0
    committed_write_count: int = 0
    committed_write_bytes: int = 0
    committed_write_time_ms: float = 0.0
    review_attach_count: int = 0
    review_attach_time_ms: float = 0.0
    receipt_write_count: int = 0
    receipt_write_time_ms: float = 0.0


class AnalysisStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.stats = AnalysisStoreStats()

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
    def stage_receipts_path(self) -> Path:
        return self.root / "stage-receipts.json"

    @property
    def execution_recipe_path(self) -> Path:
        return self.root / "execution-recipe.json"

    @property
    def execution_approval_path(self) -> Path:
        return self.root / "execution-approval.json"

    @property
    def lock_path(self) -> Path:
        return self.root / ".analysis.lock"

    def save_brief(self, brief: WorkBrief) -> None:
        value = validate_work_brief(brief)
        body = render_work_brief_markdown(value)
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
                ExecutionIntent(**{
                    **stage["execution_intent"],
                    "required_patterns": tuple(stage["execution_intent"].get("required_patterns", ())),
                    "preferred_patterns": tuple(stage["execution_intent"].get("preferred_patterns", ())),
                    "required_participants": tuple(stage["execution_intent"].get("required_participants", ())),
                    "preferred_participants": tuple(stage["execution_intent"].get("preferred_participants", ())),
                    "required_capabilities": tuple(stage["execution_intent"].get("required_capabilities", ())),
                    "preferred_capabilities": tuple(stage["execution_intent"].get("preferred_capabilities", ())),
                }) if stage.get("execution_intent") else None,
            ))
        intent_value = value.get("execution_intent")
        execution_intent = None
        if intent_value:
            execution_intent = ExecutionIntent(
                required_patterns=tuple(intent_value.get("required_patterns", ())),
                preferred_patterns=tuple(intent_value.get("preferred_patterns", ())),
                required_participants=tuple(intent_value.get("required_participants", ())),
                preferred_participants=tuple(intent_value.get("preferred_participants", ())),
                required_capabilities=tuple(intent_value.get("required_capabilities", ())),
                preferred_capabilities=tuple(intent_value.get("preferred_capabilities", ())),
                preferred_reasoning_controls=dict(intent_value.get("preferred_reasoning_controls", {})),
                source=str(intent_value.get("source", "user")),
            )
        producer_value = value.get("producer")
        producer = MethodProvenance(**producer_value) if producer_value else None
        analysis_inputs = (
            [dict(item) for item in value.get("analysis_inputs", ())]
            if "analysis_inputs" in value
            else {}
        )
        return WorkBrief(**{
            **value,
            "stages": stages,
            "analysis_inputs": analysis_inputs,
            "execution_intent": execution_intent,
            "producer": producer,
        })

    def save_recipe(self, recipe: ExecutionRecipe) -> None:
        value = validate_execution_recipe(recipe)
        with FileLock(str(self.lock_path)):
            self._atomic_write(self.execution_recipe_path, json.dumps(value, sort_keys=True, indent=2, default=str) + "\n")

    def load_recipe(self) -> ExecutionRecipe:
        return self.load_recipe_bundle().recipe

    def load_recipe_bundle(self) -> LoadedRecipe:
        raw = json.loads(self.execution_recipe_path.read_text(encoding="utf-8"))
        value = validate_execution_recipe(raw)
        return LoadedRecipe(
            raw=raw,
            recipe=ExecutionRecipe.from_dict(value),
            persisted_fingerprint=canonical_json_hash(raw),
        )

    def save_execution_approval(self, approval: ApprovalRecord) -> None:
        value = validate_approval_record(approval)
        with FileLock(str(self.lock_path)):
            self._atomic_write(self.execution_approval_path, json.dumps(value, sort_keys=True, indent=2, default=str) + "\n")

    def load_execution_approval(self) -> ApprovalRecord | None:
        if not self.execution_approval_path.exists():
            return None
        value = validate_approval_record(json.loads(self.execution_approval_path.read_text(encoding="utf-8")))
        return ApprovalRecord.from_dict(value)

    def load_stage_receipts(self) -> dict[str, StageReceipt]:
        if not self.stage_receipts_path.exists():
            return {}
        value = json.loads(self.stage_receipts_path.read_text(encoding="utf-8"))
        return {key: StageReceipt.from_dict(item) for key, item in value.get("receipts", {}).items()}

    def save_stage_receipt(self, receipt: StageReceipt) -> None:
        started = perf_counter()
        if receipt.status == "committed" and not receipt.reusable():
            raise ValueError("committed stage receipt requires canonical result references, hashes, and complete provenance")
        with FileLock(str(self.lock_path)):
            receipts = self.load_stage_receipts()
            receipts[receipt.stage_id] = receipt
            self._atomic_write(
                self.stage_receipts_path,
                json.dumps({"schema_version": 1, "receipts": {key: item.to_dict() for key, item in sorted(receipts.items())}}, sort_keys=True, indent=2) + "\n",
            )
        self.stats.receipt_write_count += 1
        self.stats.receipt_write_time_ms += (perf_counter() - started) * 1000

    def save_analysis(self, state: AnalysisState) -> None:
        value = self._validate_analysis(state)
        with FileLock(str(self.lock_path)):
            self._write_validated(value)

    def capture_revision_snapshot(self) -> dict[str, bytes | None]:
        with FileLock(str(self.lock_path)):
            return self._revision_snapshot_unlocked()

    def restore_revision_snapshot(
        self,
        snapshot: Mapping[str, bytes | None],
        *,
        expected_current: Mapping[str, bytes | None] | None = None,
    ) -> bool:
        paths = {
            "analysis": self.analysis_path,
            "pending": self.pending_analysis_path,
            "pending_tokens": self.pending_tokens_path,
        }
        with FileLock(str(self.lock_path)):
            current = self._revision_snapshot_unlocked()
            current_pending_token = self._pending_token_from_bytes(current.get("pending"))
            snapshot_pending_token = self._pending_token_from_bytes(snapshot.get("pending"))
            if expected_current is not None and current != dict(expected_current):
                expected_pending = expected_current.get("pending")
                if expected_pending is not None and current.get("pending") == expected_pending and snapshot.get("pending") != expected_pending:
                    self.pending_analysis_path.unlink(missing_ok=True)
                    self._remember_consumed_pending_token(
                        current_pending_token,
                        revision=self._revision_from_bytes(current.get("pending")) or 0,
                    )
                return False
            consumed_tokens = self._tokens_from_bytes(snapshot.get("pending_tokens"))
            if current_pending_token and current_pending_token != snapshot_pending_token:
                consumed_tokens.add(current_pending_token)
            for name, path in paths.items():
                content = snapshot.get(name)
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    self._atomic_write(path, content.decode("utf-8"))
            if consumed_tokens:
                self._atomic_write(self.pending_tokens_path, json.dumps(sorted(consumed_tokens), indent=2) + "\n")
            return True

    def save_pending_if_unchanged(
        self,
        state: AnalysisState,
        expected_snapshot: Mapping[str, bytes | None],
    ) -> tuple[AnalysisState, dict[str, bytes | None]]:
        with FileLock(str(self.lock_path)):
            if self._revision_snapshot_unlocked() != dict(expected_snapshot):
                raise ValueError("concurrent analysis mutation detected before pending publication")
            pending = self._save_pending_unlocked(state)
            return pending, self._revision_snapshot_unlocked()

    def save_delivery_receipt(self, artifact_id: str, receipt: dict[str, object]) -> AnalysisState:
        started = perf_counter()
        with FileLock(str(self.lock_path)):
            if self.pending_analysis_path.exists():
                raise ValueError("cannot persist delivery receipt while a pending analysis revision exists")
            state = self.load_accepted()
            source_revision = receipt.get("source_revision")
            if state.revision_status.value != "ACCEPTED" or source_revision != state.revision:
                raise ValueError("cannot persist delivery receipt for a non-current accepted revision")
            artifacts = []
            found = False
            for artifact in state.artifacts:
                if artifact.id == artifact_id:
                    if artifact.kind != "presentation_spec":
                        raise ValueError("delivery receipt must attach to a presentation artifact")
                    if artifact.id in state.invalidation.stale_artifact_ids or artifact.lifecycle.value != "CURRENT":
                        raise ValueError("cannot persist delivery receipt for a stale presentation artifact")
                    artifacts.append(replace(artifact, delivery_receipt=dict(receipt)))
                    found = True
                else:
                    artifacts.append(artifact)
            if not found:
                raise ValueError(f"unknown artifact for delivery receipt: {artifact_id}")
            updated = replace(state, artifacts=artifacts)
            self._write_validated(self._validate_analysis(updated))
            self.stats.review_attach_count += 1
            self.stats.review_attach_time_ms += (perf_counter() - started) * 1000
            return updated

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
            token_revision = current.revision if current is not None else (pending.revision if pending is not None else expected_revision)
            consumed_tokens = self._load_consumed_pending_tokens(token_revision)
            if pending is None and state.pending_token and state.pending_token in consumed_tokens:
                raise ValueError("stale pending identity")
            if pending is None and current is not None and (
                current.revision != expected_revision
                or state.revision not in {expected_revision, expected_revision + 1}
            ):
                raise ValueError(
                    f"stale revision: expected {expected_revision}, current {current.revision}, state {state.revision}"
                )
            if pending is not None and current is not None and not accepted:
                self._remember_consumed_pending_token(pending.pending_token, revision=current.revision if current is not None else pending.revision)
                self.pending_analysis_path.unlink(missing_ok=True)
                return current
            status = RevisionStatus.ACCEPTED if accepted else RevisionStatus.REJECTED
            committed = replace(state, revision_status=status, pending_token=None)
            if pending is not None and current is not None and accepted:
                merge_started = perf_counter()
                committed = self._merge_states(current, committed)
                self.stats.merge_count += 1
                self.stats.merge_time_ms += (perf_counter() - merge_started) * 1000
            elif current is not None and current.revision_status != RevisionStatus.PENDING_REVIEW and committed.revision <= current.revision:
                number = current.revision + 1
                revision = Revision(
                    f"revision-{number}",
                    number,
                    "accepted mutation" if accepted else "rejected mutation",
                    [item.id for collection in [committed.evidence, committed.claims, committed.implications, committed.recommendations, committed.artifacts] for item in collection] + [item.id for item in committed.calculations],
                )
                committed = replace(committed, revision=number, revisions=[*current.revisions, revision])
            self._write_validated(self._validate_analysis(committed))
            if pending is not None:
                self._remember_consumed_pending_token(pending.pending_token, revision=committed.revision)
            self.pending_analysis_path.unlink(missing_ok=True)
            return committed

    def save_pending(self, state: AnalysisState) -> AnalysisState:
        with FileLock(str(self.lock_path)):
            return self._save_pending_unlocked(state)

    def _save_pending_unlocked(self, state: AnalysisState) -> AnalysisState:
        pending = replace(state, revision_status=RevisionStatus.PENDING_REVIEW, pending_token=uuid.uuid4().hex)
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
            merge_started = perf_counter()
            pending = self._merge_states(current, pending)
            self.stats.merge_count += 1
            self.stats.merge_time_ms += (perf_counter() - merge_started) * 1000
        self._write_validated(self._validate_analysis(pending), self.pending_analysis_path)
        if existing_pending is not None:
            self._remember_consumed_pending_token(existing_pending.pending_token, revision=current.revision if current is not None else existing_pending.revision)
        return pending

    def _revision_snapshot_unlocked(self) -> dict[str, bytes | None]:
        return {
            name: path.read_bytes() if path.exists() else None
            for name, path in (
                ("analysis", self.analysis_path),
                ("pending", self.pending_analysis_path),
                ("pending_tokens", self.pending_tokens_path),
            )
        }

    @staticmethod
    def _pending_token_from_bytes(content: bytes | None) -> str | None:
        if content is None:
            return None
        value = json.loads(content.decode("utf-8"))
        token = value.get("pending_token") if isinstance(value, dict) else None
        return token if isinstance(token, str) and token else None

    @staticmethod
    def _revision_from_bytes(content: bytes | None) -> int | None:
        if content is None:
            return None
        value = json.loads(content.decode("utf-8"))
        revision = value.get("revision") if isinstance(value, dict) else None
        return revision if isinstance(revision, int) else None

    @staticmethod
    def _tokens_from_bytes(content: bytes | None) -> set[str]:
        if content is None:
            return set()
        value = json.loads(content.decode("utf-8"))
        if isinstance(value, list):
            return {item for item in value if isinstance(item, str)}
        if isinstance(value, dict):
            tokens = value.get("tokens", ())
            return {item for item in tokens if isinstance(item, str)} if isinstance(tokens, list) else set()
        return set()

    def update_pending(self, state: AnalysisState) -> AnalysisState:
        if state.revision_status != RevisionStatus.PENDING_REVIEW or not state.pending_token:
            raise ValueError("pending update requires a pending review state")
        with FileLock(str(self.lock_path)):
            pending = self._load_path(self.pending_analysis_path) if self.pending_analysis_path.exists() else None
            if pending is None:
                raise ValueError("no pending analysis to update")
            if pending.revision != state.revision or pending.pending_token != state.pending_token:
                raise ValueError("stale pending identity")
            updated = replace(state, revision_status=RevisionStatus.PENDING_REVIEW)
            self._write_validated(self._validate_analysis(updated), self.pending_analysis_path)
            return updated

    def load_pending(self) -> AnalysisState:
        return self.load_analysis()

    def load_analysis(self) -> AnalysisState:
        path = self.pending_analysis_path if self.pending_analysis_path.exists() else self.analysis_path
        return self._load_path(path)

    def load_accepted(self) -> AnalysisState:
        if not self.analysis_path.exists():
            raise FileNotFoundError(self.analysis_path)
        return self._load_path(self.analysis_path)

    def _load_path(self, path: Path) -> AnalysisState:
        started = perf_counter()
        self.stats.load_count += 1
        value = migrate_analysis_dict(json.loads(path.read_text(encoding="utf-8")))
        value = self._validate_analysis(value)
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
                tuple(item.get("monitoring_indicators", ())),
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
                CalculationVerificationStatus(item.get("verification_status", "NOT_VERIFIED")),
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
                policy_id=item.get("policy_id", ""),
                policy_version=item.get("policy_version", ""),
                skill_hashes=tuple(item.get("skill_hashes", ())),
                check_id=item.get("check_id", ""),
                reviewer_id=item.get("reviewer_id", ""),
                execution_id=item.get("execution_id", ""),
                attempt_id=item.get("attempt_id", ""),
                method=item.get("method", ""),
                source_fingerprints=tuple(item.get("source_fingerprints", ())),
                dependency_fingerprints=tuple(tuple(value) for value in item.get("dependency_fingerprints", ())),
                slot_key=item.get("slot_key", ""),
                supersedes_review_id=item.get("supersedes_review_id"),
                superseded_by_review_id=item.get("superseded_by_review_id"),
                conflict_review_ids=tuple(item.get("conflict_review_ids", ())),
                check_results=tuple(
                    ReviewCheckResult(
                        check_id=str(result["check_id"]),
                        status=ReviewSlotStatus(result["status"]),
                        expected=result.get("expected"),
                        actual=result.get("actual"),
                        delta=result.get("delta"),
                        tolerance=result.get("tolerance"),
                        source_ids=tuple(result.get("source_ids", ())),
                        input_ids=tuple(result.get("input_ids", ())),
                        interpretation=result.get("interpretation", ""),
                        limitations=tuple(result.get("limitations", ())),
                    )
                    for result in item.get("check_results", ())
                ),
                legacy=bool(item.get("legacy", False)),
            )
            for item in value.get("review_records", ())
        ]
        result = AnalysisState(
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
                    item.get("delivery_receipt"),
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
        self.stats.load_time_ms += (perf_counter() - started) * 1000
        return result

    def _validate_analysis(self, value: AnalysisState | dict) -> dict:
        started = perf_counter()
        result = validate_analysis(value)
        self.stats.validation_count += 1
        self.stats.validation_time_ms += (perf_counter() - started) * 1000
        return result

    def _write_validated(self, value: dict, path: Path | None = None) -> None:
        target = path or self.analysis_path
        started = perf_counter()
        content = json.dumps(value, indent=2) + "\n"
        self._atomic_write(target, content)
        elapsed_ms = (perf_counter() - started) * 1000
        if target == self.pending_analysis_path:
            self.stats.pending_write_count += 1
            self.stats.pending_write_bytes += len(content.encode("utf-8"))
            self.stats.pending_write_time_ms += elapsed_ms
        elif target == self.analysis_path:
            self.stats.committed_write_count += 1
            self.stats.committed_write_bytes += len(content.encode("utf-8"))
            self.stats.committed_write_time_ms += elapsed_ms

    def _load_consumed_pending_tokens(self, revision: int | None = None) -> set[str]:
        if not self.pending_tokens_path.exists():
            return set()
        value = json.loads(self.pending_tokens_path.read_text(encoding="utf-8"))
        if isinstance(value, list):
            return {item for item in value if isinstance(item, str)}
        if not isinstance(value, dict) or revision is not None and value.get("revision") != revision:
            return set()
        tokens = value.get("tokens", ())
        return {item for item in tokens if isinstance(item, str)} if isinstance(tokens, list) else set()

    def _remember_consumed_pending_token(self, token: str | None, *, revision: int) -> None:
        if not token:
            return
        tokens = self._load_consumed_pending_tokens(revision)
        tokens.add(token)
        self._atomic_write(
            self.pending_tokens_path,
            json.dumps({"revision": revision, "tokens": sorted(tokens)}, indent=2) + "\n",
        )

    @staticmethod
    def _merge_states(current: AnalysisState, pending: AnalysisState) -> AnalysisState:
        def merge(items):
            result = list(items[0])
            positions = {
                getattr(item, "id", getattr(item, "review_id", None)): index
                for index, item in enumerate(result)
            }
            for collection in items[1:]:
                for item in collection:
                    item_id = getattr(item, "id", getattr(item, "review_id", None))
                    if item_id in positions:
                        result[positions[item_id]] = item
                    else:
                        result.append(item)
                        positions[item_id] = len(result) - 1
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
