# Theory of Operation (summary)

**Status:** `sketch` (teaching summary; non-authoritative)  
Plane/timing contract: [design_specification.md](design_specification.md). Authority: [AUTHORITY.md](AUTHORITY.md). Cite keys: [references.md](references.md).

## Coincident-current half-select

Each core sits at an X/Y crossing. A full write or destructive read needs roughly \(I_c\) through the selected core. The driver puts \(I_c/2\) on one X line and \(I_c/2\) on one Y line so only the intersection sees full-select; half-selected cores on those lines must not flip.

Forward polarity (READ) and reverse polarity (WRITE/RESTORE) are steered by separate decoder/DMOS banks (`FWD_EN_n` / `REV_EN_n`).

## Three-wire sense and series inhibit

This plane has no fourth inhibit winding. The sense wire is time-multiplexed:

* **READ:** millivolt differential pickup across the folded loop ends `YA65` / `YB66`.
* **INHIBIT (write-0 / restore-0):** \(I_c/2\) forced in series through both sense loops via the external fold `YA66`═`YB65`, opposing a WRITE-1 at the selected core.

Soft mid-tap bias and clamps protect the comparator during inhibit excursions.

## Destructive READ / RESTORE

A READ to zero destroys a stored one. Every access is therefore READ → (optional INHIBIT) → WRITE restore of the latched bit (or the new data). Timing must hold a stable strobe window (~150–300 ns into READ) before inhibit/write edges.

## Why scale is layered

Nonlinear ferrite models do not run at 4,096 cores inside a useful agent loop. Physics calibrates at L0; topology proves at 2×2; full-matrix coincidence uses behavioral cores at L3; CAD fabric tiles the 256 plane ends at L4. See [system_design_spec.md](system_design_spec.md).
