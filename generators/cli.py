"""CLI: uv run python -m generators.cli --n 2|64  OR  --board ccs|axis|all"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generators.emit_boards import emit_board
from generators.emit_kicad import KICAD_ROOT, emit_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit KiCad fabric (GATE-L4-FABRIC) or multi-board PCB projects"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--n",
        type=int,
        choices=(2, 64),
        help="Array size: 2=bringup_2x2, 64=driver_64x64",
    )
    mode.add_argument(
        "--board",
        choices=("ccs", "axis", "all"),
        help="Multi-board PCB: ccs=pcb_ccs_sense, axis=pcb_axis_octal, all=both",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=KICAD_ROOT,
        help=f"Output kicad/ root (default: {KICAD_ROOT})",
    )
    args = parser.parse_args(argv)
    if args.board is not None:
        out = emit_board(args.board, kicad_root=args.out)
    else:
        out = emit_project(args.n, kicad_root=args.out)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
