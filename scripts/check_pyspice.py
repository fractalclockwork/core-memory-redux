#!/usr/bin/env python3
"""Smoke-check PySpice against system libngspice (Ubuntu ngspice 42+)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "spice" / "py"))

from ngspice_compat import patch_ngspice_stderr_false_positives  # noqa: E402


def main() -> int:
    import PySpice
    from PySpice.Spice.Netlist import Circuit
    import PySpice.Unit as U

    patch_ngspice_stderr_false_positives()

    circuit = Circuit("cmr-smoke")
    circuit.V("in", "vin", circuit.gnd, 1 @ U.u_V)
    circuit.R(1, "vin", "out", 1 @ U.u_kΩ)
    circuit.C(1, "out", circuit.gnd, 1 @ U.u_uF)

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    try:
        analysis = simulator.transient(step_time=1 @ U.u_us, end_time=100 @ U.u_us)
        n = len(analysis.out)
        v_end = float(analysis.out[-1])
    except Exception as exc:  # noqa: BLE001
        print(f"PySpice smoke check FAILED: {exc}")
        return 1

    if n <= 0 or v_end <= 0.05:
        print(f"PySpice smoke check FAILED: unexpected waveform (n={n}, v_end={v_end})")
        return 1

    print(f"PySpice {PySpice.__version__} smoke OK ({n} points, v_out={v_end:.3f} V)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
