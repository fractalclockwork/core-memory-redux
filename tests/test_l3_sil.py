"""GATE-L3-SIL — ideal_core N×N diagonal + sparse patterns; runtime budget."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spice" / "py"))

from ideal_core import I_HALF, IdealCore  # noqa: E402
from l3_harness import (  # noqa: E402
    pio_read,
    pio_write,
    run_continuous_sparse,
    run_diagonal_pattern,
    run_random_sparse,
)
from l3_plant import L3Plant  # noqa: E402

# Owner: continuous runs finish in minutes.
RUNTIME_BUDGET_S = 120.0


def test_half_select_hold_ideal():
    """Unit: one-axis Ic/2 must not flip (threshold-law)."""
    c = IdealCore(1.0)
    assert c.apply(I_HALF, 0.0) == 0.0
    assert c.state > 0.5


def test_diagonal_pattern_n8():
    _plant, elapsed = run_diagonal_pattern(8)
    assert elapsed < RUNTIME_BUDGET_S, f"n=8 diagonal {elapsed:.1f}s exceeds budget"


def test_random_sparse_n8():
    _plant, elapsed = run_random_sparse(8, n_cells=16, seed=42)
    assert elapsed < RUNTIME_BUDGET_S, f"n=8 sparse {elapsed:.1f}s exceeds budget"


def test_diagonal_and_sparse_n64():
    """Full-matrix L3 path (REQ-SCALE-ANTIX): no Chan; ideal_core only."""
    _p, t_diag = run_diagonal_pattern(64)
    assert t_diag < RUNTIME_BUDGET_S, f"n=64 diagonal {t_diag:.1f}s exceeds budget"
    _p, t_sparse = run_random_sparse(64, n_cells=64, seed=7)
    assert t_sparse < RUNTIME_BUDGET_S, f"n=64 sparse {t_sparse:.1f}s exceeds budget"


def test_continuous_runtime_n64():
    elapsed = run_continuous_sparse(64, cycles=500, seed=3)
    assert elapsed < RUNTIME_BUDGET_S, f"continuous {elapsed:.1f}s exceeds budget"


def test_strobe_after_line_settle():
    """Strobe aperture is after line R/L/C settle into the ICD window."""
    plant = L3Plant(8)
    pio_write(plant, 0, 0, 1)
    t_before = plant.sim_time
    result = pio_read(plant, 0, 0)
    assert result.bit == 1
    # READ path advances at least strobe settle into the 150–300 ns class window.
    assert plant.sim_time - t_before >= 150e-9
