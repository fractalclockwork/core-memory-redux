# Hierarchical fabric ABI (steer / magnetic / DMOS)

**Status:** `baseline` (Phase 0 contract)  
**Owns:** steer/magnetic pin budgets, octal tile ABI  
**Does not own:** timing prose, BOM — see [AUTHORITY.md](AUTHORITY.md)

<a id="REQ-HIER-OCTAL"></a>
**REQ-HIER-OCTAL** — L4 target fabric uses octal (or equivalent) tiles + buses; monolithic 256-end sheets are not the long-term ABI.

**Problem this solves:** The physical plane has **256** drive ends (64× XA/XB/YA/YB). If steer and magnetic sheets each expose every A/B end as hierarchical pins, pin counts explode (on the order of **320** steer pins + **258** magnetic pins, with ~**512** duplicated root instances). That budget is hostile to KiCad hierarchy, ERC, and agent-driven generation—and it tempts full-fidelity SPICE at the wrong scale.

**Rule:** hierarchical boundaries match a manufacturing-friendly pin budget and the **bank-level** control plane, not a flat 256-pin root. Simulation scale follows the L0–L4 dial in [system_design_spec.md](system_design_spec.md) (**REQ-SCALE-ANTIX**). Naming: [naming.md](naming.md).

## Target naming

| Artifact | Name | Role |
|----------|------|------|
| Preferred steer fabric | `steer_octal_{X,Y}_g{0..7}.kicad_sch` | One HS group × one axis (FWD+REV) |
| Optional finer grain | `steer_line` | One line, 4 diodes, 6 pins |
| Magnetic fabric | `magnetic_core_64x64.kicad_sch` (generated) | Weave from AST; bus pins on root |
| Not the long-term ABI | Monolithic `steer_64` | Acceptable only as a temporary experiment; not the L4 target |

## Pin budgets

| Boundary | Monolithic (avoid as target) | Octal tiles (target) | Line tiles (alt) |
|----------|-----------------------------:|---------------------:|-----------------:|
| Steer sheet pins | ~320 (64 switch + 256 plane) | 34 per octal × 16 sheets | 6 per line × 128 |
| Magnetic sheet pins | ~258 | Prefer `XA[63:0]`… buses on root | same |
| Root plane pin instances | ~512 (Steer + Magnetic duplicated) | Wire buses once; tiles bind locally | same |

### Octal tile pin list (one axis, one HS group `g`)

Lines \(L = 8\cdot g + k\) for \(k = 0\ldots7\).

| Pin | Count | Nets |
|-----|------:|------|
| `HS`, `HSR` | 2 | `{axis}HS{g}`, `{axis}HS{g}R` |
| `LS[0..7]`, `LSR[0..7]` | 16 | `{axis}LS{k}`, `{axis}LS{k}R` |
| `A[0..7]`, `B[0..7]` | 16 | `{axis}A{L}`, `{axis}B{L}` |
| **Total** | **34** | — |

Diode law:

```text
FWD:  HS  → diode → B{line}
      A{line} → diode → LS{ls}
REV:  HSR → diode → A{line}
      B{line} → diode → LSR{ls}
```

Tile emitters will be part of the planned generator pipeline; they are not in this tree yet.

### Line tile pin list (optional finer grain)

| Pin | Role |
|-----|------|
| `HS`, `LS`, `HSR`, `LSR` | Switch nodes for this line’s group |
| `A`, `B` | Plane ends |

Four SS14s inside. Root or octal parent binds group fan-out.

## Decode and DMOS (control side)

| Block | Pin budget intent |
|-------|-------------------|
| `decode_block` | 8 HS + 8 LS bank outs per axis/direction — **not** 64 line pins |
| DMOS array (TBD62783 / TBD62083) | 8-channel atom matching one decode bank group |
| Sense / fold | Outside Drive/Decode entirely |

Do **not** resurrect per-line TC4427 + discrete MOSFET `drive_block` × 32 as the primary hierarchical ABI. That path multiplies sheets and still dumps plane ends onto steer.

## Magnetic plane

1. **Layout / net semantics:** generated 64×64 MCE sheet from the weave AST (planned `mce_array.py` or equivalent).
2. **SPICE scale proof:** L3 behavioral `ideal_core`, not 4,096 detailed Chan/`coremem` instances.
3. **Root ABI:** prefer KiCad buses `XA[0..63]`, `XB[0..63]`, `YA[0..63]`, `YB[0..63]` plus `YA65` / `YB66`. Do not duplicate 256 hierarchical stubs on both Steer and Magnetic if a single bus vector can feed both.

Fold `YA66`═`YB65` stays **local** on the magnetic sheet (`SENSE_FOLD`); it is not a Drive/Decode hierarchical pin.

## Target sequence (redux)

| Step | Action |
|------|--------|
| 1 | Freeze naming + this ABI in docs (Phase 0) |
| 2 | Prove L1/L2 at n=2 with DMOS BOM; freeze decode/DMOS pinouts |
| 3 | L3 ideal n×n without Chan at scale |
| 4 | Emit octal steer tiles + bus-rooted magnetic fabric from AST (L4) |
| 5 | Never promote monolithic 256-end sheets as the long-term fabric |

## What never enters Drive/Decode

`YA65`, `YB65`, `YA66`, `YB66`, `SENSE_FOLD` — sense/fold only ([naming.md](naming.md) §8).

## Multi-board packaging

Physical split: **one** CCS/sense host (ADDR + `VDRIVE` distribution, CCS, sense, write-back) plus repeated **axis-octal** PCBs — bring-up 2 boards (`g=0`), full array **2×8** with unique group address. Connector pinouts: [board_icd.md](board_icd.md). Do not invent a second electrical pin list here.
