# AGENTS.md — agent entry for core-memory-redux

Ground-up magnetic core memory **array driver** + simulation-in-the-loop digital twin. Model project for agentic hardware engineering. Intended host stack: `uv`/Python generators, ngspice/PySpice; KiCad later for L4 fabric. Host install: [docs/dev_host_setup.md](docs/dev_host_setup.md). **Docs + L0/L1 SPICE today**—no `kicad/`, generators, firmware, or L2+ decks yet.

## Before you edit design or invent architecture

1. Read [docs/AUTHORITY.md](docs/AUTHORITY.md) (SSOT map, ownership, conflict priority).
2. Open [docs/system_design_spec.md](docs/system_design_spec.md) for process, normative freeze table, L0–L4, anti-explosion rules.
3. Open **only** the owner doc for the fact you need (see AUTHORITY ownership table). Link; do not copy.

Human front door: [README.md](README.md). Chat is not authoritative.

## Hard bans

- Do **not** claim KiCad, generators, firmware, or L2+ SPICE/SIL exist in this repo. L0/L1 SPICE under `spice/l0/` and `spice/l1/` is real; scale claims still require [docs/coverage_matrix.md](docs/coverage_matrix.md).
- Do **not** use Chan / detailed `coremem` physics as the n=64 proof (**no Chan at n=64**); L0 ≤ 16 instances.
- Do **not** treat monolithic 256-end hierarchical sheets as the L4 ABI; target octal steer tiles + buses ([docs/hierarchy_abi.md](docs/hierarchy_abi.md)).
- L2 drive BOM is **DMOS** (TBD62783 / TBD62083), not TC4427A + FDS8958A.
- Do **not** assert scale validation except via [docs/coverage_matrix.md](docs/coverage_matrix.md).
- [docs/implementation_summary.md](docs/implementation_summary.md) is a **sketch**; it must not override owners.

## Where to look

| Need | Owner |
|------|--------|
| SSOT / who owns what | [docs/AUTHORITY.md](docs/AUTHORITY.md) |
| Process, gates, anti-explosion | [docs/system_design_spec.md](docs/system_design_spec.md) |
| Plane ICD, sense/inhibit, timing | [docs/design_specification.md](docs/design_specification.md) |
| Net names, decode/DMOS call model | [docs/naming.md](docs/naming.md) |
| Steer/magnetic pin budgets | [docs/hierarchy_abi.md](docs/hierarchy_abi.md) |
| BOM | [docs/component_selection.md](docs/component_selection.md) |
| Open decisions | [docs/design_choices.md](docs/design_choices.md) |
| Scale × surface claims | [docs/coverage_matrix.md](docs/coverage_matrix.md) |
| Ubuntu apt + `uv` host setup | [docs/dev_host_setup.md](docs/dev_host_setup.md) |
| L0 Chan model / GATE-L0 tests | [spice/l0/](spice/l0/), [tests/test_l0_physics.py](tests/test_l0_physics.py) |
| L1 2×2 oracle / GATE-L1 tests | [spice/l1/](spice/l1/), [tests/test_l1_cycle.py](tests/test_l1_cycle.py) |

If a requirement is ambiguous or two owners seem to conflict, **stop and ask**—do not invent a third answer.
