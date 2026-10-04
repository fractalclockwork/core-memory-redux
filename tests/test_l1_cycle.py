"""GATE-L1-CYCLE — 2×2 oracle WRITE/READ/INHIBIT + CCS failure regression."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spice" / "py"))

from l1_harness import peak_abs, run_l1_transient, sample_at  # noqa: E402

RUNTIME_BUDGET_S = 60.0


def test_write_read_inhibit_cycle():
    """Full cycle on (0,0); half-selected neighbors must hold."""
    # WRITE (+pol) → READ (−pol) → INHIBIT (CCS_INH) → WRITE restore (+pol)
    en_xy = (
        "PWL(0 0 50n 0 100n 1 800n 1 850n 0 "
        "1.5u 0 1.55u 1 2.3u 1 2.35u 0 "
        "2.7u 0 3.5u 0 "
        "3.55u 1 4.2u 1 4.25u 0)"
    )
    en_i = "PWL(0 0 2.8u 0 2.85u 1 3.4u 1 3.45u 0)"
    pol = "PWL(0 1 1.4u 1 1.45u -1 2.4u -1 2.45u 1 5u 1)"

    time_s, states, sense, mmf00, elapsed = run_l1_transient(
        en_x_pwl=en_xy,
        en_y_pwl=en_xy,
        en_i_pwl=en_i,
        pol_xy_pwl=pol,
        pol_i_pwl="PWL(0 1)",
        end_time=5.0e-6,
        state_ic={"m00": -1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0},
    )
    assert elapsed < RUNTIME_BUDGET_S, f"L1 runtime {elapsed:.1f}s exceeds budget"

    after_write = sample_at(time_s, states["m00"], 1.0e-6)
    n01_write = sample_at(time_s, states["m01"], 1.0e-6)
    n10_write = sample_at(time_s, states["m10"], 1.0e-6)
    after_read = sample_at(time_s, states["m00"], 2.5e-6)
    sense_peak = peak_abs(time_s, sense, 1.5e-6, 2.5e-6)
    during_inh = sample_at(time_s, mmf00, 3.1e-6)
    after_restore = sample_at(time_s, states["m00"], 4.5e-6)

    assert after_write > 0.5, f"WRITE-1 failed, state={after_write}"
    assert n01_write < -0.5 and n10_write < -0.5, "half-selected neighbor flipped"
    assert after_read < -0.5, f"READ did not destroy stored-1, state={after_read}"
    assert sense_peak > 1.0, f"sense spike missing, peak={sense_peak}"
    assert during_inh == pytest.approx(0.3, rel=0.15, abs=0.05), (
        f"inhibit path current missing, mmf={during_inh}"
    )
    assert after_restore > 0.5, f"RESTORE-1 failed, state={after_restore}"


def test_ccs_failure_regression():
    """With CCS_X open, coincident drive must not full-select the addressed core."""
    time_s, states, _sense, _mmf, elapsed = run_l1_transient(
        en_x_pwl="PWL(0 0)",  # CCS_X failed open
        en_y_pwl="PWL(0 0 50n 0 100n 1 800n 1 850n 0)",
        en_i_pwl="PWL(0 0)",
        pol_xy_pwl="PWL(0 1)",
        end_time=1.5e-6,
        state_ic={"m00": 1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0},
    )
    assert elapsed < RUNTIME_BUDGET_S
    after = sample_at(time_s, states["m00"], 1.0e-6)
    assert after > 0.5, f"CCS_X failure allowed flip, state={after}"
