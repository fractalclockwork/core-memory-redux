"""Place KiCad library symbols / footprints for board emit."""

from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any

from generators.bom_parts import Part
from generators.emit_kicad import _effects, _property, snap
from generators.sexpr import det_uuid, parse_sexpr

SYMBOL_DIR = Path("/usr/share/kicad/symbols")
FOOTPRINT_ROOT = Path("/usr/share/kicad/footprints")


def _is_node(x: Any, head: str) -> bool:
    return isinstance(x, list) and bool(x) and x[0] == head


def _prop_name(node: list) -> str | None:
    if _is_node(node, "property") and len(node) > 1:
        return str(node[1])
    return None


def load_lib_file(lib_nickname: str) -> list:
    path = SYMBOL_DIR / f"{lib_nickname}.kicad_sym"
    if not path.is_file():
        raise FileNotFoundError(path)
    tree = parse_sexpr(path.read_text(encoding="utf-8"))
    if not _is_node(tree, "kicad_symbol_lib"):
        raise ValueError(f"not a symbol lib: {path}")
    return tree


def find_symbol(lib_tree: list, name: str) -> list:
    for node in lib_tree[1:]:
        if _is_node(node, "symbol") and len(node) > 1 and node[1] == name:
            return node
    raise KeyError(f"symbol {name!r} not in lib")


def _rename_unit_drawings(sym: list, old_base: str, new_base: str) -> None:
    for node in sym[2:]:
        if not _is_node(node, "symbol"):
            continue
        uname = str(node[1])
        if uname.startswith(old_base + "_"):
            node[1] = new_base + uname[len(old_base) :]


def deep_merge_symbol(parent: list, child: list) -> list:
    """Deep-merge parent body into child; child overrides. Drop extends."""
    parent_name = str(parent[1])
    child_name = str(child[1])
    merged: list = copy.deepcopy(parent)
    merged[1] = child_name
    _rename_unit_drawings(merged, parent_name, child_name)

    prop_idx: dict[str, int] = {}
    unit_idx: dict[str, int] = {}
    head_idx: dict[str, int] = {}
    for i, node in enumerate(merged[2:], start=2):
        if not isinstance(node, list) or not node:
            continue
        pn = _prop_name(node)
        if pn is not None:
            prop_idx[pn] = i
            continue
        if node[0] == "symbol" and len(node) > 1:
            unit_idx[str(node[1])] = i
            continue
        head_idx[str(node[0])] = i

    for node in child[2:]:
        if not isinstance(node, list) or not node or node[0] == "extends":
            continue
        pn = _prop_name(node)
        if pn is not None:
            if pn in prop_idx:
                merged[prop_idx[pn]] = copy.deepcopy(node)
            else:
                merged.append(copy.deepcopy(node))
                prop_idx[pn] = len(merged) - 1
            continue
        if node[0] == "symbol":
            uname = str(node[1])
            if uname in unit_idx:
                merged[unit_idx[uname]] = copy.deepcopy(node)
            else:
                suffix = uname[len(child_name) :] if uname.startswith(child_name) else None
                matched = False
                if suffix:
                    for k, i in unit_idx.items():
                        if k.endswith(suffix):
                            merged[i] = copy.deepcopy(node)
                            matched = True
                            break
                if not matched:
                    merged.append(copy.deepcopy(node))
                    unit_idx[uname] = len(merged) - 1
            continue
        h = str(node[0])
        if h in head_idx:
            merged[head_idx[h]] = copy.deepcopy(node)
        else:
            merged.append(copy.deepcopy(node))
            head_idx[h] = len(merged) - 1

    return [merged[0], merged[1]] + [
        n for n in merged[2:] if not _is_node(n, "extends")
    ]


def _resolve_raw(
    lib_nickname: str, name: str, stack: frozenset[str] | None = None
) -> list:
    stack = stack or frozenset()
    if name in stack:
        raise RuntimeError(f"extends cycle: {name}")
    raw = copy.deepcopy(find_symbol(load_lib_file(lib_nickname), name))
    ext = next((str(n[1]) for n in raw[2:] if _is_node(n, "extends")), None)
    if ext:
        parent = _resolve_raw(lib_nickname, ext, stack | {name})
        raw = deep_merge_symbol(parent, raw)
    return raw


def load_symbol(lib_nickname: str, name: str) -> list:
    """Load by lib+name; resolve extends; rename top to 'Lib:Name'."""
    resolved = _resolve_raw(lib_nickname, name)
    resolved[1] = f"{lib_nickname}:{name}"
    return resolved


