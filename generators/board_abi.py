"""Multi-board packaging ABI — pinouts for ccs_sense + axis_octal.

Electrical nets stay naming.md / hierarchy_abi.md. This module owns board
connector pin lists consumed by docs/board_icd.md and generators/emit_boards.py.
"""

from __future__ import annotations

from generators.abi import OCTAL_PIN_COUNT, SENSE_NETS

# Bus header J_BUS (docs/board_icd.md §3) — 16 pins.
BUS_PINS: tuple[str, ...] = (
    "+3V3",
    "AGND",
    "VDRIVE",
    "AGND_PWR",
    "ADDR_NL0",
    "ADDR_NL1",
    "ADDR_NL2",
    "ADDR_NH0",
    "ADDR_NH1",
    "ADDR_NH2",
    "FWD_EN_n",
    "REV_EN_n",
    "DEC_EN",
    "CCS_RET_AXIS",
    "AXIS_ID0",
    "AXIS_ID1",
)

# Plane-facing A/B for one octal group (axis board J_PLANE).
PLANE_AB_PINS: tuple[str, ...] = tuple(
    [f"A{k}" for k in range(8)] + [f"B{k}" for k in range(8)]
)

# Sense/fold connector on CCS board only.
PLANE_SENSE_PINS: tuple[str, ...] = ("YA65", "YB66", "YA66", "YB65", "AGND")

# Pico-compatible header on schematic (timing + address/enable fan-out to bus).
PICO_PINS: tuple[str, ...] = (
    "+3V3",
    "AGND",
    "ADDR_NL0",
    "ADDR_NL1",
    "ADDR_NL2",
    "ADDR_NH0",
    "ADDR_NH1",
    "ADDR_NH2",
    "FWD_EN_n",
    "REV_EN_n",
    "DEC_EN",
    "SENSE_STROBE",
    "DOUT",
    "PIO_STROBE",
)

# PCB Pico footprint: timing/DOUT only — ADDR/EN/power leave via J_BUS pads
# so each copper net appears once (DRC-clean power-distribution layout).
PICO_PCB_PINS: tuple[str, ...] = (
    "SENSE_STROBE",
    "DOUT",
    "PIO_STROBE",
)

# Plane sense PCB pins (AGND returns on J_BUS only).
PLANE_SENSE_PCB_PINS: tuple[str, ...] = ("YA65", "YB66", "YA66", "YB65")

# CCS trimpot channels (must appear on ccs_sense only).
CCS_TRIM_REFS: tuple[str, ...] = ("RTRIM_X", "RTRIM_Y", "RTRIM_INH")

# Octal steer conceptual pin budget on axis board (hierarchy_abi).
AXIS_STEER_PIN_COUNT = OCTAL_PIN_COUNT  # 34

BOARD_PROJECTS = ("pcb_ccs_sense", "pcb_axis_octal")


def axis_steer_pins(group: int = 0) -> tuple[str, ...]:
    """34-pin octal tile nets for group g (local LS index, absolute A/B lines)."""
    pins = ["HS", "HSR"]
    pins.extend(f"LS{k}" for k in range(8))
    pins.extend(f"LSR{k}" for k in range(8))
    for k in range(8):
        line = 8 * group + k
        pins.append(f"A{line}")
        pins.append(f"B{line}")
    return tuple(pins)


def sense_nets_on_axis() -> frozenset[str]:
    """Sense/fold nets must not appear on axis_octal."""
    return SENSE_NETS
