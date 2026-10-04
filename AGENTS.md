# AGENTS.md — agent entry for core-memory-redux

Ground-up magnetic core memory **array driver** + simulation-in-the-loop digital twin. Model project for agentic hardware engineering. Intended stack later: `uv`/Python generators, KiCad, ngspice/PySpice, RP2040 PIO. **This tree is docs-bootstrap today**—no `kicad/`, SPICE, or firmware yet.

## Before you edit design or invent architecture

1. Read [docs/AUTHORITY.md](docs/AUTHORITY.md) (SSOT map, ownership, conflict priority).
2. Open [docs/system_design_spec.md](docs/system_design_spec.md) for process, normative freeze table, L0–L4, anti-explosion rules.
3. Open **only** the owner doc for the fact you need (see AUTHORITY ownership table). Link; do not copy.

Human front door: [README.md](README.md). Chat is not authoritative.

## Hard bans

- Do **not** claim KiCad, SPICE decks, firmware, or generators exist in this repo.
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

If a requirement is ambiguous or two owners seem to conflict, **stop and ask**—do not invent a third answer.
