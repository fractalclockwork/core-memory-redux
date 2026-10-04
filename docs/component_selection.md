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

**KiCad symbol vs MPN (when sheets exist):** pin-compatible lib_id `74xx:74HC138` / `74xx:74HC238` with Value set to the ordered MPN (`74AHC138` / `74AHC238`). Do not treat the HC lib_id as the BOM part.

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
