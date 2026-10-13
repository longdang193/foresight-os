from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).parents[2])
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {"source_root": str(args.source_root.resolve())}
    with tempfile.TemporaryDirectory(prefix="foresight-wheel-") as temp:
        temp_root = Path(temp)
        source_copy = temp_root / "source"
        shutil.copytree(args.source_root, source_copy, ignore=shutil.ignore_patterns(".git", "build", "work", "*.egg-info"))
        wheel_dir = temp_root / "wheel"
        wheel_dir.mkdir()
        build = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(wheel_dir), str(source_copy)], capture_output=True, text=True, check=False)
        report["build_returncode"] = build.returncode
        if build.returncode != 0:
            report["stderr"] = build.stderr[-2000:]
        else:
            venv = temp_root / "venv"
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True)
            python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            wheel = next(wheel_dir.glob("*.whl"))
            install = subprocess.run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)], capture_output=True, text=True, check=False)
            probe = subprocess.run([str(python), "-c", "import foresight_os; print(foresight_os.__file__)"], capture_output=True, text=True, check=False)
            imported = Path(probe.stdout.strip()).resolve() if probe.returncode == 0 else None
            report.update({"install_returncode": install.returncode, "probe_returncode": probe.returncode, "imported_path": str(imported) if imported else None, "outside_repository": bool(imported and args.source_root.resolve() not in imported.parents)})
    report["passed"] = bool(report.get("build_returncode") == 0 and report.get("install_returncode") == 0 and report.get("probe_returncode") == 0 and report.get("outside_repository"))
    (args.output_root / "clean-wheel-report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
