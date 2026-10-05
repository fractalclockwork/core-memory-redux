# Target Block Architecture (Sketch)

**Status:** `sketch` (non-authoritative)  
**Must not override** owners in [AUTHORITY.md](AUTHORITY.md).

Intended hierarchical fabric sketch. Generated KiCad lives under [`kicad/`](../kicad/) from [`generators/`](../generators/) (**GATE-L4-FABRIC**); this file remains non-authoritative.

Normative contracts: [system_design_spec.md](system_design_spec.md). Naming / ABI: [naming.md](naming.md). Pin budgets: [hierarchy_abi.md](hierarchy_abi.md). BOM: [component_selection.md](component_selection.md). Coverage: [coverage_matrix.md](coverage_matrix.md).

## Architecture

Three-wire cores (X, Y, sense)—no separate inhibit winding. Sense/inhibit is two independent loops (`YA65`↔`YA66`, `YB65`↔`YB66`), joined on the driver at **`YA66`═`YB65`**. Outer ends `YA65`/`YB66` are shared for differential READ and series inhibit. Drive is coincident half-select into two sinks (`CCS_X`, `CCS_Y`), with inhibit on its own sink (`CCS_INH`). Forward DMOS arrays do READ (−Ic/2); reverse arrays do WRITE (+Ic/2).

```
ADDR_XH/XL[2:0] ──┐
DEC_EN / FWD_EN_n ┼── Decode Block (N=axis, n=bank)
│   138 + 238; four root calls (X/Y, FWD/REV)
▼
X_HS{0..7}_n / X_LS{0..7}_en
│
▼
DMOS Array Block
TBD62783 (HS) / TBD62083 (LS); SS14s on steer tiles
└────────┬─────────┘
▼
CCS_X / CCS_Y / plane
│
YA65/YB66 sense + inhibit
```

**Fail-safe (target):** `DEC_EN` pull-down (off); `FWD_EN_n` / `REV_EN_n` pull-up (inactive). Disabled **138** outputs HIGH → TBD62783 sources OFF. Disabled **238** outputs LOW → TBD62083 sinks OFF. HS inputs `*_n` have 10k pull-ups; LS inputs `*_en` have 10k pull-downs. Never assert both bank enables.

## Intended blocks

| Block | What it does |
|-------|--------------|
| Sense | 1k iso, BAT54S, TLV3501 → 74AHC74 |
| Magnetic Cores | Generated 64×64 weave fixture; center tap `SENSE_FOLD` (`YA66`═`YB65`). 2×2 archived rule is the bring-up stand-in |
| CCS | ×3 (X, Y, inhibit): TL431 + 3296W → OPA192 → IRLZ44N + 1Ω; pin `CCS_RET` |
| Drive arrays | TBD62083/TBD62783 8-channel DMOS |
| Steer | **L4 target:** octal tiles ([hierarchy_abi.md](hierarchy_abi.md)). Monolithic `steer_64` is not the long-term ABI |
| Inhibit | Discrete driver on the folded sense path |
| Decode | One axis 138+238; pins `N_HS{0..7}_n` / `N_LS{0..7}_en`; four root calls (X/Y × FWD/REV) |
| Decode CTRL | Address + enable headers; root binds X/Y and `FWD_EN_n` / `REV_EN_n` |

## Decode map (one axis)

| Ref | Part | Role | ADDR | Hier outs |
|-----|------|------|------|-----------|
| U11 | 74AHC138 | HS | `ADDR_NH[2:0]` | `N_HS0_n` … `N_HS7_n` |
| U12 | 74AHC238 | LS | `ADDR_NL[2:0]` | `N_LS0_en` … `N_LS7_en` |

**Line select:** \(Nn = 8\cdot HS + LS\). Root maps X FWD: `ADDR_NH*`←`ADDR_XH*`, `BANK_EN`←`FWD_EN_n`, outs → `X_HS*_n` / `X_LS*_en`.

## Component selection (as targeted)

### Address decode and DMOS arrays

| MPN | Role | Notes |
|-----|------|--------|
| 74AHC138 | Decode HS | Active-low Y → TBD62783 sources |
| 74AHC238 | Decode LS | Active-high Y → TBD62083 sinks |
| TBD62783 | DMOS source array | High-side drive |
| TBD62083 | DMOS sink array | Low-side drive |

See [component_selection.md](component_selection.md) §1.

### Drive matrix / CCS / Sense

SS14 on steer tiles; CCS (TL431, OPA192, IRLZ44N); Sense (TLV3501, BAT54S, 74AHC74, 1k iso). Soft mid on magnetic sheet. DC-coupled Sense locked.

## Bench cycle (target)

After CCS setpoint:

1. Assert `DEC_EN` and pulse `FWD_EN_n` → READ (−Ic/2)
2. SENSE STROBE → latch DOUT
3. Inhibit (`INH_EN_n`) if restoring/writing 0
4. Pulse `REV_EN_n` → WRITE (+Ic/2)

Plane hookup: `XA*`/`XB*`/`YA*`/`YB*` 0…63 through steer tiles to buses. Sense/inhibit outer ends `YA65`/`YB66`; center tap `YA66`═`YB65` (`SENSE_FOLD`, 10 kΩ to AGND). SPICE e2e stays on the 2×2 ladder until an L3 ideal deck is gated—see [coverage_matrix.md](coverage_matrix.md).

## Array model (target)

* **Loop A:** `(x+y)` even, 2,048 cores. 2×2 stand-in: `YA65` ↔ MCE11 ↔ MCE00 ↔ `YA66`.
* **Loop B:** `(x+y)` odd, the other 2,048. 2×2 stand-in: `YB65` ↔ MCE10 ↔ MCE01 ↔ `YB66`.
* **Center tap:** `YA66`═`YB65`, 10 kΩ→AGND. The plane does not join the loops.
* **Outer ends:** `YA65` / `YB66` for differential READ and series inhibit.

The real plane’s geographic sense split may still need tracing; the checkerboard rule above is the schematic stand-in. Weave AST geometry SSOT: [`generators/mce_array.py`](../generators/mce_array.py).

## Still deferred (not SSOT status)

This sketch must not override owners. Remaining gaps vs the gated tree:

- RP2040 PIO firmware (L3 SIL uses *synthetic* PIO stimuli today)
- Decoder / DOUT LEDs (optional; [design_choices.md](design_choices.md))
- Bench calibration of \(I_c\), inhibit polarity, weave L/DCR
- 64×64 PCB harness claim (1+16 layout is documented in [board_icd.md](board_icd.md) §7; coverage PCB cell stays `stub`)
