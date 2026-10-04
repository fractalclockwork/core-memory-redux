# Magnetic Core Memory Drive and Sense Circuit: Design Specification

**Status:** `baseline` (Phase 0 contract)  
**Owns:** plane physical ICD, sense/inhibit electrical contract, timing sequence  
**Does not own:** process phases, L0–L4 gates, BOM tables — see [AUTHORITY.md](AUTHORITY.md)

Normative plane interface, drive architecture, and timing contract for this rewrite. Part of the **normative target architecture** in [system_design_spec.md](system_design_spec.md) §1. Narrative context: [theory_of_operation.md](theory_of_operation.md). Citation keys `[cite: 1]` / `[cite: 2]`: [references.md](references.md).

## 1. Physical Parameters & Interface Specification

<a id="REQ-ICD-PLANE"></a>
**REQ-ICD-PLANE**

* **PCB Dimensions:** The magnetic core plane is constructed on a 9-inch square PCB featuring four edge connector interfaces labeled XA, XB, YA, and YB [[cite: 1](references.md#core-plane-physical-evidence)].
* **Connector Type:** Dual-readout staggered edge connector.
* **Contact Dimensions:** Pins are 0.125" wide with a 0.1875" (3/16") center-to-center pitch on each face.
* **Staggered Layout:** Odd-numbered pins are located on the top face [[cite: 1](references.md#core-plane-physical-evidence)], and even-numbered pins are located on the bottom face [[cite: 2](references.md#core-plane-physical-evidence)]. Pin 1 begins 1.3125" (1-5/16") from the right edge, offsetting the top and bottom contacts by exactly 0.0625" to maximize contact area while preventing wiper shorts during insertion.
* **Axis Connectors:**
    * **X-Axis (XA, XB):** 64 pins total. Requires a 32-position, dual-readout staggered receptacle.
    * **Y-Axis (YA, YB):** 66 pins total. Requires a 33-position, dual-readout staggered receptacle.
* **Matrix Capacity:** 64×64 bidirectional drive lines yield exactly 4,096 cores (512 bytes).
* **Pin numbering vs address:** Physical edge contacts are labeled **1–64** (drive) plus Y **65/66** (sense). Schematic and firmware address drive lines **0–63**. Mapping: physical pin \(p\) ↔ logical index \(p-1\). Pins 65/66 are **not** drive lines and are **not** part of the Drive/Decode hierarchical pin chain — see §1.1 and §2.
* **Dual sense loops:** Pins 65/66 on YA and YB are two independent loops, 2,048 cores each (`YA65`↔`YA66` and `YB65`↔`YB66`). The plane does not join them. Each loop’s DCR and inductance are half of a single weave through all 4,096 cores. The driver ties `YA66`═`YB65` (external center tap) so the series path is `YA65` → Loop A → jumper → Loop B → `YB66`. Series connection restores the full-array L and DCR. [[cite: 1](references.md#core-plane-physical-evidence),[cite: 2](references.md#core-plane-physical-evidence)]

### 1.1 Three naming layers (keep separate)

Normative net grammar, block ABI, buses, and scale path: **[naming.md](naming.md)**. Fabric pin budgets: **[hierarchy_abi.md](hierarchy_abi.md)**. Mixing physical (1–64 / Y 65–66), syntax (`XA0`…, block `N`/`n`), and semantic (drive vs sense/fold) layers is a recurring source of schematic and doc bugs. Drive/Decode hierarchical pins only cover the matrix control plane (bank-level)—do not extend that chain to 65/66, and do not put all 256 plane ends through decode sheets.

## 2. Sense and Inhibit Architecture (Pins 65 & 66)

<a id="REQ-ICD-FOLD"></a>
**REQ-ICD-FOLD**

Each core is a **three-wire** element (X, Y, sense). There is **no separate inhibit winding**; inhibit is series current on the folded sense wire, time-multiplexed with READ.

* **Two loops + external fold:** Loop A `YA65`↔`YA66`; Loop B `YB65`↔`YB66`. Driver jumper **`YA66`═`YB65`**. Outer ends: `YA65` / `YB66`. The 2×2 magnetic fixture is the schematic stand-in (one diagonal per loop).
* **Common-Mode Noise Rejection (Read Phase):** A high-speed differential comparator (TLV3501; see [component_selection.md](component_selection.md)) across `YA65` / `YB66` isolates the millivolt flip spike. Classic techniques: Linear AN13 (PDF deferred to a later datasheet/appnote pass).
* **Center-Tap Bias:** Soft-bias the center tap `YA66`/`YB65` (10 kΩ → AGND), not a hard AGND short, so inhibit current traverses both loops into the CCS.
* **Series Inhibit Drive (Write Phase):** Source \(V_{drive}\) into `YA65` and sink `YB66` to `CCS_INH` at \(-I_c/2\), so current flows Loop A, crosses `YA66`═`YB65`, and returns through Loop B — all cores in series. A parallel-drive alternative (both loops at once, two comparators) is deferred; see [design_choices.md](design_choices.md).

## 3. Drive Architecture (64×64 Matrix)

<a id="REQ-ICD-DRIVE"></a>
**REQ-ICD-DRIVE** — electrical/matrix contract. Part MPNs: [component_selection.md](component_selection.md) **REQ-DRV-DMOS**. Anti-explosion: [system_design_spec.md](system_design_spec.md) **REQ-SCALE-ANTIX**.

* **Matrix Structure:** Group the 64 lines per axis into 8 rows and 8 columns. Implement 8 High-Side source switches and 8 Low-Side sink switches per axis, per direction (Forward for READ, Reverse for WRITE). Control and simulation stay at this **8×8 bank** geometry—not as 256 independent full-fidelity switch models.
* **Address Decoding:** A 12-bit address word maps to this geometry. 6 bits decode X (3 HS + 3 LS), 6 bits decode Y. Decoders: 74AHC138 HS / 74AHC238 LS; see [component_selection.md](component_selection.md).
* **DMOS Array Switching:** High-current switching uses monolithic 8-channel DMOS arrays (TBD62783 sources / TBD62083 sinks). These take AHC decoder outputs directly. Discrete per-line MOSFET + TC4427 drive is not the normative architecture.
* **Steering Diodes:** Because there are no discrete diodes on the memory plane itself [[cite: 1](references.md#core-plane-physical-evidence),[cite: 2](references.md#core-plane-physical-evidence)], SS14 Schottkys sit on the driver at matrix outputs (octal steer tiles at L4; see [hierarchy_abi.md](hierarchy_abi.md)).

## 4. Current Recommendations (\(I_c\))

* **Coercive Current (\(I_c\)):** Given the 0.125-inch core diameter, expect a full-select current between 400 mA and 800 mA. Exact setpoint is non-normative until bench characterization ([design_choices.md](design_choices.md)).
* **Drive Regulation:** Half-select (\(I_c/2\), ~200–400 mA) must be regulated on each axis. Three copies of the same adjustable CCS: `CCS_X`, `CCS_Y`, `CCS_INH`. One shared sink would split the coincident pulse so the addressed core never sees full-select. Power op-amp + N-channel MOSFET + sense resistor holds each path flat into the inductive load.

## 5. Timing & Sequencing

<a id="REQ-ICD-TIMING"></a>
**REQ-ICD-TIMING**

Core memory operations require sub-microsecond, deterministic pulse sequencing. A READ destroys the data, so every access is a READ / RESTORE cycle.

1. **READ Phase:** Drive \(-I_c/2\) into the target X and Y lines.
2. **SENSE STROBE:** Wait ~150–300 ns for capacitive ringing to settle, then clock the D-flip-flop on the differential comparator across `YA65` / `YB66`.
3. **INHIBIT Phase:** If writing/restoring a '0', drive \(-I_c/2\) from `YA65` through the `YA66`═`YB65` center tap and out `YB66`.
4. **WRITE Phase:** Drive \(+I_c/2\) into the target X and Y lines.

Software bit-banging introduces cycle jitter that corrupts sense windows. Hardware sequencing (RP2040 PIO or equivalent programmable I/O) is the normative timing requirement; the Pico brand is replaceable.
