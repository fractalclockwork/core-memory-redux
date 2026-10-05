# A record of the driver, so far

This is a snapshot of a ground-up magnetic core memory driver and the digital twin that is being built beside it. The plane is a 64×64 ferrite array. The work is a rewrite, arranged so an agent can move against a frozen contract and a simulator. Three things count as done, when they are done: the process, the circuit, and the documentation of both. This essay is only the telling of where that stands on 4 October 2026.

The figures below were rendered that day on a machine named hellway, from the same stimuli the gate tests already run. The samples quoted in the text are in [figures/results.json](figures/results.json). Drive current in these decks is a simulation assumption, \(I_c = 600\,\mathrm{mA}\) so \(I_c/2 = 300\,\mathrm{mA}\). The exact operating current is still an open bench question; the owner for that list is [docs/design_choices.md](../docs/design_choices.md).

If a sentence here and an owner document disagree, the owner wins. This folder does not feed the design.

## The array, in one sitting

Each core sits at a crossing of an X wire and a Y wire. A full write or a destructive read wants about \(I_c\) through that one core. The driver puts \(I_c/2\) on one X line and \(I_c/2\) on one Y line. Only the intersection sees the full current. Every other core on those two lines is half-selected, and a half-selected core has to keep its bit.

The cores on this plane are three-wire. There is no separate inhibit winding. The sense wire does both jobs, at different times. During a read it is a millivolt pickup. During a write of zero it carries \(I_c/2\) in series, opposing the write so the selected core stays at zero. The plane folds that sense path outside the array: two loops joined by a jumper, so one comparator and one inhibit driver can see the whole weave. A read to one destroys a stored one, so every access is a read, then a write that puts the bit back, or writes the new one. The sense strobe has to land in a quiet window after the read edge and before the inhibit and write edges, on the order of 150–300 ns into the read.

That is the whole machine the rest of this record is trying to drive. The contract for the fold, the sense path, and the timing lives in [docs/design_specification.md](../docs/design_specification.md). A shorter teaching pass is [docs/theory_of_operation.md](../docs/theory_of_operation.md).

## Working with agents

The method is a box around the agent. Each kind of fact has one owner. Plane geometry, net names, the bill of materials, pin budgets, open decisions, and scale claims live in different files, and the map of who owns what is [docs/AUTHORITY.md](../docs/AUTHORITY.md). Downstream text links to the owner. It does not grow a second copy of the fold, the part numbers, or the gate criteria.

When two owners seem to conflict, the work stops and a person decides. Chat is a scratchpad. A scale claim is allowed to appear in one place, the coverage matrix, and only after a run has earned the cell. That is how an agent is kept from inventing a third architecture in the middle of a task: the next sentence has to land in a document that already has a job, or it does not land.

The practical shape of a task is therefore small. Read the map, open the owner for the fact at hand, change that fact or the simulation that checks it, and leave the other documents alone. The coverage matrix, as of this record, says a single core and the 2×2 driver path have passed in SPICE, and the ideal plant has passed at 8×8 and 64×64. The generated schematic has passed at 2×2 and at 64×64. The two board designs have passed ERC and DRC at the 8×8 bring-up quantity. The 64×64 board harness and the bench column are still empty. Those sentences are the matrix’s, in [docs/coverage_matrix.md](../docs/coverage_matrix.md).

## Simulation in the loop

A nonlinear ferrite model of all 4,096 cores will not finish inside a loop an agent can wait on. The ladder answers one question at a time, on the smallest plant that can answer it.

```mermaid
flowchart LR
  L0[L0 one Chan core]
  L1[L1 2x2 cycle]
  L2[L2 address path at n equals 2]
  L3[L3 ideal core at N]
  L4[L4 octal fabric and boards]
  L0 --> L1 --> L2 --> L4
  L1 --> L3 --> L4
```

L0 asks whether the physics we are willing to trust can hold a half-select, tell a stored one from a stored zero on a destructive read, and accept a write-back. It is one core, a Chan-threshold subcircuit, and it stays small: at most sixteen instances, and never the proof at n=64.

L1 asks whether four cores, wired as a 2×2 with the external sense fold, can run a full write, read, inhibit, and restore, and whether a failed current source on one axis leaves the addressed core alone. The switches here are ideal.

L2 asks the same cycle with the address pins in the path: decode, the forward and reverse banks, and the DMOS polarity the board will actually use. It still sits on the 2×2. It checks that both banks asserted together produce no drive, that an idle enable produces no drive, and that the strobe window still sees the destroyed bit while the bank is on.

L3 asks whether a whole matrix can be walked. The core there is a threshold law: full-select flips, half-select holds, a destructive read of a one emits a fixed sense pulse. Each line carries a lumped resistance, inductance, and capacitance, and the plant waits out that settle before it treats the bit as valid. Stimuli are a synthetic stand-in for the PIO sequence. Patterns are a full diagonal and a random sparse set, at 8 and at 64, plus a few hundred continuous cycles at 64. Chan stays behind, on L0.

