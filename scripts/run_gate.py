#!/usr/bin/env python3
"""Thin wrapper to run fidelity-ladder gate tests."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GATE_TESTS = {
    "GATE-L0-PHYSICS": ["tests/test_l0_physics.py"],
    "GATE-L1-CYCLE": ["tests/test_l1_cycle.py"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "gate",
        nargs="?",
        default="GATE-L0-PHYSICS",
        choices=sorted(GATE_TESTS),
        help="Gate ID to run (default: GATE-L0-PHYSICS)",
    )
    args = parser.parse_args()
    tests = GATE_TESTS[args.gate]
    cmd = ["uv", "run", "pytest", "-q", *tests]
    print("Running", args.gate, "→", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
