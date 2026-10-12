import argparse
import json
from pathlib import Path

from foresight_os.artifacts.report import write_report
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.recovery import continue_investigation
from foresight_os.clients.first_client_adapter import LocalClient
from foresight_os.vertical_slice import run_vertical_slice


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="foresight-os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--workbook", type=Path, required=True)
    analyze.add_argument("--work-dir", type=Path, required=True)
    analyze.add_argument("--accept", action="store_true")

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
