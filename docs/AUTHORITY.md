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
| Scale × surface verification claims | [coverage_matrix.md](coverage_matrix.md) (+ future regression scripts) | Architecture invention |

## Derived / non-authoritative (Layer C)

| Doc | Role |
|-----|------|
| [implementation_summary.md](implementation_summary.md) | Target block **sketch** only |
| [theory_of_operation.md](theory_of_operation.md) | Teaching summary |
| [references.md](references.md) | Evidence / citation pointers |
| [../README.md](../README.md) | Human front door; architecture snapshot defers to owners |
| [../AGENTS.md](../AGENTS.md) | Agent entry; points here; does not define ICD |

## Machine golden source (Layer D — planned)

Markdown contract owners are the baseline **until** generators exist. Then authority flips as follows (do not pretend these artifacts exist today):

1. **Weave / fabric geometry SSOT** → AST / generator script (planned `mce_array` or equivalent)
2. Human ICD docs become generated from AST **or** must match AST under a diff gate
3. **Verification SSOT** → [coverage_matrix.md](coverage_matrix.md) rows + regression exit codes (simulator as oracle for that layer)

Formal YAML/TLA+ conversion of the full ICD is out of scope until the AST pipeline exists; record the intent here only.

## Agent navigation

1. Read [../AGENTS.md](../AGENTS.md) (hard bans + entry).
2. Read **this file** (who owns the fact).
3. Open only the **owner** doc for the task; follow links for adjacent categories.
4. Before any scale claim, check [coverage_matrix.md](coverage_matrix.md).

## Stable IDs

Owner docs use anchors such as `REQ-ICD-FOLD`, `REQ-DRV-DMOS`, `GATE-L1-CYCLE` for future REQ → sim → bench tracing. Prefer citing those IDs over paraphrasing.
