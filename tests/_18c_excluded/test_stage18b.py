#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STAGES = [
    ("16V", "tests/test_stage16v.py"),
    ("16W", "tests/test_stage16w.py"),
    ("16X", "tests/test_stage16x.py"),
    ("16Y", "tests/test_stage16y.py"),
    ("16Z", "tests/test_stage16z.py"),
]


def run_stage(name, script):
    print()
    print("=" * 60)
    print(f"RUNNING {name}")
    print("=" * 60)

    path = ROOT / script

    if not path.exists():
        print(f"{name}: FAILED — missing {script}")
        return False

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    output = result.stdout
    print(output, end="")

    if f"STAGE {name}: FAILED" in output:
        print(f"\n{name}: FAILED")
        return False

    if f"STAGE {name}: PASSED" in output:
        print(f"\n{name}: PASSED")
        return True

    print(f"\n{name}: FAILED — no explicit result")
    return False


def main():
    print("=" * 60)
    print("STAGE 18B — FAST VERIFIED REGRESSION")
    print("=" * 60)
    print("Signal-only mode : ENABLED")
    print("Trade execution  : DISABLED")
    print("Primary market   : XAUUSD")
    print("=" * 60)

    results = []

    for name, script in STAGES:
        results.append((name, run_stage(name, script)))

    print()
    print("=" * 60)
    print("STAGE 18B RESULTS")
    print("=" * 60)

    failed = []

    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{name:<8}: {status}")
        if not passed:
            failed.append(name)

    print("=" * 60)

    if failed:
        print("STAGE 18B: FAILED")
        print("Failed:", ", ".join(failed))
        return 1

    print("STAGE 18B: PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
