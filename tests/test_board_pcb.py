"""Multi-board PCB topology + kicad-cli ERC/DRC (ccs_sense + axis_octal)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generators.abi import OCTAL_PIN_COUNT, SENSE_NETS  # noqa: E402
from generators.board_abi import (  # noqa: E402
    AXIS_STEER_PIN_COUNT,
    BUS_PINS,
    CCS_TRIM_REFS,
    PICO_PCB_PINS,
    axis_steer_pins,
    sense_nets_on_axis,
)
from generators.emit_boards import emit_board  # noqa: E402

import importlib.util  # noqa: E402

_board_spec = importlib.util.spec_from_file_location(
    "run_kicad_board", ROOT / "scripts" / "run_kicad_board.py"
)
_board_mod = importlib.util.module_from_spec(_board_spec)
assert _board_spec and _board_spec.loader
_board_spec.loader.exec_module(_board_mod)
erc_board = _board_mod.erc_board
drc_board = _board_mod.drc_board


def test_axis_steer_pin_budget():
    pins = axis_steer_pins(0)
    assert len(pins) == OCTAL_PIN_COUNT == AXIS_STEER_PIN_COUNT
    assert "HS" in pins and "HSR" in pins
    assert all(f"A{k}" in pins for k in range(8))
    assert sense_nets_on_axis() == SENSE_NETS


def test_ccs_trims_and_sense_not_on_axis(tmp_path: Path):
    axis = emit_board("axis", kicad_root=tmp_path)
    sch = (axis / "pcb_axis_octal.kicad_sch").read_text(encoding="utf-8")
    for net in SENSE_NETS:
        assert net not in sch, f"sense net {net} must not appear on axis board"
    for trim in CCS_TRIM_REFS:
        assert trim not in sch

    ccs = emit_board("ccs", kicad_root=tmp_path)
    csch = (ccs / "pcb_ccs_sense.kicad_sch").read_text(encoding="utf-8")
    for trim in CCS_TRIM_REFS:
        assert trim in csch
    assert "SENSE_FOLD" in csch
    assert "Rfold" in csch
    for net in ("YA65", "YB66", "YA66", "YB65"):
        assert net in csch


def test_bom_parts_placed_on_sch_and_pcb(tmp_path: Path):
    ccs = emit_board("ccs", kicad_root=tmp_path)
    axis = emit_board("axis", kicad_root=tmp_path)
    csch = (ccs / "pcb_ccs_sense.kicad_sch").read_text(encoding="utf-8")
    asch = (axis / "pcb_axis_octal.kicad_sch").read_text(encoding="utf-8")
    cpcb = (ccs / "pcb_ccs_sense.kicad_pcb").read_text(encoding="utf-8")
    apcb = (axis / "pcb_axis_octal.kicad_pcb").read_text(encoding="utf-8")

    for token in (
        "TL431",
        "OPA192",
        "IRLZ44N",
        "BAT54S",
        "TLV3501",
        "74AHC74",
        "RTRIM_X",
        "U_OA_X",
        "J_PICO_HDR",
    ):
        assert token in csch, token
        assert token in cpcb or token.replace("U_OA_X", "OPA192") in cpcb

    for token in (
        "74AHC138",
        "74AHC238",
        "TBD62783",
        "TBD62083",
        "U_HS_FWD",
        "U_DMOS_LS_FWD",
        "SS14",
    ):
        assert token in asch, token
    assert apcb.count("Diode_SMD:D_SMA") == 32
    assert "SOIC-18W" in apcb
    assert "TO-220-3_Vertical" in cpcb
    assert "Potentiometer_Bourns_3296W" in cpcb


def test_emit_board_manifests(tmp_path: Path):
    ccs = emit_board("ccs", kicad_root=tmp_path)
    axis = emit_board("axis", kicad_root=tmp_path)
    cm = json.loads((ccs / "board_manifest.json").read_text(encoding="utf-8"))
    am = json.loads((axis / "board_manifest.json").read_text(encoding="utf-8"))
    assert cm["ccs_trims"] == list(CCS_TRIM_REFS)
    assert cm["pico_pcb_pins"] == list(PICO_PCB_PINS)
    assert am["steer_pin_count"] == OCTAL_PIN_COUNT
    assert am["bus_pins"] == list(BUS_PINS)
    assert (ccs / "pcb_ccs_sense.kicad_pcb").is_file()
    assert (axis / "pcb_axis_octal.kicad_pcb").is_file()


def test_pcb_one_pad_per_net(tmp_path: Path):
    for board in ("ccs", "axis"):
        out = emit_board(board, kicad_root=tmp_path)
        name = "pcb_ccs_sense" if board == "ccs" else "pcb_axis_octal"
        pcb = (out / f"{name}.kicad_pcb").read_text(encoding="utf-8")
        # Top-level net table only (pad (net …) refs come after first footprint).
        header = pcb.split("(footprint", 1)[0]
        names = []
        for line in header.splitlines():
            s = line.strip()
            if s.startswith("(net ") and not s.startswith("(net 0"):
                parts = s.split('"')
                if len(parts) >= 2:
                    names.append(parts[1])
        assert names, f"no nets in {name}"
        assert len(names) == len(set(names)), f"duplicate nets on {name}: {names}"


@pytest.mark.parametrize(
    "project,stem",
    [("pcb_ccs_sense", "pcb_ccs_sense"), ("pcb_axis_octal", "pcb_axis_octal")],
)
def test_board_erc_drc(project: str, stem: str):
    board = "ccs" if project == "pcb_ccs_sense" else "axis"
    emit_board(board)
    errors = erc_board(project, stem) + drc_board(project)
    assert errors == [], f"ERC/DRC errors: {errors[:12]}"
