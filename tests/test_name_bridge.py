"""Cross-surface name bridge: shared ICD tokens must not drift silently.

L0–L2 SPICE is a behavioral plant, not a pin-faithful KiCad co-sim. This test
only guards tokens that both surfaces must share (sense/fold + L2 bank enables)
and documents the intentional L2 collapse (en_x present; XHS absent).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generators.abi import SENSE_NETS  # noqa: E402
from generators.mce_array import build_fabric  # noqa: E402

L1_DECK = ROOT / "spice" / "l1" / "oracle_2x2.cir"
L2_DECK = ROOT / "spice" / "l2" / "driver_2x2.cir"
L2_HARNESS = ROOT / "spice" / "py" / "l2_harness.py"

# Shared ICD set (casefold match in ngspice decks).
SENSE_FOLD_TOKENS = ("YA65", "YB66", "YA66", "YB65")
L2_ENABLE_TOKENS = ("FWD_EN_n", "REV_EN_n", "DEC_EN")


def _casefold_has(text: str, token: str) -> bool:
    return token.casefold() in text.casefold()


def test_sense_nets_constant_matches_icd():
    assert SENSE_NETS == frozenset({"YA65", "YB65", "YA66", "YB66", "SENSE_FOLD"})


def test_l1_deck_has_sense_fold_tokens():
    text = L1_DECK.read_text(encoding="utf-8")
    for tok in SENSE_FOLD_TOKENS:
        assert _casefold_has(text, tok), f"L1 deck missing {tok}"


def test_l2_deck_has_shared_icd_tokens():
    text = L2_DECK.read_text(encoding="utf-8")
    for tok in SENSE_FOLD_TOKENS:
        assert _casefold_has(text, tok), f"L2 deck missing {tok}"
    for tok in L2_ENABLE_TOKENS:
        assert _casefold_has(text, tok), f"L2 deck missing {tok}"


def test_fabric_ast_has_shared_icd_tokens():
    fab = build_fabric(64)
    fold_vals = set(fab.fold.values()) | set(fab.fold.keys())
    assert "SENSE_FOLD" in fold_vals
    assert fab.fold["YA66"] == "SENSE_FOLD"
    assert fab.fold["YB65"] == "SENSE_FOLD"
    assert {"YA65", "YB66"} <= set(fab.fold)
    # Bank enables appear on decode pin sets via sense_nets_disjoint check path
    assert fab.sense_nets_disjoint_from_decode()


def test_l2_collapse_guard():
    """L2 remains behavioral: en_x plant gate; no XHS DMOS switch nodes."""
    deck = L2_DECK.read_text(encoding="utf-8")
    harness = L2_HARNESS.read_text(encoding="utf-8")
    blob = deck + "\n" + harness
    assert _casefold_has(blob, "en_x"), "L2 collapse lost en_x"
    assert not re.search(r"\bXHS\d", blob), "L2 unexpectedly grew XHS* pins"
    assert not re.search(r"\bXLS\d", blob), "L2 unexpectedly grew XLS* pins"


def test_fabric_rev_decode_uses_r_token():
    """naming.md §2: REV outs are X_HS0r_n / X_LS0r_en (fabric ABI, not SPICE)."""
    fab = build_fabric(2)
    fwd = next(c for c in fab.decode_calls if c.axis == "X" and c.direction == "FWD")
    rev = next(c for c in fab.decode_calls if c.axis == "X" and c.direction == "REV")
    assert fwd.hs_outs[0] == "X_HS0_n"
    assert fwd.ls_outs[0] == "X_LS0_en"
    assert rev.hs_outs[0] == "X_HS0r_n"
    assert rev.ls_outs[0] == "X_LS0r_en"
    assert all(re.fullmatch(r"[XY]_(HS|LS)[0-9]{1,2}r?_(n|en)", n) for n in rev.hs_outs + rev.ls_outs)
