"""Deterministic KiCad sexpr writer (KiCad 10-compatible)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

# Pre-upgrade schema; scripts/run_kicad_erc.py runs `kicad-cli sch upgrade`.
KICAD_SCH_VERSION = 20250114

# KiCad schema tokens must be bare atoms; quoting them fails schematic load.
_BARE_ATOMS = frozenset(
    {
        "yes",
        "no",
        "solid",
        "dash",
        "dash_dot",
        "dot",
        "default",
        "none",
        "bidirectional",
        "input",
        "output",
        "passive",
        "power_in",
        "power_out",
        "tri_state",
        "line",
        "inverted",
        "clock",
        "left",
        "right",
        "top",
        "bottom",
        # PCB
        "signal",
        "user",
        "thru_hole",
        "through_hole",
        "smd",
        "circle",
        "rect",
        "oval",
        "roundrect",
        "*.Cu",
        "*.Mask",
        "*.SilkS",
        "F.Cu",
        "B.Cu",
        "F.SilkS",
        "B.SilkS",
        "F.Mask",
        "B.Mask",
        "F.Paste",
        "B.Paste",
        "F.CrtYd",
        "B.CrtYd",
        "F.Fab",
        "B.Fab",
        "Edge.Cuts",
        "Dwgs.User",
        "Cmts.User",
        "Margin",
        # fp_text types (must be bare; quoted breaks pcbnew load)
        "reference",
        "value",
        "hide",
        "locked",
        # stock symbol fill / pin style tokens
        "background",
        "outline",
        "italic",
        "bold",
        "open_emitter",
        "open_collector",
        "unspecified",
        "free",
        "inverted_clock",
        "input_low",
        "clock_low",
        "output_low",
        "edge_clock_high",
        "non_logic",
    }
)


def det_uuid(key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"core-memory-redux/{key}"))


def atom(x: Any) -> str:
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:g}"
    if isinstance(x, int):
        return str(x)
    s = str(x)
    if s in _BARE_ATOMS:
        return s
    esc = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{esc}"'


def render(node: Any, indent: int = 0) -> str:
    """Render a nested list sexpr tree with KiCad-like indentation."""
    if not isinstance(node, (list, tuple)):
        return atom(node) if isinstance(node, str) else (
            atom(node) if not isinstance(node, (int, float, bool)) else (
                "yes" if node is True else "no" if node is False else (
                    f"{node:g}" if isinstance(node, float) else str(node)
                )
            )
        )
    if not node:
        return "()"
    head, *rest = node
    head_s = head if isinstance(head, str) else render(head)
    if not rest:
        return f"({head_s})"
    # Compact single-line for tiny nodes
    flat_parts = [head_s] + [render(x) for x in rest]
    flat = f"({' '.join(flat_parts)})"
    if len(flat) <= 100 and not any(isinstance(x, (list, tuple)) and len(x) > 3 for x in rest):
        return flat
    pad = "\t" * (indent + 1)
    lines = [f"({head_s}"]
    for x in rest:
        lines.append(pad + render(x, indent + 1))
    lines.append(("\t" * indent) + ")")
    return "\n".join(lines)


def write_sexpr(path: Path, root: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(root) + "\n", encoding="utf-8")


def parse_sexpr(text: str) -> Any:
    """Minimal KiCad sexpr parser → nested lists (atoms as str/int/float)."""
    tokens: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c in "()":
            tokens.append(c)
            i += 1
            continue
        if c == '"':
            j = i + 1
            buf: list[str] = []
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                if text[j] == '"':
                    break
                buf.append(text[j])
                j += 1
            tokens.append('"' + "".join(buf) + '"')
            i = j + 1
            continue
        j = i
        while j < n and text[j] not in " \t\r\n()":
            j += 1
        tokens.append(text[i:j])
        i = j

    def atom_token(tok: str) -> Any:
        if tok.startswith('"') and tok.endswith('"'):
            return tok[1:-1]
        if tok in ("yes", "true"):
            return True
        if tok in ("no", "false"):
            return False
        try:
            if "." in tok or "e" in tok.lower():
                return float(tok)
            return int(tok)
        except ValueError:
            return tok

    def read(idx: int) -> tuple[Any, int]:
        tok = tokens[idx]
        if tok == "(":
            out: list[Any] = []
            idx += 1
            while tokens[idx] != ")":
                val, idx = read(idx)
                out.append(val)
            return out, idx + 1
        if tok == ")":
            raise ValueError("unexpected )")
        return atom_token(tok), idx + 1

    tree, _ = read(0)
    return tree
