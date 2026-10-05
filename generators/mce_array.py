"""Weave/fabric AST — geometry SSOT for GATE-L4-FABRIC (AUTHORITY Layer D).

Emits structured fabric descriptions consumed by emit_kicad. Markdown ICD/BOM
owners remain authoritative for electrical contracts; this module owns topology.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from generators.abi import (
    AXES,
    DECODE_HS_OUTS,
    DECODE_LS_OUTS,
    DIRS,
    OCTAL_PIN_COUNT,
    SENSE_NETS,
    lines_in_group,
    ls_of,
    octal_groups_for_n,
)


@dataclass(frozen=True)
class DiodeEdge:
    """One SS14 in an octal tile (anode → cathode nets)."""

    anode: str
    cathode: str
    role: str  # FWD_HS | FWD_LS | REV_HS | REV_LS


@dataclass(frozen=True)
class OctalTile:
    axis: str  # X | Y
    group: int
    lines: tuple[int, ...]
    pins: tuple[str, ...]
    diodes: tuple[DiodeEdge, ...]

    @property
    def sheet_name(self) -> str:
        return f"steer_octal_{self.axis}_g{self.group}"


@dataclass(frozen=True)
class DecodeCall:
    axis: str
    direction: str  # FWD | REV
    hs_outs: tuple[str, ...]
    ls_outs: tuple[str, ...]

    @property
    def instance(self) -> str:
        return f"decode_{self.axis}_{self.direction}"


@dataclass
class FabricAST:
    """Parameterized n×n fabric (n=2 bring-up or n=64 full plane)."""

    n: int
    groups: list[int] = field(init=False)
    tiles: list[OctalTile] = field(init=False)
    decode_calls: list[DecodeCall] = field(init=False)
    plane_buses: dict[str, list[str]] = field(init=False)
    fold: dict[str, str] = field(init=False)
    tune_points: tuple[str, ...] = (
        "CCS_X_TRIM",
        "CCS_Y_TRIM",
        "CCS_INH_TRIM",
        "VDRIVE",
        "INH_POL_SEL",
        "PIO_STROBE",
    )

    def __post_init__(self) -> None:
        if self.n not in (2, 64):
            raise ValueError("GATE-L4 generators support n=2 (bring-up) or n=64 only")
        self.groups = octal_groups_for_n(self.n)
        self.tiles = []
        for axis in AXES:
            for g in self.groups:
                self.tiles.append(self._make_tile(axis, g))
        self.decode_calls = [self._make_decode(ax, d) for ax in AXES for d in DIRS]
        self.plane_buses = {
            "XA": [f"XA{i}" for i in range(self.n)],
            "XB": [f"XB{i}" for i in range(self.n)],
            "YA": [f"YA{i}" for i in range(self.n)],
            "YB": [f"YB{i}" for i in range(self.n)],
        }
        # REQ-ICD-FOLD local on magnetic sheet
        self.fold = {
            "YA66": "SENSE_FOLD",
            "YB65": "SENSE_FOLD",
            "YA65": "YA65",
            "YB66": "YB66",
            "SOFT_BIAS": "R_SENSE_FOLD_10k",
        }

    def _make_tile(self, axis: str, g: int) -> OctalTile:
        lines = tuple(lines_in_group(g, self.n))
        a = axis  # X or Y
        pins = [
            f"{a}HS{g}",
            f"{a}HS{g}R",
        ]
        for k in range(8):
            pins.append(f"{a}LS{k}")
        for k in range(8):
            pins.append(f"{a}LS{k}R")
        for line in range(g * 8, g * 8 + 8):
            # Full octal pin budget always presents A/B[0..7] slots for the group.
            pins.append(f"{a}A{line}")
            pins.append(f"{a}B{line}")
        assert len(pins) == OCTAL_PIN_COUNT, (len(pins), OCTAL_PIN_COUNT)

        diodes: list[DiodeEdge] = []
        for line in lines:
            k = ls_of(line)
            # Plane ends: XA/XB or YA/YB naming on root; tile uses A/B.
            diodes.append(
                DiodeEdge(f"{a}HS{g}", f"{a}B{line}", "FWD_HS")
            )
            diodes.append(
                DiodeEdge(f"{a}A{line}", f"{a}LS{k}", "FWD_LS")
            )
            diodes.append(
                DiodeEdge(f"{a}HS{g}R", f"{a}A{line}", "REV_HS")
            )
            diodes.append(
                DiodeEdge(f"{a}B{line}", f"{a}LS{k}R", "REV_LS")
            )
        return OctalTile(
            axis=axis,
            group=g,
            lines=lines,
            pins=tuple(pins),
            diodes=tuple(diodes),
        )

    def _make_decode(self, axis: str, direction: str) -> DecodeCall:
        # naming.md §2: omit dir = FWD/READ; `r` = REV/WRITE → X_HS0r_n
        rev = "r" if direction == "REV" else ""
        pref = f"{axis}_"
        hs = tuple(f"{pref}HS{i}{rev}_n" for i in range(DECODE_HS_OUTS))
        ls = tuple(f"{pref}LS{i}{rev}_en" for i in range(DECODE_LS_OUTS))
        return DecodeCall(axis=axis, direction=direction, hs_outs=hs, ls_outs=ls)

    def sense_nets_disjoint_from_decode(self) -> bool:
        decode_pins: set[str] = set()
        for call in self.decode_calls:
            decode_pins.update(call.hs_outs)
            decode_pins.update(call.ls_outs)
            decode_pins.add("DEC_EN")
            decode_pins.add("FWD_EN_n")
            decode_pins.add("REV_EN_n")
        return SENSE_NETS.isdisjoint(decode_pins)

    def project_name(self) -> str:
        return "bringup_2x2" if self.n == 2 else "driver_64x64"

    def summary(self) -> dict:
        return {
            "n": self.n,
            "project": self.project_name(),
            "octal_tiles": len(self.tiles),
            "groups": list(self.groups),
            "decode_calls": len(self.decode_calls),
            "octal_pin_count": OCTAL_PIN_COUNT,
            "diodes": sum(len(t.diodes) for t in self.tiles),
            "tune_points": list(self.tune_points),
            "fold": dict(self.fold),
            "sense_disjoint": self.sense_nets_disjoint_from_decode(),
        }


def build_fabric(n: int) -> FabricAST:
    return FabricAST(n=n)
