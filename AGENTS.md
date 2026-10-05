# AGENTS.md — agent entry for core-memory-redux

Ground-up magnetic core memory **array driver** + simulation-in-the-loop digital twin. Model project for agentic hardware engineering. Intended host stack: `uv`/Python generators, ngspice/PySpice, KiCad 10.0.6 (`kicad-cli`). Host install: [docs/dev_host_setup.md](docs/dev_host_setup.md). **Docs + L0–L3 sim/SIL + L4 fabric KiCad + multi-board PCB projects today**—no firmware / no bench fab yet.

## Before you edit design or invent architecture

1. Read [docs/AUTHORITY.md](docs/AUTHORITY.md) (SSOT map, ownership, conflict priority).
2. Open [docs/system_design_spec.md](docs/system_design_spec.md) for process, normative freeze table, L0–L4, anti-explosion rules.
3. Open **only** the owner doc for the fact you need (see AUTHORITY ownership table). Link; do not copy.

Human front door: [README.md](README.md). Chat is not authoritative.

## Hard bans

- Do **not** claim firmware or bench fab exist. L0–L2 SPICE, L3 ideal SIL, L4 fabric KiCad, and multi-board PCB projects (`kicad/pcb_ccs_sense/`, `kicad/pcb_axis_octal/`) are real; scale claims still require [docs/coverage_matrix.md](docs/coverage_matrix.md).
- Do **not** hand-edit generated `kicad/**` sheets/PCBs — fix AST/emitter and regenerate (`--n` fabric or `--board` PCB).
- Do **not** use Chan / detailed `coremem` physics as the n=64 proof (**no Chan at n=64**); L0 ≤ 16 instances; L3 uses `ideal_core` only.
- Do **not** treat monolithic 256-end hierarchical sheets as the L4 ABI; target octal steer tiles + buses ([docs/hierarchy_abi.md](docs/hierarchy_abi.md)).
- L2 drive BOM is **DMOS** (TBD62783 / TBD62083), not TC4427A + FDS8958A.
- Do **not** assert scale validation except via [docs/coverage_matrix.md](docs/coverage_matrix.md).
- [docs/implementation_summary.md](docs/implementation_summary.md) is a **sketch**; it must not override owners.
- Do **not** open, cite, or reconcile [`writeup/`](writeup/) when working on design, SPICE, tests, or `docs/`. A mention in the README is not permission to read it. Edit `writeup/` only when a human asks for a writeup pass; facts still come from owner docs and from re-running the harnesses. Never push a sentence from the essay back into an owner.

## Where to look

| Need | Owner |
|------|--------|
| SSOT / who owns what | [docs/AUTHORITY.md](docs/AUTHORITY.md) |
| Process, gates, anti-explosion | [docs/system_design_spec.md](docs/system_design_spec.md) |
| Plane ICD, sense/inhibit, timing | [docs/design_specification.md](docs/design_specification.md) |
| Net names, decode/DMOS call model | [docs/naming.md](docs/naming.md) |
| Steer/magnetic pin budgets | [docs/hierarchy_abi.md](docs/hierarchy_abi.md) |
| BOM / multi-board qty | [docs/component_selection.md](docs/component_selection.md) §6, [docs/bom_multiboard.csv](docs/bom_multiboard.csv) |
| Open decisions | [docs/design_choices.md](docs/design_choices.md) |
| Scale × surface claims | [docs/coverage_matrix.md](docs/coverage_matrix.md) |
| Ubuntu apt + `uv` host setup | [docs/dev_host_setup.md](docs/dev_host_setup.md) |
| L0 Chan model / GATE-L0 tests | [spice/l0/](spice/l0/), [tests/test_l0_physics.py](tests/test_l0_physics.py) |
| L1 2×2 oracle / GATE-L1 tests | [spice/l1/](spice/l1/), [tests/test_l1_cycle.py](tests/test_l1_cycle.py) |
| L2 driver e2e / GATE-L2 tests | [spice/l2/](spice/l2/), [tests/test_l2_e2e.py](tests/test_l2_e2e.py) |
| L3 ideal N×N SIL / GATE-L3 tests | [spice/l3/](spice/l3/), [spice/py/l3_plant.py](spice/py/l3_plant.py), [tests/test_l3_sil.py](tests/test_l3_sil.py) |
| L4 fabric AST / KiCad / GATE-L4 | [generators/](generators/), [kicad/](kicad/), [tests/test_l4_fabric.py](tests/test_l4_fabric.py) |
| Multi-board PCB (1 host + 2×8 axis) | [docs/board_icd.md](docs/board_icd.md), [generators/emit_boards.py](generators/emit_boards.py), [tests/test_board_pcb.py](tests/test_board_pcb.py) |

If a requirement is ambiguous or two owners seem to conflict, **stop and ask**—do not invent a third answer.
