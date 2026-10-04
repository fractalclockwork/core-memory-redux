# Coverage Matrix

**Status:** `baseline` as the verification claim surface; cell values are mostly `stub` until artifacts land  
**Owns:** scale × surface validation claims (only place allowed to assert them)  
**Does not own:** architecture invention — see [AUTHORITY.md](AUTHORITY.md)

Scale claims in this repository require an explicit row: which surfaces are validated at a given \(N \times N\). Hardware and schematic commitments must not outpace simulation capability. Process rules: [system_design_spec.md](system_design_spec.md) **REQ-SCALE-ANTIX** rule 7 and §6.

Legend: `—` not claimed; `stub` planned; `pass` gated green; `fail` known red. Gate IDs: **GATE-L0-PHYSICS**, **GATE-L1-CYCLE**, **GATE-L2-E2E**, **GATE-L3-SIL**, **GATE-L4-FABRIC**.

| Scale \(N\) | Schematic | SPICE (L0/L1/L2) | SIL (L3) | Bench |
|-------------|:---------:|:----------------:|:--------:|:-----:|
| 1 (single core) | — | pass (**GATE-L0-PHYSICS**) | — | — |
| 2×2 | stub | pass (**GATE-L1-CYCLE**, **GATE-L2-E2E**) | — | stub |
| 8×8 | — | — | pass (**GATE-L3-SIL**) | — |
| 64×64 | stub (L4 tiled) | — (no Chan at n=64) | pass (**GATE-L3-SIL**) | — |

L0 evidence: `uv run pytest tests/test_l0_physics.py` (or `uv run python scripts/run_gate.py GATE-L0-PHYSICS`); model [`spice/models/chan_core.lib`](../spice/models/chan_core.lib), deck [`spice/l0/single_core.cir`](../spice/l0/single_core.cir).

L1 evidence: `uv run pytest tests/test_l1_cycle.py` (or `uv run python scripts/run_gate.py GATE-L1-CYCLE`); deck [`spice/l1/oracle_2x2.cir`](../spice/l1/oracle_2x2.cir); includes CCS-failure regression.

L2 evidence: `uv run pytest tests/test_l2_e2e.py` (or `uv run python scripts/run_gate.py GATE-L2-E2E`); deck [`spice/l2/driver_2x2.cir`](../spice/l2/driver_2x2.cir); behavioral AHC/DMOS polarity + mutex (`spice/models/dmos_ahc.lib`).

L3 evidence: `uv run pytest tests/test_l3_sil.py` (or `uv run python scripts/run_gate.py GATE-L3-SIL`); behavioral `ideal_core` + line R/L/C plant [`spice/py/l3_plant.py`](../spice/py/l3_plant.py); synthetic PIO harness [`spice/py/l3_harness.py`](../spice/py/l3_harness.py); diagonal + random sparse at n=8 and n=64 (no Chan).

Surfaces mean:

* **Schematic** — generated or hand-reviewed KiCad at that N (L4 prefers octal tiles / buses; see [hierarchy_abi.md](hierarchy_abi.md)).
* **SPICE** — L0 physics, L1 oracle, and/or L2 driver BOM decks at that N (L1/L2 stay at 2×2).
* **SIL** — L3 ideal plant + PIO/decode stimuli.
* **Bench** — physical measurements on the plane or fixture.
