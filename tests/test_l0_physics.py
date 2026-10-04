"""GATE-L0-PHYSICS — single-core Chan calibration gates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spice" / "py"))

from l0_harness import I_HALF, peak_abs, run_l0_transient, sample_at  # noqa: E402

# Runtime budget: single-core transient must finish in seconds.
RUNTIME_BUDGET_S = 30.0


def test_half_select_hold():
    """One-axis Ic/2 must not flip remanent state."""
    ix = (
        f"PWL(0 0 50n 0 100n {I_HALF} 800n {I_HALF} 850n 0 "
        f"1.2u 0 1.25u {I_HALF} 2.0u {I_HALF} 2.05u 0)"
    )
    iy = f"PWL(0 0 50n 0 100n {I_HALF} 800n {I_HALF} 850n 0 1.2u 0 2.05u 0)"

    time_s, state, _sense, mmf, elapsed = run_l0_transient(
        ix, iy, end_time=2.5e-6, state_ic=1.0
    )
    assert elapsed < RUNTIME_BUDGET_S, f"L0 runtime {elapsed:.1f}s exceeds budget"

    after_write = sample_at(time_s, state, 1.0e-6)
    during_half = sample_at(time_s, mmf, 1.6e-6)
    after_half = sample_at(time_s, state, 2.3e-6)

    assert after_write > 0.5, f"expected stored-1 after WRITE, got state={after_write}"
    assert during_half == pytest.approx(I_HALF, rel=0.05, abs=0.02)
    assert after_half > 0.5, f"half-select flipped state to {after_half}"


def test_read1_amplitude_discrimination():
    """Destructive READ of a stored-1 must produce a larger sense peak than stored-0."""
    # WRITE-1 then READ
    ix1 = (
        f"PWL(0 0 50n 0 100n {I_HALF} 800n {I_HALF} 850n 0 "
        f"1.5u 0 1.55u {-I_HALF} 2.3u {-I_HALF} 2.35u 0)"
    )
    t1, st1, s1, _m1, e1 = run_l0_transient(ix1, ix1, end_time=3.0e-6, state_ic=1.0)
    assert e1 < RUNTIME_BUDGET_S
    peak1 = peak_abs(t1, s1, 1.5e-6, 2.5e-6)
    assert sample_at(t1, st1, 2.7e-6) < -0.5, "READ did not destroy stored-1"

    # WRITE-0 then READ
    ix0 = (
        f"PWL(0 0 50n 0 100n {-I_HALF} 800n {-I_HALF} 850n 0 "
        f"1.5u 0 1.55u {-I_HALF} 2.3u {-I_HALF} 2.35u 0)"
    )
    t0, st0, s0, _m0, e0 = run_l0_transient(ix0, ix0, end_time=3.0e-6, state_ic=1.0)
    assert e0 < RUNTIME_BUDGET_S
    peak0 = peak_abs(t0, s0, 1.5e-6, 2.5e-6)
    assert sample_at(t0, st0, 1.0e-6) < -0.5, "WRITE-0 did not store 0"

    assert peak1 > 10 * max(peak0, 1e-9), (
        f"read-1 peak {peak1:.3e} not distinguishable from read-0 peak {peak0:.3e}"
    )


def test_restore_polarity():
    """WRITE-1 → READ → WRITE-1 restore returns positive remanence."""
    ix = (
        f"PWL(0 0 50n 0 100n {I_HALF} 600n {I_HALF} 650n 0 "
        f"1.2u 0 1.25u {-I_HALF} 1.9u {-I_HALF} 1.95u 0 "
        f"2.5u 0 2.55u {I_HALF} 3.2u {I_HALF} 3.25u 0)"
    )
    time_s, state, _sense, _mmf, elapsed = run_l0_transient(
        ix, ix, end_time=3.8e-6, state_ic=1.0
    )
    assert elapsed < RUNTIME_BUDGET_S

    after_write = sample_at(time_s, state, 0.9e-6)
    after_read = sample_at(time_s, state, 2.2e-6)
    after_restore = sample_at(time_s, state, 3.5e-6)

    assert after_write > 0.5
    assert after_read < -0.5
    assert after_restore > 0.5, f"restore failed, state={after_restore}"
