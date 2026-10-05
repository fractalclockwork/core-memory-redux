# Board ICD — CCS/sense host + axis-octal modules

**Status:** `baseline` (mechanical / packaging contract for multi-board bring-up and 64×64 scale-out)  
**Owns:** board split, connector pinouts, 8×8 bring-up wiring, 2×8 axis replication for 64×64  
**Does not own:** plane physical ICD, BOM MPNs, gate criteria — see [AUTHORITY.md](AUTHORITY.md)

Electrical ABI stays [naming.md](naming.md) / [hierarchy_abi.md](hierarchy_abi.md) **REQ-HIER-OCTAL**. Bus net grammar bridge: [naming.md](naming.md) §4.1. Tune knobs: [design_choices.md](design_choices.md). BOM MPNs + multi-board quantities: [component_selection.md](component_selection.md) §6 / [`bom_multiboard.csv`](bom_multiboard.csv). Generated KiCad: [`kicad/pcb_ccs_sense/`](../kicad/pcb_ccs_sense/), [`kicad/pcb_axis_octal/`](../kicad/pcb_axis_octal/) from [`generators/`](../generators/).

## 1. Architecture

Two PCB designs only:

| Design | Role |
|--------|------|
| **`ccs_sense` (one host)** | Distributes **address**, **`VDRIVE`**, logic power, and bank enables on the control bus. Owns all **CCS**, **sense / inhibit / fold**, and **write-back** path (comparator → latch → `DOUT`). Pico (or equivalent) timing sits here. |
| **`axis_octal` (repeated)** | Identical decode + DMOS + SS14 board for **8 lines** (one HS group). Same copper for X or Y; straps set axis and unique group address `g=0..7`. |

### Quantities

| | Bring-up (prove) | Full array (64×64) |
|--|-----------------:|-------------------:|
| `ccs_sense` | **1** | **1** (unchanged) |
| `axis_octal` | **2** = 1×X + 1×Y at `g=0` | **16** = **2×8** (8×X + 8×Y, `g=0..7`) |
| Cores exercised | 8×8 | 64×64 |

Scale-out is **replication with unique address straps**, not a new axis PCB. The host still fans out ADDR / `VDRIVE` / enables; each axis board owns only its eight plane lines.

```text
                    ┌─────────────────────────────────────┐
                    │  ccs_sense (×1)                     │
  Pico / PIO ──────►│  ADDR, EN, VDRIVE, +3V3 distribution│
                    │  CCS_X / CCS_Y / CCS_INH            │
                    │  sense + fold + write-back (DOUT)    │
                    └──────────────┬──────────────────────┘
                                   │ J_BUS (star @ 64×64; daisy OK @ 8×8)
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
   axis_octal X g=0 … g=7    axis_octal Y g=0 … g=7    (16 boards = 2×8)
          │                        │
          └──────────► ferrite plane XA/XB / YA/YB + YA65/YB66
```

Bring-up uses only the `g=0` pair (three boards total). Full array is **1 + 2×8 = 17** boards — roster and harness in §7.

## 2. Stackup / mechanics

- **Layers:** **4-layer preferred** for the full-array host and all axis boards (Sig / GND / PWR / Sig). 2-layer remains acceptable only as an early **CCS prototype** exception if the CCS MOSFET has copper pour + heatsink.
- **Axis board size target:** ≤ 100×80 mm (octal connectors + DMOS SOIC-18s).
- **CCS board size target:** ≤ 120×80 mm (three linear CCS + sense + Pico header + bus host).
- **Connectors:** 2.54 mm pin headers unless noted; high-current CCS/`VDRIVE` use ≥ 3.5 mm screw terminal or 0.1" doubled pins paralleled.

## 3. Control / power bus (`J_BUS`)

Hosted **only** on `ccs_sense`; every `axis_octal` is a bus receptacle. The host is the single source of address and `VDRIVE` for the array.

