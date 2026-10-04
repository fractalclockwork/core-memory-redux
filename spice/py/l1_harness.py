"""Build and run L1 2×2 oracle transients for GATE-L1-CYCLE."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_ns

from ngspice_compat import patch_ngspice_stderr_false_positives

ROOT = Path(__file__).resolve().parents[2]
CHAN_LIB = ROOT / "spice" / "models" / "chan_core.lib"
CCS_LIB = ROOT / "spice" / "models" / "ideal_ccs.lib"

# Sim assumption — not a frozen ICD value.
I_HALF = 0.3  # Ic/2 with Ic=600 mA

CORE_STATE = {
    "m00": "xm00.state",
    "m01": "xm01.state",
    "m10": "xm10.state",
    "m11": "xm11.state",
}


def _array_netlist() -> str:
    """2×2 weave + REQ-ICD-FOLD sense (implementation_summary stand-in)."""
    return """
xm00 xa0_d xa0_m ya0_d ya0_m sa_m00 sa_m00n chan_core
xm10 xa0_m xa0_r ya1_d ya1_m sb_m10 sb_m10n chan_core
xm01 xa1_d xa1_m ya0_m ya0_r sb_m01 sb_m01n chan_core
xm11 xa1_m xa1_r ya1_m ya1_r sa_m11 sa_m11n chan_core
* Loop A even: YA65 → MCE11 → MCE00 → YA66
Rsa1 ya65 sa_m11 1m
Rsa2 sa_m11n sa_m00 1m
Rsa3 sa_m00n ya66 1m
* Loop B odd: YB65 → MCE10 → MCE01 → YB66
Rsb1 yb65 sb_m10 1m
Rsb2 sb_m10n sb_m01 1m
Rsb3 sb_m01n yb66 1m
Rfold ya66 yb65 1m
Rsoft ya66 0 10k
* Unselected line parks
Rpark_x1d xa1_d 0 100Meg
Rpark_x1r xa1_r 0 100Meg
Rpark_y1d ya1_d 0 100Meg
Rpark_y1r ya1_r 0 100Meg
"""


def run_l1_transient(
    *,
    en_x_pwl: str,
    en_y_pwl: str,
    en_i_pwl: str,
    pol_xy_pwl: str,
    pol_i_pwl: str = "PWL(0 1)",
    end_time: float,
    state_ic: dict[str, float] | None = None,
    step_time: float = 5e-9,
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, float]:
    """Run address-(0,0) oracle with gated CCS_X/Y/INH.

    Returns time, state dict (m00..), differential sense YA65-YB66, inhibit
    path MMF proxy (xm00.mmf), wall seconds.
    """
    patch_ngspice_stderr_false_positives()

    if state_ic is None:
        state_ic = {"m00": -1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0}

    circuit = Circuit("GATE-L1-CYCLE")
    circuit.raw_spice += CHAN_LIB.read_text(encoding="utf-8") + "\n"
    circuit.raw_spice += CCS_LIB.read_text(encoding="utf-8") + "\n"
    circuit.raw_spice += _array_netlist()

    # Address (0,0): short XA0/YA0 drive ends to AGND when that CCS is enabled;
    # CCS sinks/sources at the return ends. Inhibit: short YA65, CCS on YB66.
    circuit.raw_spice += f"""
xsw_xd xa0_d 0 en_x ideal_drive_switch
xsw_yd ya0_d 0 en_y ideal_drive_switch
xccs_x xa0_r 0 en_x pol_xy ideal_ccs
xccs_y ya0_r 0 en_y pol_xy ideal_ccs
xsw_inh ya65 0 en_i ideal_drive_switch
xccs_i yb66 0 en_i pol_i ideal_ccs
Venx en_x 0 {en_x_pwl}
Veny en_y 0 {en_y_pwl}
Veni en_i 0 {en_i_pwl}
Vpolxy pol_xy 0 {pol_xy_pwl}
Vpoli pol_i 0 {pol_i_pwl}
.ic v(xm00.state)={state_ic["m00"]} v(xm01.state)={state_ic["m01"]} v(xm10.state)={state_ic["m10"]} v(xm11.state)={state_ic["m11"]}
"""

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    t0 = time.perf_counter()
    analysis = simulator.transient(
        step_time=step_time * 1e9 @ u_ns,
        end_time=end_time,
        use_initial_condition=True,
    )
    elapsed = time.perf_counter() - t0

    time_s = np.asarray(analysis.time, dtype=float)
    states = {k: np.asarray(analysis[v], dtype=float) for k, v in CORE_STATE.items()}
    sense = np.asarray(analysis["ya65"], dtype=float) - np.asarray(
        analysis["yb66"], dtype=float
    )
    mmf00 = np.asarray(analysis["xm00.mmf"], dtype=float)
    return time_s, states, sense, mmf00, elapsed


def sample_at(time_s: np.ndarray, values: np.ndarray, t: float) -> float:
    return float(values[np.argmin(np.abs(time_s - t))])


def peak_abs(time_s: np.ndarray, values: np.ndarray, t0: float, t1: float) -> float:
    mask = (time_s >= t0) & (time_s <= t1)
    if not np.any(mask):
        return 0.0
    return float(np.max(np.abs(values[mask])))