def load_symbol_lib_id(lib_id: str) -> list:
    lib, name = lib_id.split(":", 1)
    return load_symbol(lib, name)


def _unit_base(sym: list) -> str:
    return str(sym[1]).split(":", 1)[-1]


def _unit_drawing(sym: list, unit: int) -> list | None:
    """Return the unit drawing that actually carries pins (style 1, else 0)."""
    base = _unit_base(sym)
    candidates = []
    for node in sym[2:]:
        if not _is_node(node, "symbol"):
            continue
        uname = str(node[1])
        if not uname.startswith(f"{base}_{unit}_"):
            continue
        parts = uname[len(base) + 1 :].split("_")
        if len(parts) != 2:
            continue
        try:
            u, style = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if u != unit:
            continue
        if any(_is_node(c, "pin") for c in node[2:]):
            candidates.append((style, node))
    if not candidates:
        return None
    # Prefer body style 1 (IEEE) when both exist; else De Morgan style 0.
    candidates.sort(key=lambda t: (0 if t[0] == 1 else 1, t[0]))
    return candidates[0][1]


def symbol_units(sym: list) -> list[int]:
    base = _unit_base(sym)
    units: set[int] = set()
    for node in sym[2:]:
        if not _is_node(node, "symbol"):
            continue
        uname = str(node[1])
        if not uname.startswith(base + "_"):
            continue
        parts = uname[len(base) + 1 :].split("_")
        if len(parts) != 2:
            continue
        try:
            u, _style = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if u == 0:
            continue
        if any(_is_node(c, "pin") for c in node[2:]):
            units.add(u)
    return sorted(units)


def unit_pin_ats(sym: list, unit: int) -> list[tuple[str, float, float, float]]:
    drawing = _unit_drawing(sym, unit)
    if drawing is None:
        raise KeyError(f"missing pinned unit drawing for {_unit_base(sym)} unit {unit}")
    out: list[tuple[str, float, float, float]] = []
    for node in drawing[2:]:
        if not _is_node(node, "pin"):
            continue
        at = next((c for c in node if _is_node(c, "at")), None)
        num = next((str(c[1]) for c in node if _is_node(c, "number")), None)
        if at is None or num is None:
            continue
        px, py = float(at[1]), float(at[2])
        pang = float(at[3]) if len(at) > 3 else 0.0
        out.append((num, px, py, pang))
    return out


def pin_tip_abs(
    sx: float, sy: float, angle_deg: float, px: float, py: float
) -> tuple[float, float]:
    """Absolute tip of pin `at` after instance transform (KiCad local-Y mirror)."""
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    return (sx + px * c + py * s, sy + px * s - py * c)


def place_symbol_unit(
    lib_id: str,
    ref: str,
    unit: int,
    sx: float,
    sy: float,
    sheet_uuid: str,
    pin_numbers: list[str],
    *,
    value: str,
    footprint: str = "",
    angle: float = 0.0,
    role: str = "",
) -> list:
    sx, sy = snap(sx), snap(sy)
    pins = [
        ["pin", n, ["uuid", det_uuid(f"pin/{ref}/u{unit}/{n}")]] for n in pin_numbers
    ]
    return [
        "symbol",
        ["lib_id", lib_id],
        ["at", sx, sy, angle],
        ["unit", unit],
        ["exclude_from_sim", False],
        ["in_bom", True],
        ["on_board", True],
        ["dnp", False],
        ["uuid", det_uuid(f"sym/{ref}/u{unit}@{sx:g},{sy:g}")],
        _property("Reference", ref, sx + 2.54, sy - 2.54),
        _property("Value", value, sx + 2.54, sy + 2.54),
        _property("Footprint", footprint, sx, sy, hide=True),
        _property("Datasheet", "~", sx, sy, hide=True),
        _property("Description", role, sx, sy, hide=True),
        *pins,
        [
            "instances",
            [
                "project",
                "",
                [
                    "path",
                    f"/{sheet_uuid}",
                    ["reference", ref],
                    ["unit", unit],
                ],
            ],
        ],
    ]