L4 asks whether that same driver can be drawn as sheets and as two boards without making the 256 drive ends into 256 pins. It is KiCad, emitted from the weave, and checked by `kicad-cli` 10.0.6. The bench is still later. The rules for the ladder, and the reason the 256 drive ends are not the unit of simulation or of a hierarchical sheet, are in [docs/system_design_spec.md](../docs/system_design_spec.md) and [docs/hierarchy_abi.md](../docs/hierarchy_abi.md).

Each layer is a pytest module. A thin wrapper, `scripts/run_gate.py`, runs one gate by name. A green run is what turns a coverage cell from a plan into a pass. The essay does not add a new test. It replays the ones that already exist and draws them.

## What the runs show

### One core

The first question is half-select. Both axes carry 300 mA together, which is a full-select write, and the remanent state sits at +1. Then only one axis carries 300 mA. The magnetomotive force during that second pulse is 0.300 A, and the state afterward is still +1. The shaded band in the figure is that one-axis pulse.

![Half-select holds a stored 1. The shaded band is a single axis at 300 mA.](figures/l0_half_select.png)

The second question is whether a read can tell the bits apart. A stored one, read with both axes at −300 mA, produces a sense spike of 40.0 V inside the read window and leaves the state at −1. The same read of a stored zero, in that same window, produces a sense peak of \(4 \times 10^{-15}\,\mathrm{V}\), which is numerical zero. The early spike on the stored-zero trace is the write that put the zero there, starting from a stored one; the shaded band is the read, and that read is quiet.

The 40 V figure is the model’s sense node. A flux scale inside the Chan subcircuit sets the height of these numerical peaks. The gate asks for discrimination: the stored-one peak has to dwarf the stored-zero peak. It does. A bench measurement on the real plane will be millivolts, and this plot is not that measurement.

![Destructive read of a stored 1, over the same current shape used to read a stored 0.](figures/l0_read_discrimination.png)

The third question is restore. The core is written to +1, read back through zero to −1, and written again to +1. Sampled after each phase, the state is +1, then −1, then +1.

![Write, destructive read, and write-back on one core.](figures/l0_restore.png)

### A 2×2 cycle

Four cores share the fold. The addressed core is (0,0). The run writes a one, reads it, drives the inhibit current through the sense path, and writes the one back.

After the write, (0,0) is at +1. The two half-selected neighbors, (0,1) and (1,0), stay at −1, and so does the unselected core; on the plot those three traces lie on top of each other. The read drives the addressed core to −1 and puts a 40.0 V spike on the sense node, same numerical sense scale as the single core. During inhibit the addressed magnetomotive force is 0.300 A, the half-current on the sense wire, and the core stays at the zero the read just wrote. The restore returns (0,0) to +1.

The bands on the figure are the four phases: write, read, inhibit, restore.

![Four cores through write, read, inhibit, and restore. Neighbors stay at −1.](figures/l1_cycle.png)

The regression that has to keep passing is a broken X source. Y is enabled, X is open, and the addressed core starts as a stored one. A single axis must not flip it. After the pulse, (0,0) is still at +1.

![With the X current source open, the addressed core holds its stored 1.](figures/l1_ccs_failure.png)

### The address path

L2 keeps the 2×2 and inserts the decode path in front of it. Address (0,0), a reverse-bank write, then a forward-bank read. After the write, (0,0) is +1 and the half-selected neighbors are still −1. After the read, (0,0) is −1. The sense spike on that read is 40.0 V, again the model node, sitting on the leading edge of the forward pulse.

The dashed line is the strobe, 1.75 µs, which is 200 ns after the read edge. At that instant the addressed state is already −1, and the X line enable is still 1. The bit is valid while the bank is still on. That is the window the timing contract is trying to protect.

![Reverse write, then forward read, with the strobe marked 200 ns into the read.](figures/l2_address_path.png)

The mutex is the fail-safe. Forward and reverse are both asserted, with decode enabled. The X line enable stays at 0, and a stored one on (0,0) is still +1 at the end of the run. An idle enable, covered by the same gate and not drawn here, does the same thing: no drive, core holds.

![Both banks asserted: the line enable stays off and the core holds.](figures/l2_mutex.png)

### The full matrix, idealized

L3 does not have a SPICE waveform to show. The plant applies settled currents after a lumped line delay, then updates a threshold core. The honest pictures are the array and the clock.

An 8×8 written with ones on the diagonal and zeros elsewhere holds exactly eight ones, on that diagonal. The same plant, the same write, is what runs at 64×64. The small map is the one a person can read.

![8×8 ideal cores after a diagonal write. Stored 1 is the warm diagonal.](figures/l3_diagonal_n8.png)

Wall time on hellway, for the same workloads the gate runs:

| Run | Wall time |
|-----|----------:|
| 8×8 diagonal, every cell written and checked | 2.69 ms |
| 8×8 sparse, 16 cells, seed 42 | 0.48 ms |
| 64×64 diagonal, every cell written and checked | 3.68 s |
| 64×64 sparse, 64 cells, seed 7 | 32.0 ms |
| 64×64, 500 random cycles, seed 3 | 182 ms |

