"""Pin-budget constants from hierarchy_abi / naming (REQ-HIER-OCTAL).

Do not invent a second ABI — values mirror docs/hierarchy_abi.md and docs/naming.md.
"""

from __future__ import annotations

# Octal steer tile (one axis, one HS group g): hierarchy_abi pin list.
OCTAL_PIN_COUNT = 34  # HS,HSR + LS[0..7],LSR[0..7] + A[0..7],B[0..7]

# Decode block: 8 HS + 8 LS bank outs (not 64 line pins).
DECODE_HS_OUTS = 8
DECODE_LS_OUTS = 8

# Sense / fold — never enter Drive/Decode hierarchical pins.
SENSE_NETS = frozenset({"YA65", "YB65", "YA66", "YB66", "SENSE_FOLD"})

AXES = ("X", "Y")
DIRS = ("FWD", "REV")

# Diode law (hierarchy_abi):
# FWD: HS → diode → B{line}; A{line} → diode → LS{ls}
# REV: HSR → diode → A{line}; B{line} → diode → LSR{ls}


def line_index(hs: int, ls: int) -> int:
    return 8 * hs + ls


def hs_of(line: int) -> int:
    return line // 8


def ls_of(line: int) -> int:
    return line % 8


def octal_groups_for_n(n: int) -> list[int]:
    """HS group indices needed for an n×n logical array (n in {2, 64})."""
    if n < 1:
        raise ValueError("n must be >= 1")
    max_line = n - 1
    max_g = hs_of(max_line)
    return list(range(max_g + 1))


def lines_in_group(g: int, n: int) -> list[int]:
    """Logical lines in HS group g that exist for size n."""
    return [line_index(g, k) for k in range(8) if line_index(g, k) < n]
