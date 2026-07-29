#!/usr/bin/env python3
"""Fast static validation that does not contact or change the homelab."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def validate_sensitive_files_are_untracked() -> None:
    forbidden_names = {
        ".env",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "talosconfig",
    }
    offenders = [
        str(path.relative_to(ROOT))
        for path in tracked_files()
        if path.name in forbidden_names
    ]
    if offenders:
        raise AssertionError(f"sensitive local files are tracked: {offenders}")


def validate_python_syntax() -> None:
    for path in ROOT.rglob("*.py"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validate_json_documents() -> None:
    for path in ROOT.rglob("*.json"):
        if ".git" in path.parts or "target" in path.parts:
            continue
        json.loads(path.read_text(encoding="utf-8"))


def validate_live_test_gates() -> None:
    required = {
        ROOT / "tests" / "test_mirth_integration.py":
            "require_live_test_acknowledgement()",
        ROOT / "tests" / "test_smart_gateway.py":
            "require_live_test_acknowledgement()",
    }
    for path, guard_call in required.items():
        source = path.read_text(encoding="utf-8")
        if source.count(guard_call) < 2:
            raise AssertionError(
                f"{path.relative_to(ROOT)} does not fail closed through "
                f"{guard_call}"
            )


def main() -> None:
    checks = (
        validate_sensitive_files_are_untracked,
        validate_python_syntax,
        validate_json_documents,
        validate_live_test_gates,
    )
    for check in checks:
        check()
        print(f"PASS: {check.__name__}")


if __name__ == "__main__":
    main()
