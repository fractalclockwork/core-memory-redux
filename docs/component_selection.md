# Component Selection

**Status:** `baseline` (Phase 0 contract)  
**Owns:** BOM MPNs and part rationale  
**Does not own:** ICD geometry — see [AUTHORITY.md](AUTHORITY.md)

Architecture rationale: [design_choices.md](design_choices.md). Process / anti-explosion: [system_design_spec.md](system_design_spec.md). Target block sketch (non-authoritative): [implementation_summary.md](implementation_summary.md).

Offline datasheet PDFs and appnotes are **deferred** (no `datasheets/` tree in this repo yet). MPN names below are the normative BOM picks.

---

## 1. Address Decoding & Matrix Gate Drive (DMOS pivot)

<a id="REQ-DRV-DMOS"></a>
**REQ-DRV-DMOS** — L2 / normative drive path is AHC decode → TBD62783 / TBD62083 (not TC4427A + FDS8958A).

To avoid a discrete MOSFET + gate-driver forest, the design uses modern DMOS sink/source arrays. These give SN75325-like density with FET switching speed (avoiding Darlington/BJT turn-off drag that would blur the inductive read spike).

| MPN | Role | Package | Key params | Alternate | Datasheet |
|-----|------|---------|------------|-----------|-----------|
| 74AHC138 | 3-to-8 decoder HS (×4: FWD/REV × X-H/Y-H) | SOIC-16 | Active-low Y0–Y7; bank enables | 74HC138 | deferred |
| 74AHC238 | 3-to-8 decoder LS (×4: FWD/REV × X-L/Y-L) | SOIC-16 | Active-high Y0–Y7; same enables as 138 | 74HC238 | deferred |
| TBD62783 | 8-channel DMOS source array (HS) | SOIC-18 | 500 mA/ch; replaces P-FETs + TC4427 | — | deferred |
| TBD62083 | 8-channel DMOS sink array (LS) | SOIC-18 | 500 mA/ch; replaces N-FETs + TC4427 | — | deferred |

**Architecture impact:** TBD62x83 inputs accept 3.3 V AHC decoder outputs directly. 74AHC138 (active-low) drives TBD62783 sources; 74AHC238 (active-high) drives TBD62083 sinks. This discards the old discrete MOSFET staged bring-up as the primary architecture.

**KiCad symbol vs MPN:** pin-compatible lib_id `74xx:74HC138` / `74xx:74HC238` with Value set to the ordered MPN (`74AHC138` / `74AHC238`). Do not treat the HC lib_id as the BOM part.

---

## 2. The Steer Matrix (64×64)

| MPN | Role | Package | Key params | Alternate | Datasheet |
|-----|------|---------|------------|-----------|-----------|
| SS14 | Steering Schottky | SMA | 1 A, low Vf, fast recovery | SS16 (higher Vr) | deferred |

The 8×8 addressing geometry creates sneak paths across unselected lines. SS14 diodes remain mandatory on the driver at matrix outputs. The plane itself contains no diodes. Long-term fabric: octal steer tiles ([hierarchy_abi.md](hierarchy_abi.md)).

---

## 3. Constant-Current Sink (manual)

Low-side matrix returns share an adjustable CCS so \(I_c/2\) stays flat into the inductive load (target band ~200–400 mA).

| MPN | Role | Package | Key params | Alternate | Datasheet |
|-----|------|---------|------------|-----------|-----------|
| TL431 | Precision shunt reference | SOT-23 / TO-92 | Stable Vref for setpoint divider | TLV431 (lower Vref) | deferred |
| Bourns 3296W | 10 kΩ multi-turn trimpot | 3296W | Bench adjustment of \(I_c/2\) | 3296Y (side adjust) | deferred |
| OPA192 | Feedback error amp | SOIC-8 | 10 MHz GBW, fast slew | OPA191 | deferred |
| IRLZ44N | Throttle N-MOSFET (CCS) | TO-220 / DPAK family | Linear-region dissipation | AOD4184 | deferred |
| 1.0 Ω 1% 2 W | Current sense | 2512 SMD | Low inductance thick film | 0.47 Ω (if higher I) | — |

Speed matters when the drive pulse hits: the op-amp must contain inductive overshoot within the microsecond pulse. The throttle MOSFET runs in its linear region and must handle the waste heat.

---

## 4. Sense & Inhibit Front End (pins 65 & 66)

Isolates the differential read pulse from common-mode noise and protects the amp during inhibit.

| MPN | Role | Package | Key params | Alternate | Datasheet |
|-----|------|---------|------------|-----------|-----------|
| BAT54S | Dual series Schottky clamp | SOT-23 | Clamp YA65/YB66 to rails | BAT54C | deferred |
| TLV3501 | High-speed comparator (Sense) | SOT-23-5 / SOIC | 4.5 ns tpd, 3.3 V logic out | LT1016 (legacy ±5 V class) | deferred |
| 74AHC74 | D flip-flop read latch | SOIC-14 | Captures comparator on SENSE STROBE | 74LVC74 | deferred |

Sense uses **TLV3501** (not LT1016): single-supply 3.3 V logic-friendly output and short propagation delay. Classic comparator layout/strobe advice (Linear AN13) remains useful; PDF deferred. Latch clocks ~150–300 ns into READ to miss capacitive ringing and catch the core flip.