The long bar is the full diagonal at 64, because that walk touches all 4,096 cores twice: a write, then a read and restore. The 500-cycle run is a thin sample of the same plant, which is why it finishes faster than the exhaustive diagonal. All five finished well inside the gate’s two-minute budget. The axis is logarithmic so the millisecond runs stay visible next to the 3.68 s bar.

![Wall-clock time of the ideal-core patterns on hellway, 4 October 2026.](figures/l3_runtimes.png)

## The fabric, then the boards

### Octal tiles

The 256 drive ends remain a physical fact of the plane. They are not the pin list of a sheet. A monolithic steer sheet would carry on the order of 320 pins, and the root would then instance those ends twice. L4 emits octal tiles instead: 34 pins each, one axis and one group of eight lines. The 64×64 fabric has sixteen of those tiles and 512 steering diodes. The 2×2 bring-up fabric has two tiles, X and Y at group 0, and 16 diodes. Both projects put four decode calls on the root. The fold stays local to the magnetic sheet: `YA66` and `YB65` join as `SENSE_FOLD`, and the fabric manifest records the sense nets as disjoint from the drive tiles.

KiCad 10.0.6 electrical rules on both projects, stamped 17:52 on 4 October 2026, returned empty error lists. The gate is **GATE-L4-FABRIC**. A topological fix goes back through the weave AST and the emitter; the sheets under `kicad/bringup_2x2/` and `kicad/driver_64x64/` are generated. Pin budgets live in [docs/hierarchy_abi.md](../docs/hierarchy_abi.md). Geometry lives in [`generators/mce_array.py`](../generators/mce_array.py).

### Two copper designs

The fabric is one drawing of the whole driver. The thing that can be repeated on a bench is two boards. One host, `ccs_sense`, holds the three current sources, the sense path, the fold, the write-back latch, and the bus that fans address and `VDRIVE` out. The axis board is the same copper for X and for Y. Straps pick the axis and the group address. Bring-up is one host and two axis boards, both at group 0, which is an 8×8. The full plane is that same host and sixteen axis boards, eight X and eight Y. The roster is written down. The coverage cell for a uniquely addressed 1+16 harness is still a stub. Packaging is [docs/board_icd.md](../docs/board_icd.md); quantities are [docs/component_selection.md](../docs/component_selection.md) §6.

What the 8×8 PCB cell actually cleared, on the same KiCad at 18:54 that day: empty ERC error lists, and DRC with no violations and no unconnected items, on both `pcb_ccs_sense` and `pcb_axis_octal`. The gate counts errors. ERC ignored a global label that appears once, four-way junctions, SPICE model issues, and footprint-filter mismatch. DRC ignored missing courtyards, footprint-filter and footprint-type mismatch, and two track-geometry checks that do not apply to a board with no tracks. Warnings were not promoted. Empty error lists are what the matrix calls pass.

The schematics carry the bill the selection note names. On the host: TL431, a 3296W trimpot, OPA192, and IRLZ44N, three times, plus BAT54S, TLV3501, and the 74AHC74 latch. On each axis board: two 74AHC138, two 74AHC238, TBD62783 and TBD62083 in forward and reverse, and 32 SS14s. Sense nets `YA65`, `YB66`, `YA66`, and `YB65` stay on the host. They do not appear on the axis sheet. Bring-up therefore totals 64 steering diodes and four of each DMOS array; the full roster totals 512 diodes and 32 of each array, which is the same diode count the 64×64 fabric already emits.

The copper on the board is the headers. Each net is given a single pad, so the check stays clean without an autorouter. The schematic Pico header still lists address, enables, and power. The PCB footprint keeps `SENSE_STROBE`, `DOUT`, and `PIO_STROBE`. The sense connector keeps the four fold ends; `AGND` returns on the bus. The BOM footprints are placed — three CCS strips and the sense parts on a 220×120 mm host, decode, DMOS, and a 32-diode grid on a 160×140 mm axis board — and the files contain no tracks. The stack in those files is two layers. The packaging contract still prefers four layers, and smaller outlines, at most 120×80 mm for the host and 100×80 mm for an axis board. Those size and stack targets belong to the board ICD. This layout has not met them. A clean DRC here means the placed connectors do not fight themselves.

## The edge of the record

The tree this essay describes has the contracts, the L0–L2 SPICE decks, the L3 ideal plant, the generated octal fabric, and two board projects whose 8×8 ERC/DRC cell is green. Firmware is not in the tree. The bench column is empty. The 64×64 PCB cell stays a stub until the sixteen uniquely strapped axis boards are a gated harness, not only a roster in [docs/board_icd.md](../docs/board_icd.md) §7.

Still open, and owned by the design-choices note rather than by this prose: the exact \(I_c\), the drive-rail voltage, inhibit polarity against the read, how the RP2040 is packaged, the CCS MOSFET alternate, and whether diagnostic LEDs are required. The 600 mA used in every figure above is the harness assumption, recorded so the plots can be read, and it is not a frozen setpoint.

The next emitter job is the copper between those footprints, a stack that matches the four-layer preference, and outlines inside the size targets. Bring-up, when it happens, starts at 2×2, on three boards.

To draw the figures again:

```bash
uv run --group writeup python writeup/scripts/render_figures.py
```
