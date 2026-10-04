"""GATE-L2-E2E — address-pin driver path, mutex, fail-safe, strobe aperture."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spice" / "py"))

from l2_harness import peak_abs, run_l2_transient, sample_at  # noqa: E402

RUNTIME_BUDGET_S = 60.0
T_STROBE = 200e-9  # mid of ICD ~150–300 ns sense strobe window


def test_address_e2e_cycle_and_strobe():
    """REV WRITE then FWD READ on addr (0,0); strobe aperture sees destroyed-1."""
    # Active-low bank enables: 0=on, 1=off. DEC_EN active-high.
    rev = "PWL(0 1 50n 1 100n 0 800n 0 850n 1 5u 1)"
    fwd = "PWL(0 1 1.5u 1 1.55u 0 2.3u 0 2.35u 1 5u 1)"
    dec = "PWL(0 1)"

    time_s, states, sense, dout, en_x, elapsed = run_l2_transient(
        addr_x0=0.0,
        addr_y0=0.0,
        fwd_en_n_pwl=fwd,
        rev_en_n_pwl=rev,
        dec_en_pwl=dec,
        end_time=3.0e-6,
        state_ic={"m00": -1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0},
    )
    assert elapsed < RUNTIME_BUDGET_S, f"L2 runtime {elapsed:.1f}s exceeds budget"

    after_write = sample_at(time_s, states["m00"], 1.0e-6)
    n01 = sample_at(time_s, states["m01"], 1.0e-6)
    n10 = sample_at(time_s, states["m10"], 1.0e-6)
    t_read = 1.55e-6
    after_read = sample_at(time_s, states["m00"], 2.5e-6)
    at_strobe = sample_at(time_s, states["m00"], t_read + T_STROBE)
    en_at_strobe = sample_at(time_s, en_x, t_read + T_STROBE)
    # Behavioral Chan flip is near the READ edge; capture a wide aperture.
    sense_peak = peak_abs(time_s, sense, t_read - 50e-9, t_read + 150e-9)

    assert after_write > 0.5, f"WRITE via REV path failed, state={after_write}"
    assert n01 < -0.5 and n10 < -0.5, "half-selected neighbor flipped"
    assert after_read < -0.5, f"READ via FWD path failed, state={after_read}"
    assert sense_peak > 0.5, f"sense spike missing on READ, peak={sense_peak}"
    # ICD strobe ~150–300 ns into READ: bit already valid, bank still enabled
    assert at_strobe < -0.5, f"strobe aperture missing destroyed-1, state={at_strobe}"
    assert en_at_strobe > 0.5, "FWD path dropped before strobe"


def test_fwd_rev_mutex():
    """Both FWD and REV asserted → no drive (mutex)."""
    time_s, states, _sense, _dout, en_x, elapsed = run_l2_transient(
        fwd_en_n_pwl="PWL(0 0)",
        rev_en_n_pwl="PWL(0 0)",
        dec_en_pwl="PWL(0 1)",
        end_time=1.0e-6,
        state_ic={"m00": 1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0},
    )
    assert elapsed < RUNTIME_BUDGET_S
    assert sample_at(time_s, en_x, 0.5e-6) < 0.1
    assert sample_at(time_s, states["m00"], 0.8e-6) > 0.5


def test_failsafe_enables():
    """Idle fail-safe (FWD/REV inactive, DEC off) → no drive."""
    time_s, states, _sense, _dout, en_x, elapsed = run_l2_transient(
        fwd_en_n_pwl="PWL(0 1)",
        rev_en_n_pwl="PWL(0 1)",
        dec_en_pwl="PWL(0 0)",
        end_time=1.0e-6,
        state_ic={"m00": 1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0},
    )
    assert elapsed < RUNTIME_BUDGET_S
    assert sample_at(time_s, en_x, 0.5e-6) < 0.1
    assert sample_at(time_s, states["m00"], 0.8e-6) > 0.5
