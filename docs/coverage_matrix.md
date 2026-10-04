# Coverage Matrix

**Status:** `baseline` as the verification claim surface; cell values are mostly `stub` until artifacts land  
**Owns:** scale × surface validation claims (only place allowed to assert them)  
**Does not own:** architecture invention — see [AUTHORITY.md](AUTHORITY.md)

Scale claims in this repository require an explicit row: which surfaces are validated at a given \(N \times N\). Hardware and schematic commitments must not outpace simulation capability. Process rules: [system_design_spec.md](system_design_spec.md) **REQ-SCALE-ANTIX** rule 7 and §6.

Legend: `—` not claimed; `stub` planned; `pass` gated green; `fail` known red. Gate IDs: **GATE-L0-PHYSICS**, **GATE-L1-CYCLE**, **GATE-L2-E2E**, **GATE-L3-SIL**, **GATE-L4-FABRIC**.

| Scale \(N\) | Schematic | SPICE (L0/L1/L2) | SIL (L3) | Bench |
|-------------|:---------:|:----------------:|:--------:|:-----:|
| 1 (single core) | — | stub | — | — |
| 2×2 | stub | stub | — | stub |
| 8×8 | — | — | stub | — |
| 64×64 | stub (L4 tiled) | — (no Chan at n=64) | stub | — |

Surfaces mean:

* **Schematic** — generated or hand-reviewed KiCad at that N (L4 prefers octal tiles / buses; see [hierarchy_abi.md](hierarchy_abi.md)).
* **SPICE** — L0 physics, L1 oracle, and/or L2 driver BOM decks at that N (L1/L2 stay at 2×2).
* **SIL** — L3 ideal plant + PIO/decode stimuli.
* **Bench** — physical measurements on the plane or fixture.
