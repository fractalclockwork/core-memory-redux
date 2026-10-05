#!/usr/bin/env python3
"""Run kicad-cli sch upgrade + erc on generated L4 projects (KiCad 10.0.6)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KICAD_ROOT = ROOT / "kicad"
CONFIG_HOME = ROOT / ".kicad-config"

PROJECTS = ("bringup_2x2", "driver_64x64")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    CONFIG_HOME.mkdir(parents=True, exist_ok=True)
    env["XDG_CONFIG_HOME"] = str(CONFIG_HOME)
    return env


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, env=_env(), text=True, capture_output=True)


def erc_project(project: str) -> list[str]:
    """Return list of error-severity violation messages (empty if clean)."""
    sch = KICAD_ROOT / project / "driver.kicad_sch"
    if not sch.is_file():
        return [f"missing schematic: {sch}"]
    if not shutil.which("kicad-cli"):
        return ["kicad-cli not on PATH — install KiCad 10.0.6 per docs/dev_host_setup.md"]

    up = _run(["kicad-cli", "sch", "upgrade", str(sch)])
    if up.returncode != 0:
        return [f"upgrade failed: {up.stderr or up.stdout}"]

    report = KICAD_ROOT / project / "erc.json"
    erc = _run(
        [
            "kicad-cli",
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-error",
            "--output",
            str(report),
            str(sch),
        ]
    )
    # kicad-cli may return non-zero when violations exist
    if not report.is_file():
        return [f"erc produced no report: {erc.stderr or erc.stdout}"]

    data = json.loads(report.read_text(encoding="utf-8"))
    errors: list[str] = []
    for sheet in data.get("sheets", []):
        for v in sheet.get("violations", []):
            sev = (v.get("severity") or "").lower()
            if sev == "error":
                desc = v.get("description") or v.get("type") or str(v)
                errors.append(f"{project}:{desc}")
    return errors


def main() -> int:
    ver = _run(["kicad-cli", "--version"])
    print("kicad-cli", (ver.stdout or ver.stderr or "").strip())
    all_errors: list[str] = []
    for project in PROJECTS:
        errs = erc_project(project)
        if errs:
            print(f"FAIL {project}: {len(errs)} error(s)")
            for e in errs[:20]:
                print(" ", e)
            all_errors.extend(errs)
        else:
            print(f"PASS {project}: 0 ERC errors")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