---

## 5. Hardware Testability

| MPN / series | Role | Package | Key params | Alternate | Datasheet |
|--------------|------|---------|------------|-----------|-----------|
| Keystone 5000-series | Loop test points | Through-hole loop | SENSE STROBE, DOUT, Isense | Equivalent loop TP | deferred |
| 2N7002 | LED buffer N-MOSFET | SOT-23 | Decoder / DOUT indicators | 2N7002K | deferred |
| 0805 LED | Diagnostic indicators | 0805 | Address + data visibility | — | — |

Populate loop-style test points on SENSE STROBE, the sense-latch output, and the current-sense node. Decoder/DOUT LEDs are planned but not a frozen schematic requirement ([design_choices.md](design_choices.md) open decisions).

---

## 6. Multi-board PCB BOM (quantities)

Packaging split: [board_icd.md](board_icd.md). MPNs above remain normative; this section owns **how many** of each part go on `ccs_sense` vs `axis_octal`, and roll-ups for bring-up vs full array.

Machine-readable roll-up: [`bom_multiboard.csv`](bom_multiboard.csv).

### 6.1 Per `ccs_sense` board (qty 1 forever)

| MPN / value | Role | Pkg | Qty / board |
|-------------|------|-----|------------:|
| TL431 | CCS Vref (×3 channels) | SOT-23 | 3 |
| Bourns 3296W 10 kΩ | CCS trim (`RTRIM_X/Y/INH`) | 3296W | 3 |
| OPA192 | CCS error amp | SOIC-8 | 3 |
| IRLZ44N | CCS throttle MOSFET | TO-220 / DPAK | 3 |
| 1.0 Ω 1% 2 W | CCS sense | 2512 | 3 |
| BAT54S | Sense clamp | SOT-23 | 1 |
| TLV3501 | Sense comparator | SOT-23-5 | 1 |
| 74AHC74 | Write-back latch → `DOUT` | SOIC-14 | 1 |
| 1 kΩ | Sense isolation | 0805 | 2 |
| 10 kΩ | `SENSE_FOLD` soft bias | 0805 | 1 |
| PinHeader 1×16 | `J_BUS` host | 2.54 mm | 1 |
| PinHeader 1×4 | `J_PLANE_SENSE` | 2.54 mm | 1 |
| PinHeader 1×3 | `J_PICO` timing/`DOUT` (PCB) | 2.54 mm | 1 |
| PinHeader 1×1 | `J_CCS_X/Y/INH` | 2.54 mm | 3 |
| Raspberry Pi Pico H (or header) | PIO timing — packaging open | — | 1 |
| Keystone 5000-series | TP: STROBE / DOUT / Isense | loop | 3 |

Supporting divider/bypass passives around TL431/OPA192 are implied by the CCS topology and will appear as schematic detail densifies; do not invent extra MPNs here.

### 6.2 Per `axis_octal` board (identical X/Y; strap `JP_AXIS` / `JP_G`)

One board = one HS group (`g`), FWD+REV, 8 lines → **32× SS14** (4 diodes/line).

| MPN / value | Role | Pkg | Qty / board | Notes |
|-------------|------|-----|------------:|-------|
| 74AHC138 | HS decode FWD + REV | SOIC-16 | 2 | Board enables when `ADDR_NH` matches `JP_G` |
| 74AHC238 | LS decode FWD + REV | SOIC-16 | 2 | 8 LS sinks per direction |
| TBD62783 | HS DMOS FWD + REV | SOIC-18 | 2 | 1 of 8 channels used for this group’s `HS`/`HSR` |
| TBD62083 | LS DMOS FWD + REV | SOIC-18 | 2 | All 8 channels used |
| SS14 | Steer Schottky | SMA | **32** | Diode law per [hierarchy_abi.md](hierarchy_abi.md) |
| 10 kΩ | `FWD_EN_n` / `REV_EN_n` pull-up; `DEC_EN` pull-down | 0805 | 3 | Fail-safe |
| PinHeader 1×16 | `J_BUS` | 2.54 mm | 1 | |
| PinHeader 1×16 | `J_PLANE` A/B[0..7] | 2.54 mm | 1 | |
| PinHeader 1×2 | `JP_AXIS` | 2.54 mm | 1 | |
| PinHeader 1×3 | `JP_G` | 2.54 mm | 1 | |

### 6.3 System roll-up

| Build | `ccs_sense` | `axis_octal` | SS14 total | TBD62783 | TBD62083 | 74AHC138 | 74AHC238 |
|-------|------------:|-------------:|-----------:|---------:|---------:|---------:|---------:|
| **Bring-up 8×8** | 1 | 2 | 64 | 4 | 4 | 4 | 4 |
| **Full 64×64** | 1 | 16 | 512 | 32 | 32 | 32 | 32 |

Matches [`bom_multiboard.csv`](bom_multiboard.csv) columns `Bringup_1ccs_2axis` / `Full_1ccs_16axis` and the board roster in [board_icd.md](board_icd.md) §7.1 (**1 + 2×8**). CCS/sense ICs stay at the **per-host** counts in §6.1 for both builds (one host). Diagnostic LEDs / 2N7002 remain optional ([design_choices.md](design_choices.md)).
