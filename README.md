# core-memory-redux

Ground-up reimplementation of a magnetic core memory array driver and its simulation-in-the-loop (SIL) digital twin.

**Agents:** start at [AGENTS.md](AGENTS.md), then [docs/AUTHORITY.md](docs/AUTHORITY.md) (SSOT map). This README is the human front door; architecture bullets below are a snapshot and defer to owner docs.

## Why this repo exists

This is a rewrite of [`fractalclockwork/core-memory`](https://github.com/fractalclockwork/core-memory), rebuilt as a model project for **simulation-in-the-loop agentic engineering**. The goal is not only a working circuit, but a repeatable process: requirements, tools, generators, fidelity-gated simulation, and documentation that stay aligned as the design evolves.

**Done** means all three deliverables:

1. The engineering process (phased SIL loop, coverage gates, agent-friendly workflow)
2. The circuit (driver for the existing 64×64 ferrite plane)
3. Documentation of the circuit, simulation ladder, and design decisions

## Status

**Docs bootstrap (Phase 0).** Design contracts live under [`docs/`](docs/). There is no KiCad, SPICE, firmware, or host SIL tree yet. Claims are *normative target* / `baseline`, not as-built hardware.

**SSOT:** layered authority — one owner per fact category ([docs/AUTHORITY.md](docs/AUTHORITY.md)). Normative definition: [docs/system_design_spec.md](docs/system_design_spec.md) §1. Machine geometry SSOT (weave AST) is planned, not present.

## Target architecture (snapshot)

Non-authoritative summary — edit owners, not this list:

- **Plane / fold / timing:** [docs/design_specification.md](docs/design_specification.md) (`REQ-ICD-*`)
- **Drive path (DMOS):** [docs/component_selection.md](docs/component_selection.md) (`REQ-DRV-DMOS`)
- **Naming / decode call model:** [docs/naming.md](docs/naming.md) (`REQ-NAME-GATE`)
- **L4 fabric / pin budgets:** [docs/hierarchy_abi.md](docs/hierarchy_abi.md) (`REQ-HIER-OCTAL`)
- **Anti-explosion / L0–L4:** [docs/system_design_spec.md](docs/system_design_spec.md) (`REQ-SCALE-ANTIX`, `GATE-L*`)
- **Scale validation claims:** [docs/coverage_matrix.md](docs/coverage_matrix.md) only

## Open items

**Open technical decisions** (`open`): [docs/design_choices.md](docs/design_choices.md) — exact \(I_c\) / \(I_c/2\); \(V_{drive}\); inhibit polarity vs READ; Pico packaging; CCS MOSFET alternate; diagnostic LEDs.

**Deferred:** datasheet/appnote PDF tree; full evidence pack; generators and KiCad/SPICE trees.

## Phased implementation / simulation / validation loop

Detail and gate IDs: [docs/system_design_spec.md](docs/system_design_spec.md). L2 assumes **DMOS** BOM.

| Phase | Focus | Gate (summary) |
|-------|--------|----------------|
| **0** | Authority, ICD, naming | [AUTHORITY.md](docs/AUTHORITY.md); owners tagged `baseline` |
| **1** | L0 — single-core physics | `GATE-L0-PHYSICS` (≤16 Chan instances) |
| **2** | L1 — 2×2 oracle array | `GATE-L1-CYCLE` + CCS failure regression |
| **3** | L2 — driver fidelity | `GATE-L2-E2E`; freeze decode/DMOS ABI |
| **4** | L3 — ideal \(N \times N\) SIL | `GATE-L3-SIL` |
| **5** | L4 — hardware fabric | `GATE-L4-FABRIC`; octal tiles + buses |
| **6** | Bench bring-up | 2×2 first; characterize \(I_c\) |

## Documentation map

| Doc | Role | Status |
|-----|------|--------|
| [AGENTS.md](AGENTS.md) | Agent entry, hard bans | entry |
| [docs/AUTHORITY.md](docs/AUTHORITY.md) | SSOT map, ownership, conflict priority | `baseline` |
| [docs/system_design_spec.md](docs/system_design_spec.md) | Process, freeze table, anti-explosion, L0–L4 | `baseline` |
| [docs/design_specification.md](docs/design_specification.md) | Plane ICD, sense/inhibit, timing | `baseline` |
| [docs/design_choices.md](docs/design_choices.md) | Tradeoffs and open decisions | `baseline` / `open` |
| [docs/component_selection.md](docs/component_selection.md) | BOM (DMOS pivot) | `baseline` |
| [docs/naming.md](docs/naming.md) | Net grammar, hierarchy-as-call | `baseline` |
| [docs/hierarchy_abi.md](docs/hierarchy_abi.md) | Steer/magnetic pin budgets | `baseline` |
| [docs/coverage_matrix.md](docs/coverage_matrix.md) | Scale × surface claims | `baseline` (cells stub) |
| [docs/implementation_summary.md](docs/implementation_summary.md) | Block architecture sketch | `sketch` |
| [docs/theory_of_operation.md](docs/theory_of_operation.md) | Teaching summary | `sketch` |
| [docs/references.md](docs/references.md) | Citation placeholders | `sketch` |

## Dev-host tooling

To be documented in a later pass. Expected stack: Python (`uv`), KiCad, SPICE (ngspice / PySpice), RP2040 SDK.

## Upstream and non-goals

- **Upstream:** [fractalclockwork/core-memory](https://github.com/fractalclockwork/core-memory) — history only, not SSOT for this tree.
- **Not carrying over:** discrete MOSFET + TC4427 primary architecture; monolithic 256-end L4 ABI; as-built claims until regenerated from AST / phased loop.
# core-memory-redux
# core-memory-redux
