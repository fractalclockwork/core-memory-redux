# Design Choices

**Status:** `baseline` for recorded tradeoffs; open rows below are `open`  
**Owns:** tradeoffs + open decisions  
**Does not own:** frozen ICD — see [AUTHORITY.md](AUTHORITY.md)

Part-level picks: [component_selection.md](component_selection.md). Net grammar / call model: [naming.md](naming.md). Pin budgets: [hierarchy_abi.md](hierarchy_abi.md). Normative freeze table: [system_design_spec.md](system_design_spec.md) §1.

## Three-wire cores: no separate inhibit winding

Each core carries **X**, **Y**, and **sense** only (classic 3-wire). There is no fourth inhibit wire through the array. WRITE-0 inhibit reuses the sense path at high current; READ uses the same path as a millivolt differential. That time-multiplex forces Sense-block isolation (1 kΩ), clamps, and soft center-tap bias before Inhibit can source `YA65` and sink `YB66` into the CCS.

## Series differential sense (shared READ / inhibit loops)

The plane has two independent sense/inhibit loops (`YA65`↔`YA66` and `YB65`↔`YB66`), 2,048 cores each. The driver joins them with an external center-tap jumper **`YA66`═`YB65`** and uses the outer ends (`YA65`/`YB66`) as a differential pair. That rejects common-mode drive noise that would swamp a single-ended pickup, and it keeps a single TLV3501 and a single inhibit driver. A dedicated sense-only winding is not available on this hardware, so the driver must protect and bias this shared path for both READ (small-signal) and INHIBIT (high current).

Each loop’s DCR and inductance are half of a continuous 4,096-core weave. Wiring the loops in series presents that full-array L and DCR to the driver, so \(V_{drive}\) and the CCS current stay at \(I_c/2\).

If the series-loop noise floor is too high on the bench, the deferred alternative is to drive and sense the loops in parallel: `YA65` and `YB65` both fed from the inhibit P-FET, `YA66` and `YB66` both returned to `CCS_INH` (that sink then takes \(I_c\), and \(V_{drive}\) can be lower), plus a second TLV3501 whose output is OR’d with the first. That is not the 2×2 sim fixture or the initial build target.

## The TBD62083/TBD62783 matrix array

Driving 64 X and 64 Y lines as discrete half-bridges would explode component counts and hierarchical sheet counts. The design uses an 8×8 crossbar with Toshiba DMOS sink/source arrays (TBD62083/TBD62783). These replace dozens of discrete MOSFETs and gate drivers, giving SN75325-like density without BJT turn-off drag that would blur the inductive read spike. Twelve address bits feed four decode banks (X/Y × FWD/REV); each bank’s 8+8 outputs trigger the DMOS arrays directly.

## Steering diodes on the driver board

The 8×8 addressing geometry creates passive matrix sneak paths across unselected lines. Discrete Schottky steering diodes (SS14) remain mandatory on the driver at matrix outputs. The core PCB contains no diodes. At L4, diodes live in octal steer tiles rather than one monolithic 256-end sheet ([hierarchy_abi.md](hierarchy_abi.md)).

## Why not simulate all 256 ends at full fidelity

The plane’s 256 drive ends are a **physical** fact. Making them the default unit of SPICE fidelity or KiCad hierarchical pins recreates the failure mode this rewrite avoids: root-sheet pin explosion, duplicated stub nets, and nonlinear transients that cannot finish at n=64.

Instead:

* Control and L2 ABI stay at **bank level** (8 HS + 8 LS) with DMOS 8-channel atoms ([naming.md](naming.md)).
* L0 Chan physics stays ≤16 cores; L1/L2 prove the cycle at **2×2**; L3 scales with behavioral `ideal_core` ([system_design_spec.md](system_design_spec.md) §4–5).
* L4 compresses plane ends with octal tiles and KiCad buses ([hierarchy_abi.md](hierarchy_abi.md)).
* Scale claims require a [coverage_matrix.md](coverage_matrix.md) row.

## Prototype 2×2 before scaling lines

Bring-up and L1/L2 prove a full READ → STROBE → INHIBIT → WRITE cycle on the **2×2** before trusting n×n SIL. Drive hierarchy targets 8-channel DMOS arrays; decode is one hierarchical page per axis (74AHC138 HS + 74AHC238 LS). KiCad paths are future targets—this repo is docs-bootstrap until generators and sheets exist. Scale gates: [system_design_spec.md](system_design_spec.md), [coverage_matrix.md](coverage_matrix.md).

## Soft mid-bias and input clamps on sense

During inhibit, the outer ends see large excursions. BAT54S clamps dump spikes into the rails; a soft resistive bias from the center tap (`YA66`/`YB65`) to AGND keeps the comparator inputs from floating between cycles. Isolation resistors (e.g. 1 kΩ in Sense) limit clamp current into the amp (~8 mA into clamps at 12 V). This favors a modern fast comparator (TLV3501) over older ±supply parts that assumed different front-ends.

A 1:1 pulse-transformer sense front-end was considered and **deferred**: on this 3-wire plane the same fold ends carry series inhibit, so a low-DCR primary across those pins would shunt inhibit current around the cores. AC-coupling the primary would still slam inhibit edges onto the secondary and force clamps/blanking, erasing the BOM win. DC-coupled Sense stays.

## Manual TL431 + trimpot CCS

Bench bring-up needs a knob for \(I_c/2\) while probing cores of uncertain coercivity (400–800 mA full-select estimate). A TL431 reference and multi-turn 3296W divider set the OPA192 target without firmware or a DAC. A later digital setpoint (DAC or PWM + filter) can replace the trimpot once the operating current is known; the MOSFET + sense-resistor power stage stays.

## AHC logic and DMOS compatibility

The timing controller is 3.3 V (RP2040). 74AHC138/238 accept 3.3 V inputs with short propagation delay. The DMOS arrays (TBD62083/783) accept these logic levels directly—no dedicated level shifters. Low-side decode uses 74AHC238 (active-high) to match sinks; high-side uses 74AHC138 (active-low) to match sources.

FWD vs REV steering uses duplicated decoder banks gated by `FWD_EN_n` / `REV_EN_n`. That removes a mux layer and keeps fail-safe behavior native.

## RP2040 PIO for timing

READ → strobe → inhibit → WRITE needs fixed delays on the order of hundreds of nanoseconds. Main-CPU GPIO toggling under an OS or interrupt load introduces jitter that corrupts sense windows. PIO state machines give cycle-accurate multi-pin sequences while application code runs elsewhere. Another MCU with equivalent programmable I/O could substitute; the requirement is hardware sequencing, not the Pico brand.

## Decisions still open

| Topic | Notes |
|-------|--------|
| Exact \(I_c\) / \(I_c/2\) setpoint | Characterize on the real plane; trimpot covers 200–400 mA half-select for now |
| \(V_{drive}\) rail voltage | Must satisfy DMOS voltage drops, diode drops, and inductive headroom; value not frozen |
| Inhibit polarity vs READ | Source is `YA65` and sink is `YB66`; whether that direction matches the core’s read polarity is still a bench question |
| On-board vs off-board RP2040 | Pico header vs soldered MCU vs external timing pod |
| Final CCS throttle MOSFET | IRLZ44N in CCS; AOD4184 (or similar) remains a thermal/package alternate |
| Diagnostic LED set | Planned on decoder outputs and DOUT; not yet a frozen schematic requirement |
