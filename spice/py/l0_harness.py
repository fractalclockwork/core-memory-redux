"""Build and run L0 single-core transients for GATE-L0-PHYSICS."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_kΩ, u_ns

from ngspice_compat import patch_ngspice_stderr_false_positives

ROOT = Path(__file__).resolve().parents[2]
CHAN_LIB = ROOT / "spice" / "models" / "chan_core.lib"

# Sim assumption (deck header / tests) — not a frozen ICD value.
I_HALF = 0.3  # Ic/2 with Ic=600 mA


def _lib_text() -> str:
    return CHAN_LIB.read_text(encoding="utf-8")


def run_l0_transient(
    ix_pwl: str,
    iy_pwl: str,
    *,
    end_time: float,
    state_ic: float = 1.0,
    step_time: float = 5e-9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Return time, state, sense, mmf, and wall seconds."""
    patch_ngspice_stderr_false_positives()

    circuit = Circuit("GATE-L0-PHYSICS")
    circuit.raw_spice += _lib_text() + "\n"
    circuit.raw_spice += f".ic v(xcore.state)={state_ic}\n"
    circuit.X("core", "chan_core", "xp", circuit.gnd, "yp", circuit.gnd, "sp", circuit.gnd)
    circuit.R("sense", "sp", circuit.gnd, 1 @ u_kΩ)
    circuit.I("x", circuit.gnd, "xp", ix_pwl)
    circuit.I("y", circuit.gnd, "yp", iy_pwl)

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    t0 = time.perf_counter()
    analysis = simulator.transient(
        step_time=step_time * 1e9 @ u_ns,
        end_time=end_time,
        use_initial_condition=True,
    )
    elapsed = time.perf_counter() - t0

    time_s = np.asarray(analysis.time, dtype=float)
    state = np.asarray(analysis["xcore.state"], dtype=float)
    sense = np.asarray(analysis["sp"], dtype=float)
    mmf = np.asarray(analysis["xcore.mmf"], dtype=float)
    return time_s, state, sense, mmf, elapsed


def sample_at(time_s: np.ndarray, values: np.ndarray, t: float) -> float:
    return float(values[np.argmin(np.abs(time_s - t))])


def peak_abs(time_s: np.ndarray, values: np.ndarray, t0: float, t1: float) -> float:
    mask = (time_s >= t0) & (time_s <= t1)
    if not np.any(mask):
        return 0.0
    return float(np.max(np.abs(values[mask])))
