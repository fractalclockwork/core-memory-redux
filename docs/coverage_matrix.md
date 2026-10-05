# Coverage Matrix

**Status:** `baseline` as the verification claim surface; gated cells are `pass` where evidence exists — remaining `stub` cells are Bench and 64×64 PCB harness  
**Owns:** scale × surface validation claims (only place allowed to assert them)  
**Does not own:** architecture invention — see [AUTHORITY.md](AUTHORITY.md)

Scale claims in this repository require an explicit row: which surfaces are validated at a given \(N \times N\). Hardware and schematic commitments must not outpace simulation capability. Process rules: [system_design_spec.md](system_design_spec.md) **REQ-SCALE-ANTIX** rule 7 and §6.

Legend: `—` not claimed; `stub` planned / described but not gated; `pass` gated green; `fail` known red. Gate IDs: **GATE-L0-PHYSICS**, **GATE-L1-CYCLE**, **GATE-L2-E2E**, **GATE-L3-SIL**, **GATE-L4-FABRIC**.

| Scale \(N\) | Schematic | PCB | SPICE (L0/L1/L2) | SIL (L3) | Bench |
|-------------|:---------:|:---:|:----------------:|:--------:|:-----:|
| 1 (single core) | — | — | pass (**GATE-L0-PHYSICS**) | — | — |
| 2×2 | pass (**GATE-L4-FABRIC** bring-up) | — | pass (**GATE-L1-CYCLE**, **GATE-L2-E2E**) | — | stub |
| 8×8 | — | pass (1× ccs_sense host + 2× axis_octal ERC/DRC) | — | pass (**GATE-L3-SIL**) | stub |
| 64×64 | pass (**GATE-L4-FABRIC**) | stub (1+16 layout described in [board_icd.md](board_icd.md) §7; harness not gated) | — (no Chan at n=64) | pass (**GATE-L3-SIL**) | — |

L0 evidence: `uv run pytest tests/test_l0_physics.py` (or `uv run python scripts/run_gate.py GATE-L0-PHYSICS`); model [`spice/models/chan_core.lib`](../spice/models/chan_core.lib), deck [`spice/l0/single_core.cir`](../spice/l0/single_core.cir).

L1 evidence: `uv run pytest tests/test_l1_cycle.py` (or `uv run python scripts/run_gate.py GATE-L1-CYCLE`); deck [`spice/l1/oracle_2x2.cir`](../spice/l1/oracle_2x2.cir); includes CCS-failure regression.

L2 evidence: `uv run pytest tests/test_l2_e2e.py` (or `uv run python scripts/run_gate.py GATE-L2-E2E`); deck [`spice/l2/driver_2x2.cir`](../spice/l2/driver_2x2.cir); behavioral AHC/DMOS polarity + mutex (`spice/models/dmos_ahc.lib`).

L3 evidence: `uv run pytest tests/test_l3_sil.py` (or `uv run python scripts/run_gate.py GATE-L3-SIL`); behavioral `ideal_core` + line R/L/C plant [`spice/py/l3_plant.py`](../spice/py/l3_plant.py); synthetic PIO harness [`spice/py/l3_harness.py`](../spice/py/l3_harness.py); diagonal + random sparse at n=8 and n=64 (no Chan).

L4 evidence: `uv run pytest tests/test_l4_fabric.py` (or `uv run python scripts/run_gate.py GATE-L4-FABRIC`); AST [`generators/mce_array.py`](../generators/mce_array.py); emit [`generators/emit_kicad.py`](../generators/emit_kicad.py) → [`kicad/bringup_2x2/`](../kicad/bringup_2x2/), [`kicad/driver_64x64/`](../kicad/driver_64x64/); ERC via `kicad-cli` 10.0.6 (`scripts/run_kicad_erc.py`).

Multi-board PCB: [`docs/board_icd.md`](board_icd.md) — **one** host distributes ADDR/`VDRIVE` and owns CCS/sense/write-back; axis-octal repeats (**2** @ 8×8 bring-up, **2×8 = 16** @ 64×64 with unique `g`; full roster §7). Emit `uv run python -m generators.cli --board ccs|axis` → [`kicad/pcb_ccs_sense/`](../kicad/pcb_ccs_sense/), [`kicad/pcb_axis_octal/`](../kicad/pcb_axis_octal/); `uv run pytest tests/test_board_pcb.py` / `scripts/run_kicad_board.py`. Docs describe the 1+16 layout; do **not** claim 64×64 PCB `pass` until the uniquely addressed 2×8 harness is gated. Bench stays `stub` until fab; exact \(I_c\) / \(V_{drive}\) stay non-normative ([design_choices.md](design_choices.md)).

Surfaces mean:

* **Schematic** — generated or hand-reviewed KiCad at that N (L4 prefers octal tiles / buses; see [hierarchy_abi.md](hierarchy_abi.md)).
* **PCB** — multi-board layouts (CCS+sense + axis-octal) with `kicad-cli` ERC/DRC error-clean; see [board_icd.md](board_icd.md).
* **SPICE** — L0 physics, L1 oracle, and/or L2 driver BOM decks at that N (L1/L2 stay at 2×2).
* **SIL** — L3 ideal plant + PIO/decode stimuli.
* **Bench** — physical measurements on the plane or fixture.