| Pin | Net | Dir (from CCS) | Notes |
|----:|-----|----------------|-------|
| 1 | `+3V3` | out | Logic |
| 2 | `AGND` | out | |
| 3 | `VDRIVE` | out | ~12 V class adjustable; one rail to all axis boards |
| 4 | `AGND_PWR` | out | Power return |
| 5 | `ADDR_NL0` | out | LS address bit 0 |
| 6 | `ADDR_NL1` | out | |
| 7 | `ADDR_NL2` | out | |
| 8 | `ADDR_NH0` | out | HS / group select bit 0 |
| 9 | `ADDR_NH1` | out | |
| 10 | `ADDR_NH2` | out | |
| 11 | `FWD_EN_n` | out | Active-low; pull-up on axis |
| 12 | `REV_EN_n` | out | Active-low; pull-up on axis |
| 13 | `DEC_EN` | out | Active-high; pull-down on axis |
| 14 | `CCS_RET_AXIS` | in | Axis CCS return (wired to `CCS_X` or `CCS_Y` per harness) |
| 15 | `AXIS_ID0` | out | Optional strap echo / ID |
| 16 | `AXIS_ID1` | out | |

`CCS_RET_AXIS` is **axis-specific in harness wiring**: host provides `J_CCS_X` and `J_CCS_Y` (and `J_CCS_INH` stays on the sense/inhibit path). X boards’ pin 14 → `CCS_X`; Y boards’ pin 14 → `CCS_Y`.

## 4. `ccs_sense` board (host)

### 4.1 Functions

- **Distribution:** address bits, `FWD_EN_n` / `REV_EN_n` / `DEC_EN`, `+3V3`, `VDRIVE` onto `J_BUS`.
- **CCS×3:** `CCS_X`, `CCS_Y`, `CCS_INH` — TL431 + 3296W + OPA192 + IRLZ44N + 1 Ω sense.
- **Sense / inhibit / fold:** 1 kΩ iso, BAT54S, TLV3501; **INH_POL_SEL**; `YA66`═`YB65`═`SENSE_FOLD` with 10 kΩ → AGND.
- **Write-back:** sense comparator → 74AHC74 latch → `DOUT` (and `SENSE_STROBE` from Pico). This path exists only on the host — not on axis boards.
- Pico-compatible header (`J_PICO`): PIO timing + GPIO that drive the bus.
- Plane sense connector `J_PLANE_SENSE`: `YA65`, `YB66`, `YA66`, `YB65` (+ AGND via harness/`J_BUS`).

### 4.2 Tune points (design_choices)

| Ref | Function |
|-----|----------|
| `RTRIM_X` / `RTRIM_Y` / `RTRIM_INH` | Ic/2 ~200–400 mA |
| `VDRIVE` input | Adjustable bench supply (distributed to all axis boards) |
| `JP_INH_POL` | Inhibit polarity select |
| PIO | READ / STROBE / INHIBIT / WRITE aperture |

### 4.3 Sense nets

`YA65`, `YB65`, `YA66`, `YB66`, `SENSE_FOLD` live **only** on this board (+ plane cable). They never appear on `axis_octal`.

### 4.4 PCB connector copper (fab layout)

Schematic keeps the full Pico + sense pin lists. The generated PCB uses **one pad per net** so DRC stays clean without an autorouter:

| Footprint | PCB nets |
|-----------|----------|
| `J_BUS` | Full bus (§3), including `+3V3` / `AGND` / `VDRIVE` / ADDR / enables |
| `J_PLANE_SENSE` | `YA65`, `YB66`, `YA66`, `YB65` (AGND return via bus/`AGND` harness) |
| `J_PICO` | `SENSE_STROBE`, `DOUT`, `PIO_STROBE` (ADDR/EN/power fan-out is on `J_BUS`) |
| `J_CCS_X/Y/INH` | Single pin each (`CCS_X`, `CCS_Y`, `CCS_INH`) |

Harness or short jumpers complete Pico GPIO→bus and AGND returns as needed on the bench.

## 5. `axis_octal` board (identical X/Y, unique `g`)

### 5.1 Identity straps (unique address)

