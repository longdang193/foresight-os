import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

from foresight_os.artifacts.approval import build_approval_package, render_approval_json, render_approval_markdown
from foresight_os.artifacts.report import write_report
from foresight_os.controller.proposal import build_execution_recipe
from foresight_os.controller.proposal import classify_reuse
from foresight_os.controller.proposal import apply_execution_overrides
from foresight_os.controller.proposal import validate_execution_recipe_contract
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalRecord, ApprovalStatus
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.execution_gate import ExecutionAdmissionError, execute_approved_investigation
from foresight_os.persistence.recovery import continue_investigation
from foresight_os.clients.first_client_adapter import LocalClient
from foresight_os.analysis.powerbi import read_powerbi_project
from foresight_os.vertical_slice import run_vertical_slice


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="foresight-os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--workbook", type=Path, required=True)
    analyze.add_argument("--work-dir", type=Path, required=True)
    analyze.add_argument("--accept", action="store_true")

    propose = subparsers.add_parser("propose")
    propose.add_argument("--work-dir", type=Path, required=True)
    propose.add_argument("--question")
    propose.add_argument("--investigation-id", default="case-001")
    propose.add_argument("--format", choices=("json", "markdown"), default="markdown")
    propose.add_argument("--detailed", action="store_true")

    approve = subparsers.add_parser("approve")
    approve.add_argument("--work-dir", type=Path, required=True)
    approve.add_argument("--fingerprint", required=True)
    approve.add_argument("--approver-label")
    approve.add_argument("--run-fresh", action="append", default=[])

    execute = subparsers.add_parser("execute")
    execute.add_argument("--work-dir", type=Path, required=True)
    execute.add_argument("--prompt", required=True)
    execute.add_argument("--run-id")

    for name in ("pause", "cancel"):
        control = subparsers.add_parser(name)
        control.add_argument("--work-dir", type=Path, required=True)
        control.add_argument("--run-id", required=True)

    revise = subparsers.add_parser("revise")
    revise.add_argument("--work-dir", type=Path, required=True)
    revise.add_argument("--overrides-json", required=True)
    revise.add_argument("--reason", required=True)

    inspect_powerbi = subparsers.add_parser("inspect-powerbi")
    inspect_powerbi.add_argument("--path", type=Path, required=True)

    report = subparsers.add_parser("report")
    report.add_argument("--work-dir", type=Path, required=True)

    continue_run = subparsers.add_parser("continue")
    continue_run.add_argument("--work-dir", type=Path, required=True)
    continue_run.add_argument("--changed-id", action="append", default=[])
    continue_run.add_argument("--reason")

    challenge = subparsers.add_parser("challenge")
    challenge.add_argument("--work-dir", type=Path, required=True)
    challenge.add_argument("--record-id", required=True)
    challenge.add_argument("--reason", required=True)

    scope_change = subparsers.add_parser("scope-change")
    scope_change.add_argument("--work-dir", type=Path, required=True)
    scope_change.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        outcome = run_vertical_slice(args.workbook, args.work_dir, args.accept)
        print(json.dumps({"accepted": outcome.accepted, "status": outcome.status}))
        return 0 if outcome.accepted else 2
    if args.command == "propose":
        store = AnalysisStore(args.work_dir)
        if store.brief_path.exists():
            brief = store.load_brief()
        elif args.question:
            from foresight_os.wayfinding import create_work_brief

            brief = create_work_brief(args.question, investigation_id=args.investigation_id)
            store.save_brief(brief)
        else:
            print(json.dumps({"error": "--question is required when the work directory has no brief"}))
            return 2
        if store.execution_recipe_path.exists():
            recipe = store.load_recipe()
            diagnostics = validate_execution_recipe_contract(recipe)
            if diagnostics:
                print(json.dumps({"status": "DRAFT", "diagnostics": [item.__dict__ for item in diagnostics]}, sort_keys=True))
                return 2
        else:
            result = build_execution_recipe(brief)
            if not result.accepted:
                print(json.dumps({"status": result.status, "diagnostics": [item.__dict__ for item in result.diagnostics]}, sort_keys=True))
                return 2
            recipe = result.recipe
            store.save_recipe(recipe)
        package = build_approval_package(brief, recipe, AdaptationEnvelope(
            allowed_operations=("bounded_retry", "reduced_concurrency", "dependency_safe_topology_reduction"),
            max_retries=1,
            compatible_participant_substitution=True,
            dependency_safe_topology_reduction=True,
        ), reuse_candidates=tuple(
            {"stage_id": stage_id, **classify_reuse(
                receipt,
                reusable=False,
                reason="runtime fingerprint comparison is required before reuse",
            )}
            for stage_id, receipt in store.load_stage_receipts().items()
        ))
        rendered = render_approval_json(package) if args.format == "json" else render_approval_markdown(package, detailed=args.detailed)
        print(rendered, end="")
        return 0
    if args.command == "approve":
        store = AnalysisStore(args.work_dir)
        with FileLock(str(store.lock_path)):
            if not store.brief_path.exists() or not store.execution_recipe_path.exists():
                print(json.dumps({"error": "brief and execution recipe are required before approval"}))
                return 2
            brief = store.load_brief()
            recipe = store.load_recipe()
            package = build_approval_package(brief, recipe, AdaptationEnvelope(
                allowed_operations=("bounded_retry", "reduced_concurrency", "dependency_safe_topology_reduction"),
                max_retries=1,
                compatible_participant_substitution=True,
                dependency_safe_topology_reduction=True,
            ))
            if package.fingerprint != args.fingerprint:
                print(json.dumps({"error": "displayed fingerprint is stale", "current_fingerprint": package.fingerprint}))
                return 2
            previous = store.load_execution_approval()
            record = ApprovalRecord(
                investigation_id=brief.investigation_id,
                status=ApprovalStatus.APPROVED,
                projection=package.projection,
                projection_fingerprint=package.fingerprint,
                displayed_fingerprint=args.fingerprint,
                recipe_snapshot_fingerprint=canonical_json_hash(recipe.to_dict()),
                approval_source="local_cli",
                approved_at=datetime.now(timezone.utc).isoformat(),
                approver_label=args.approver_label,
                supersedes_fingerprint=previous.projection_fingerprint if previous else None,
                run_decisions={"run_fresh_stages": list(args.run_fresh)},
            )
            store._atomic_write(store.execution_approval_path, json.dumps(record.to_dict(), sort_keys=True, indent=2) + "\n")
        print(json.dumps({"status": record.status.value, "fingerprint": record.projection_fingerprint, "approval_source": record.approval_source}, sort_keys=True))
        return 0
    if args.command == "execute":
        try:
            import asyncio

            result = asyncio.run(execute_approved_investigation(args.work_dir, args.prompt, run_id=args.run_id))
        except ExecutionAdmissionError as exc:
            print(json.dumps({"error": str(exc)}))
            return 2
        print(json.dumps({"run_id": result.run_id, "outputs": len(result.outputs), "settled": result.metrics.settled}, sort_keys=True))
        return 0
    if args.command in {"pause", "cancel"}:
        from foresight_os.runtime.orchestration import get_run_control

        control = get_run_control(args.run_id)
        if control is None:
            print(json.dumps({"status": "BLOCKED_EXTERNAL", "error": "no local or transport-backed run-control channel can address this run"}))
            return 2
        getattr(control, f"request_{args.command}")()
        print(json.dumps({"status": control.state, "run_id": args.run_id}))
        return 0
    if args.command == "revise":
        store = AnalysisStore(args.work_dir)
        try:
            overrides = json.loads(args.overrides_json)
            result = apply_execution_overrides(store.load_recipe(), overrides)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "DRAFT", "error": str(exc)}))
            return 2
        if not result.accepted:
            print(json.dumps({"status": result.status, "diagnostics": [item.__dict__ for item in result.diagnostics]}, sort_keys=True))
            return 2
        store.save_recipe(result.recipe)
        print(json.dumps({"status": "REAPPROVAL_REQUIRED", "reason": args.reason, "recipe_saved": True}, sort_keys=True))
        return 0
    if args.command == "inspect-powerbi":
        print(json.dumps(read_powerbi_project(args.path).to_dict(), sort_keys=True))
        return 0
    if args.command == "report":
        store = AnalysisStore(args.work_dir)
        state = store.load_analysis()
        path = args.work_dir / "artifacts" / "executive-report.md"
        write_report(path, state)
        print(path)
        return 0
    if args.command == "continue":
        state = continue_investigation(args.work_dir, args.changed_id, args.reason)
        print(json.dumps({"investigation_id": state.investigation_id, "revision": state.revision, "invalidation": state.invalidation.__dict__}))
        return 0
    if args.command == "challenge":
        state = LocalClient().challenge(args.work_dir, args.record_id, args.reason)
        print(json.dumps({"revision": state.revision, "reassessment_ids": state.invalidation.reassessment_ids}))
        return 0
    if args.command == "scope-change":
        state = LocalClient().scope_change(args.work_dir, args.reason)
        print(json.dumps({"revision": state.revision, "stale_artifact_ids": state.invalidation.stale_artifact_ids}))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
