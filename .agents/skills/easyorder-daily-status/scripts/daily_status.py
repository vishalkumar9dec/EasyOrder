#!/usr/bin/env python3
"""Run the repeatable local EasyOrder daily status checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_command(name: str, command: list[str], cwd: Path) -> tuple[bool, str]:
    print(f"\n## {name}")
    print("$ " + " ".join(command))
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = result.stdout.strip()
    if output:
        print(output)
    status = "PASS" if result.returncode == 0 else "FAIL"
    print(f"[{status}] {name}")
    return result.returncode == 0, output


def probe_whatsapp_payloads(repo_root: Path) -> bool:
    backend_dir = repo_root / "src" / "backend"
    python = backend_dir / ".venv" / "bin" / "python"
    fixtures_dir = repo_root / "docs" / "api-test-data"

    print("\n## WhatsApp Payload Fixtures")
    if not python.exists():
        print(f"[FAIL] Backend virtualenv Python not found: {python}")
        return False
    if not fixtures_dir.exists():
        print(f"[FAIL] Fixture directory not found: {fixtures_dir}")
        return False

    script = """
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
for path in sorted(Path('../../docs/api-test-data').glob('whatsapp-*.json')):
    response = client.post('/api/whatsapp/webhook', json=json.loads(path.read_text()))
    payload = response.json()
    marker = payload.get('status') or payload.get('detail')
    print(f'{path.name}: {response.status_code} {marker}')
"""
    result = subprocess.run(
        [str(python), "-c", script],
        cwd=backend_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = result.stdout.strip()
    if output:
        print(output)

    expected = {
        "whatsapp-injection.json: 400",
        "whatsapp-low-budget.json: 200",
        "whatsapp-tagged-normal.json: 200",
        "whatsapp-untagged.json: 200",
        "whatsapp-vegetarian.json: 200",
    }
    observed = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(".json:"):
            observed.add(f"{parts[0]} {parts[1]}")

    ok = result.returncode == 0 and expected.issubset(observed)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] WhatsApp Payload Fixtures")
    return ok


def scan_docs(repo_root: Path) -> bool:
    print("\n## Documentation Signals")
    docs = [
        repo_root / "docs" / "implementation-tasks.md",
        repo_root / "docs" / "manual-ui-test-plan.md",
        repo_root / "docs" / "easyorder-prd.md",
        repo_root / "docs" / "implementation-plan.md",
    ]
    patterns = [
        "Needs vendor/source follow-up",
        "restaurant_id",
        "restaurant_name",
        "brand/source",
        "one Food order",
        "multiple restaurants",
    ]

    ok = True
    for doc in docs:
        if not doc.exists():
            print(f"[FAIL] Missing {doc.relative_to(repo_root)}")
            ok = False
            continue
        text = doc.read_text(encoding="utf-8")
        hits = [pattern for pattern in patterns if pattern in text]
        print(f"{doc.relative_to(repo_root)}: {', '.join(hits) if hits else 'no tracked signals'}")
    print(f"[{'PASS' if ok else 'FAIL'}] Documentation scan")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".", help="Path to the EasyOrder repository root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    checks: list[tuple[str, bool]] = []

    commands = [
        ("Git Status", ["git", "status", "--short", "--branch"]),
        ("Backend And Frontend Tests", ["make", "test"]),
        ("Frontend Production Build", ["make", "frontend-build"]),
        (
            "Backend Ruff",
            [
                str(repo_root / "src" / "backend" / ".venv" / "bin" / "python"),
                "-m",
                "ruff",
                "check",
                "src/backend/app",
                "src/backend/tests",
            ],
        ),
    ]

    for name, command in commands:
        ok, _ = run_command(name, command, repo_root)
        checks.append((name, ok))

    checks.append(("WhatsApp Payload Fixtures", probe_whatsapp_payloads(repo_root)))
    checks.append(("Documentation Scan", scan_docs(repo_root)))

    print("\n## Summary")
    for name, ok in checks:
        print(f"- {name}: {'PASS' if ok else 'FAIL'}")

    failed = [name for name, ok in checks if not ok]
    if failed:
        print("\nOverall: FAIL")
        print(json.dumps({"failed": failed}, indent=2))
        return 1

    print("\nOverall: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