| Strap | Meaning |
|-------|---------|
| `JP_AXIS` | `X` or `Y` — plane connector prefix (`XA`/`XB` vs `YA`/`YB`) |
| `JP_G[2:0]` | Group address `g=0..7` — which HS bank this board owns |

Lines driven: \(L = 8\cdot g + k\) for \(k=0..7\).  
Full 64×64 needs every `(axis, g)` pair once: **2×8 = 16** boards, each with a unique strap (§7 roster).

**Normative group select:** hard-strap `JP_G[2:0]`; bus carries full `ADDR_NH*` / `ADDR_NL*`. The board enables its decode only when bus HS address matches the strap (on-board compare). Bring-up (`g=0` only) may share a single `DEC_EN`. Per-group firmware `DEC_EN` fan-out is a deferred alternate, not a second normative path.

### 5.2 Contents

- Decode: 74AHC138 (HS) + 74AHC238 (LS), bank enables from `J_BUS`.
- DMOS: TBD62783 (HS) + TBD62083 (LS) × FWD/REV for 8 channels.
- Steer: SS14 octal diode law ([hierarchy_abi.md](hierarchy_abi.md) **REQ-HIER-OCTAL**, 34-pin tile budget).
- `J_PLANE`: 16 signals — `{A,B}{0..7}` for this group’s lines.
- `J_BUS`: see §3.

### 5.3 Steer pin budget (one board)

Matches hierarchy_abi octal tile: **34** switch/plane pins conceptually (`HS`, `HSR`, `LS[0..7]`, `LSR[0..7]`, `A[0..7]`, `B[0..7]`). Plane-facing connector exposes the 16 A/B ends; HS/LS stay on-board to DMOS.

## 6. Bring-up wiring (8×8 = three boards)

1. One host `ccs_sense`.
2. Strap axis board A: `JP_AXIS=X`, `JP_G=0`; board B: `JP_AXIS=Y`, `JP_G=0`.
3. Cable `J_BUS` from host to both axis boards (star or short daisy).
4. Map `CCS_X` → X board pin 14; `CCS_Y` → Y board pin 14.
5. Wire X `J_PLANE` A/B[0..7] → plane `XA0..7` / `XB0..7`.
6. Wire Y `J_PLANE` similarly → `YA0..7` / `YB0..7`.
7. Wire `J_PLANE_SENSE` → plane YA/YB 65/66.
8. Apply `VDRIVE`, `+3V3`; set trimpots mid (~300 mA half-select default).

## 7. Scale-out layout (64×64 = 1 host + 2×8 axis)

Full array is **17 PCBs**: **1** × `ccs_sense` + **16** × `axis_octal` (`1 + 2×8`). Same two copper designs as bring-up; only straps and harness change. No axis-PCB redesign.

This section **describes** the 1+16 packaging contract. Coverage **PCB @ 64×64 stays `stub`** until a uniquely addressed 2×8 harness is an explicit gated claim ([coverage_matrix.md](coverage_matrix.md)). Bench / exact \(I_c\) / \(V_{drive}\) remain non-normative ([design_choices.md](design_choices.md)).

### 7.1 Board roster (straps + CCS return + plane lines)

