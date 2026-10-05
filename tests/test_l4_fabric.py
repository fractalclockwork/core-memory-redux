"""GATE-L4-FABRIC — AST topology, idempotent emit, kicad-cli ERC."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generators.abi import OCTAL_PIN_COUNT, SENSE_NETS  # noqa: E402
from generators.emit_kicad import emit_project  # noqa: E402
from generators.mce_array import build_fabric  # noqa: E402

import importlib.util  # noqa: E402

_erc_spec = importlib.util.spec_from_file_location(
    "run_kicad_erc", ROOT / "scripts" / "run_kicad_erc.py"
)
_erc_mod = importlib.util.module_from_spec(_erc_spec)
assert _erc_spec and _erc_spec.loader
_erc_spec.loader.exec_module(_erc_mod)
erc_project = _erc_mod.erc_project


def test_ast_topology_n64():
    fab = build_fabric(64)
    assert fab.n == 64
    assert len(fab.groups) == 8
    assert len(fab.tiles) == 16  # 2 axes × 8 groups
    assert all(len(t.pins) == OCTAL_PIN_COUNT for t in fab.tiles)
    assert fab.fold["YA66"] == "SENSE_FOLD"
    assert fab.fold["YB65"] == "SENSE_FOLD"
    assert fab.sense_nets_disjoint_from_decode()
    assert SENSE_NETS.isdisjoint({"N_HS0_n", "DEC_EN", "FWD_EN_n"})
    # Diode law endpoints reference tile nets
    for tile in fab.tiles:
        assert tile.diodes
        for d in tile.diodes:
            assert d.anode
            assert d.cathode


def test_ast_topology_n2_subset():
    fab = build_fabric(2)
    assert fab.project_name() == "bringup_2x2"
    assert fab.groups == [0]
    assert len(fab.tiles) == 2  # X_g0 + Y_g0
    assert fab.tiles[0].lines == (0, 1)
    assert len(fab.decode_calls) == 4
    assert all(t in fab.tune_points for t in ("VDRIVE", "INH_POL_SEL", "PIO_STROBE"))


def test_emit_idempotent(tmp_path: Path):
    out = tmp_path / "kicad"
    p1 = emit_project(2, kicad_root=out)
    files1 = {p.name: p.read_bytes() for p in sorted(p1.glob("*.kicad_sch"))}
    assert "driver.kicad_sch" in files1
    assert "steer_octal_X_g0.kicad_sch" in files1
    assert (p1 / "fabric_manifest.json").is_file()
    p2 = emit_project(2, kicad_root=out)
    files2 = {p.name: p.read_bytes() for p in sorted(p2.glob("*.kicad_sch"))}
    assert files1 == files2


def test_emit_n64_sheet_count(tmp_path: Path):
    out = tmp_path / "kicad"
    proj = emit_project(64, kicad_root=out)
    manifest = json.loads((proj / "fabric_manifest.json").read_text(encoding="utf-8"))
    assert manifest["octal_tiles"] == 16
    assert manifest["n"] == 64
    schs = list(proj.glob("steer_octal_*.kicad_sch"))
    assert len(schs) == 16


@pytest.mark.parametrize("project", ["bringup_2x2", "driver_64x64"])
def test_kicad_erc_errors(project: str):
    """ERC error severity must be clean on generated roots (KiCad 10.0.6)."""
    # Ensure projects exist under repo kicad/
    n = 2 if project == "bringup_2x2" else 64
    emit_project(n)
    errors = erc_project(project)
    assert errors == [], f"ERC errors: {errors[:10]}"