def place_part_nc(
    part: Part,
    ref: str,
    x: float,
    y: float,
    sheet_uuid: str,
    lib_cache: dict[str, list],
    items: list,
    *,
    value: str | None = None,
    unit_dx: float = 30.48,
) -> None:
    """Embed symbol (once), place all units, NC every pin tip (ERC-clean)."""
    lib_id = part.lib_id
    if lib_id not in lib_cache:
        lib_cache[lib_id] = load_symbol_lib_id(lib_id)
    sym = lib_cache[lib_id]
    val = value if value is not None else part.mpn
    units = symbol_units(sym)
    if not units:
        units = [1]
    for i, unit in enumerate(units):
        sx = snap(x + i * unit_dx)
        sy = snap(y)
        pins = unit_pin_ats(sym, unit) if unit in symbol_units(sym) else []
        if not pins and unit == 1:
            # Fallback: sequential pin uuids when drawing parse failed
            pins = [(str(n), 0.0, 0.0, 0.0) for n in range(1, part.pins + 1)]
        items.append(
            place_symbol_unit(
                lib_id,
                ref,
                unit,
                sx,
                sy,
                sheet_uuid,
                [p[0] for p in pins],
                value=val,
                footprint=part.footprint,
                role=part.role,
            )
        )
        for num, px, py, _pang in pins:
            tx, ty = pin_tip_abs(sx, sy, 0.0, px, py)
            items.append(
                [
                    "no_connect",
                    ["at", snap(tx), snap(ty)],
                    ["uuid", det_uuid(f"nc/{ref}/u{unit}/{num}")],
                ]
            )


def footprint_path(fp_lib_id: str) -> Path:
    lib, name = fp_lib_id.split(":", 1)
    return FOOTPRINT_ROOT / f"{lib}.pretty" / f"{name}.kicad_mod"


def load_board_footprint(
    fp_lib_id: str,
    ref: str,
    value: str,
    x: float,
    y: float,
    *,
    angle: float = 0,
) -> list:
    """Load a stock footprint into a PCB instance (no nets on pads)."""
    path = footprint_path(fp_lib_id)
    if not path.is_file():
        raise FileNotFoundError(f"{fp_lib_id} -> {path}")
    tree = parse_sexpr(path.read_text(encoding="utf-8"))
    if not isinstance(tree, list) or tree[0] != "footprint":
        raise ValueError(path)
    fp: list = [
        "footprint",
        fp_lib_id,
        ["layer", "F.Cu"],
        ["uuid", det_uuid(f"fp/{ref}")],
        ["at", x, y, angle],
    ]
    for node in tree[2:]:
        if isinstance(node, list) and node and node[0] in (
            "version",
            "generator",
            "generator_version",
            "layer",
            "uuid",
            "at",
            "tedit",
        ):
            continue
        if isinstance(node, list) and node and node[0] == "pad":
            pad = [x for x in node if not (isinstance(x, list) and x and x[0] in ("uuid", "net"))]
            pnum = pad[1] if len(pad) > 1 else "0"
            pad.append(["uuid", det_uuid(f"pad/{ref}/{pnum}")])
            fp.append(pad)
        elif isinstance(node, list) and node and node[0] == "property":
            prop = [p for p in node if not (isinstance(p, list) and p and p[0] == "uuid")]
            pname = prop[1] if len(prop) > 1 else ""
            if pname == "Reference":
                prop[2] = ref
            elif pname == "Value":
                prop[2] = value
            elif pname == "Footprint":
                prop[2] = fp_lib_id
            prop.append(["uuid", det_uuid(f"fp/{ref}/prop/{pname}")])
            fp.append(prop)
        elif isinstance(node, list) and node and node[0] == "fp_text":
            txt = [p for p in node if not (isinstance(p, list) and p and p[0] in ("tstamp", "uuid"))]
            if len(txt) >= 3 and txt[1] == "reference":
                txt[2] = ref
            elif len(txt) >= 3 and txt[1] == "value":
                txt[2] = value
            kind = txt[1] if len(txt) > 1 else "x"
            txt.append(["uuid", det_uuid(f"fp/{ref}/fp_text/{kind}")])
            fp.append(txt)
        else:
            fp.append(node)
    # Ensure Reference/Value properties exist
    props = {n[1] for n in fp if isinstance(n, list) and n and n[0] == "property"}
    if "Reference" not in props:
        fp.append(
            [
                "property",
                "Reference",
                ref,
                ["at", 0, -2.5, 0],
                ["layer", "F.SilkS"],
                ["uuid", det_uuid(f"fp/{ref}/prop/Reference")],
            ]
        )
    if "Value" not in props:
        fp.append(
            [
                "property",
                "Value",
                value,
                ["at", 0, 2.5, 0],
                ["layer", "F.Fab"],
                ["uuid", det_uuid(f"fp/{ref}/prop/Value")],
            ]
        )
    return fp