| Board ID | Design | `JP_AXIS` | `JP_G` | `CCS_RET_AXIS` → | Plane lines \(L=8g..8g+7\) |
|----------|--------|-----------|-------:|------------------|---------------------------|
| `HOST` | `ccs_sense` | — | — | (sources `CCS_X` / `CCS_Y` / `CCS_INH`) | Sense via `J_PLANE_SENSE` only |
| `X_g0` | `axis_octal` | X | 0 | `CCS_X` | `XA/XB0..7` |
| `X_g1` | `axis_octal` | X | 1 | `CCS_X` | `XA/XB8..15` |
| `X_g2` | `axis_octal` | X | 2 | `CCS_X` | `XA/XB16..23` |
| `X_g3` | `axis_octal` | X | 3 | `CCS_X` | `XA/XB24..31` |
| `X_g4` | `axis_octal` | X | 4 | `CCS_X` | `XA/XB32..39` |
| `X_g5` | `axis_octal` | X | 5 | `CCS_X` | `XA/XB40..47` |
| `X_g6` | `axis_octal` | X | 6 | `CCS_X` | `XA/XB48..55` |
| `X_g7` | `axis_octal` | X | 7 | `CCS_X` | `XA/XB56..63` |
| `Y_g0` | `axis_octal` | Y | 0 | `CCS_Y` | `YA/YB0..7` |
| `Y_g1` | `axis_octal` | Y | 1 | `CCS_Y` | `YA/YB8..15` |
| `Y_g2` | `axis_octal` | Y | 2 | `CCS_Y` | `YA/YB16..23` |
| `Y_g3` | `axis_octal` | Y | 3 | `CCS_Y` | `YA/YB24..31` |
| `Y_g4` | `axis_octal` | Y | 4 | `CCS_Y` | `YA/YB32..39` |
| `Y_g5` | `axis_octal` | Y | 5 | `CCS_Y` | `YA/YB40..47` |
| `Y_g6` | `axis_octal` | Y | 6 | `CCS_Y` | `YA/YB48..55` |
| `Y_g7` | `axis_octal` | Y | 7 | `CCS_Y` | `YA/YB56..63` |

Every `(axis, g)` pair appears once. `AXIS_ID0/1` stay optional and are **not** required for this roster.

### 7.2 Harness topology (`J_BUS`)

- **Full array (normative recommend):** **star** from host `J_BUS` to all sixteen axis receptacles (short equal-ish stubs). Keeps address/`VDRIVE` returns predictable under sixteen loads.
- **Bring-up (8×8):** star or short daisy between host and the two `g=0` boards is acceptable (§6).
- Keep high-current `VDRIVE` / `AGND_PWR` pairs short; treat long daisy chains as guidance to avoid, not a new electrical REQ.

CCS return harness: every X board pin 14 → host `CCS_X`; every Y board pin 14 → host `CCS_Y`. `CCS_INH` stays on the host sense/inhibit path (not on axis `J_BUS` pin 14).

### 7.3 Plane connector map

For each axis board with group `g` and local index \(k=0..7\):

| `J_PLANE` pin | Net on board | Plane net (X) | Plane net (Y) |
|---------------|--------------|---------------|---------------|
| A\(k\) | `A[k]` | `XA{L}` | `YA{L}` |
| B\(k\) | `B[k]` | `XB{L}` | `YB{L}` |

where \(L = 8\cdot g + k\). Sense/fold ends stay host-only: `J_PLANE_SENSE` → `YA65`, `YB66`, `YA66`, `YB65` (plus AGND return via bus/harness). They never appear on `axis_octal`.

```text
                    ┌─────────────────────────────────────┐
                    │  ccs_sense (HOST ×1)                │
  Pico / PIO ──────►│  ADDR, EN, VDRIVE, +3V3             │
                    │  CCS_X / CCS_Y / CCS_INH            │
                    │  sense + fold + write-back (DOUT)    │
                    └──────────────┬──────────────────────┘
                                   │ J_BUS (star @ 64×64)
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
   X_g0 … X_g7 (8 boards)   Y_g0 … Y_g7 (8 boards)   = 16 axis
          │                        │
          └──────────► ferrite plane XA/XB / YA/YB 0..63
                       + YA65/YB66 via HOST J_PLANE_SENSE
```

### 7.4 Assembly checklist

1. Keep the **same** `ccs_sense` host — sole ADDR / `VDRIVE` / CCS / sense / write-back board.
2. Populate and strap all sixteen axis boards per §7.1 (unique `(JP_AXIS, JP_G)`).
3. Star `J_BUS` from host to all sixteen; wire CCS returns X→`CCS_X`, Y→`CCS_Y`.
4. Wire each `J_PLANE` to the plane line range in the roster.
5. Wire `J_PLANE_SENSE` once from host to plane YA/YB 65/66.

## 8. Generation

```bash
uv run python -m generators.cli --board ccs
uv run python -m generators.cli --board axis
```

Do not hand-edit `kicad/pcb_*/` — fix generators and regenerate.
