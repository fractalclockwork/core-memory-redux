# Documentation authority (SSOT map)

**Status:** `baseline` (Phase 0 authority contract)

This file is the **SSOT map**, not the design itself. It names which document owns each fact category, how conflicts resolve, and how agents must navigate. Design content lives in the owner docs below.

Chat transcripts, agent scratchpads, and derived sketches are **not** authoritative.

## Status tags

Use these tags on claims and at the top of each doc:

| Tag | Meaning |
|-----|---------|
| `baseline` | Approved Phase 0 contract; agents may synthesize / plan against it |
| `proposal` | Suggested change; outside baseline until explicitly promoted |
| `open` | Decision deferred (usually to bench); not frozen |
| `sketch` | Illustrative / non-authoritative; must not override owners |

## Conflict priority

When two sources disagree:

1. **This ownership table** (which doc is allowed to define the fact)
2. **Owning document** section for that category
3. **Derived docs** (README snapshot, implementation sketch, theory summary)
4. **Chat / prior agent turns**

If implementation or simulation contradicts an owner: **update the owner first**, then adapt consumers. Do not “fix forward” in a sketch or chat and leave the owner stale.

## Link, do not copy

Normative facts have **one editable home**. Downstream docs must **link** to the owner (file + section or stable ID). Do not restate fold geometry, BOM MPNs, naming regex, or gate criteria in full elsewhere—summaries of one sentence plus a link are fine.

## Ownership table (Layer B — contract owners)

| Information category | Authoritative owner | Must not own |
|----------------------|---------------------|--------------|
| Process, normative freeze table, L0–L4 gates, anti-explosion rules | [system_design_spec.md](system_design_spec.md) | Block wiring narrative |
| Plane physical ICD, sense/inhibit electrical contract, timing sequence | [design_specification.md](design_specification.md) | Process phases |
| Net grammar, naming layers, decode/DMOS call model | [naming.md](naming.md) | Pin-budget tables |
| Steer/magnetic pin budgets, octal tile ABI | [hierarchy_abi.md](hierarchy_abi.md) | Timing prose |
| BOM MPNs and part rationale | [component_selection.md](component_selection.md) | ICD geometry |
| Tradeoffs + open decisions | [design_choices.md](design_choices.md) | Frozen ICD |
| Multi-board packaging (1× CCS host + 2×8 axis-octal) | [board_icd.md](board_icd.md) | Electrical ABI / pin budgets |
| Scale × surface verification claims | [coverage_matrix.md](coverage_matrix.md) (+ future regression scripts) | Architecture invention |

## Derived / non-authoritative (Layer C)

| Doc | Role |
|-----|------|
| [implementation_summary.md](implementation_summary.md) | Target block **sketch** only |
| [theory_of_operation.md](theory_of_operation.md) | Teaching summary |
| [references.md](references.md) | Evidence / citation pointers |
| [dev_host_setup.md](dev_host_setup.md) | Ubuntu apt + `uv` host procedure |
| [../README.md](../README.md) | Human front door; architecture snapshot defers to owners |
| [../AGENTS.md](../AGENTS.md) | Agent entry; points here; does not define ICD |

## Machine golden source (Layer D)

Markdown contract owners remain baseline for ICD / BOM / timing. **Weave / fabric geometry** SSOT for generated KiCad is now:

1. **Weave / fabric geometry SSOT** → [`generators/mce_array.py`](../generators/mce_array.py) (+ [`generators/emit_kicad.py`](../generators/emit_kicad.py) emitter). Do not hand-edit `kicad/**` sheets; regenerate with `uv run python -m generators.cli --n 2|64`.
2. **Multi-board PCB SSOT** → [`generators/board_abi.py`](../generators/board_abi.py) + [`generators/emit_boards.py`](../generators/emit_boards.py) → `kicad/pcb_ccs_sense/`, `kicad/pcb_axis_octal/`; `uv run python -m generators.cli --board ccs|axis`. Packaging contract: [board_icd.md](board_icd.md).
3. Human ICD docs stay owner for electrical contracts; geometry emitted from the AST must conform to [hierarchy_abi.md](hierarchy_abi.md) / [naming.md](naming.md).
4. **Verification SSOT** → [coverage_matrix.md](coverage_matrix.md) rows + regression exit codes (simulator / `kicad-cli` ERC/DRC as oracle for that layer)

Formal YAML/TLA+ conversion of the full ICD remains out of scope; geometry SSOT for fabric is the AST above.

## Agent navigation

1. Read [../AGENTS.md](../AGENTS.md) (hard bans + entry).
2. Read **this file** (who owns the fact).
3. Open only the **owner** doc for the task; follow links for adjacent categories.
4. Before any scale claim, check [coverage_matrix.md](coverage_matrix.md).

## Stable IDs

Owner docs use anchors such as `REQ-ICD-FOLD`, `REQ-DRV-DMOS`, `GATE-L1-CYCLE` for future REQ → sim → bench tracing. Prefer citing those IDs over paraphrasing.
