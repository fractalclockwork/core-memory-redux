#!/usr/bin/env python3
"""Run kicad-cli sch ERC + pcb DRC on multi-board projects (KiCad 10.0.6)."""

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

# (project_dir, root_sch_stem)
PROJECTS = (
    ("pcb_ccs_sense", "pcb_ccs_sense"),
    ("pcb_axis_octal", "pcb_axis_octal"),
)


def _env() -> dict[str, str]:
    env = os.environ.copy()
    CONFIG_HOME.mkdir(parents=True, exist_ok=True)
    env["XDG_CONFIG_HOME"] = str(CONFIG_HOME)
    env.setdefault("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
    env.setdefault("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
    return env


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, env=_env(), text=True, capture_output=True)


def erc_board(project: str, sch_stem: str) -> list[str]:
    sch = KICAD_ROOT / project / f"{sch_stem}.kicad_sch"
    if not sch.is_file():
        return [f"missing schematic: {sch}"]
    if not shutil.which("kicad-cli"):
        return ["kicad-cli not on PATH — install KiCad 10.0.6 per docs/dev_host_setup.md"]

    up = _run(["kicad-cli", "sch", "upgrade", str(sch)])
    if up.returncode != 0:
        return [f"upgrade failed: {up.stderr or up.stdout}"]

    report = KICAD_ROOT / project / "erc.json"
    _run(
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
    if not report.is_file():
        return [f"erc produced no report for {project}"]

    data = json.loads(report.read_text(encoding="utf-8"))
    errors: list[str] = []
    for sheet in data.get("sheets", []):
        for v in sheet.get("violations", []):
            if (v.get("severity") or "").lower() == "error":
                desc = v.get("description") or v.get("type") or str(v)
                errors.append(f"{project}:{desc}")
    return errors


def drc_board(project: str) -> list[str]:
    pcb = KICAD_ROOT / project / f"{project}.kicad_pcb"
    if not pcb.is_file():
        return [f"missing pcb: {pcb}"]
    if not shutil.which("kicad-cli"):
        return ["kicad-cli not on PATH"]

    _run(["kicad-cli", "pcb", "upgrade", str(pcb)])
    report = KICAD_ROOT / project / "drc.json"
    _run(
        [
            "kicad-cli",
            "pcb",
            "drc",
            "--format",
            "json",
            "--severity-error",
            "--output",
            str(report),
            str(pcb),
        ]
    )
    if not report.is_file():
        return [f"drc produced no report for {project}"]

    data = json.loads(report.read_text(encoding="utf-8"))
    errors: list[str] = []
    for v in data.get("violations", []):
        if (v.get("severity") or "").lower() == "error":
            desc = v.get("description") or v.get("type") or str(v)
            errors.append(f"{project}:viol:{desc}")
    for v in data.get("unconnected_items", []):
        if (v.get("severity") or "").lower() == "error":
            desc = v.get("description") or v.get("type") or str(v)
            errors.append(f"{project}:unconnected:{desc}")
    return errors


def main() -> int:
    ver = _run(["kicad-cli", "--version"])
    print("kicad-cli", (ver.stdout or ver.stderr or "").strip())
    all_errors: list[str] = []
    for project, stem in PROJECTS:
        e = erc_board(project, stem)
        d = drc_board(project)
        if e or d:
            print(f"FAIL {project}: erc={len(e)} drc={len(d)}")
            for msg in (e + d)[:20]:
                print(" ", msg)
            all_errors.extend(e + d)
        else:
            print(f"PASS {project}: ERC+DRC clean")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
