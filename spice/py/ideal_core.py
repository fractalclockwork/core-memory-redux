"""Behavioral ideal_core for GATE-L3-SIL (threshold-law Ic flip).

Not Chan / coremem. Sim assumption: Ic=600 mA, Ic/2=300 mA.
"""

from __future__ import annotations

from dataclasses import dataclass

# Sim assumption — not a frozen ICD value (design_choices stays open).
I_HALF = 0.3
I_FULL = 2.0 * I_HALF  # coincident full-select threshold
SENSE_PULSE = 1.0  # fixed destructive-read amplitude (arb. units)


@dataclass
class IdealCore:
    """Three-wire threshold core: state ±1; sense pulse on destructive READ."""

    state: float = -1.0  # +1 = stored-1, −1 = stored-0

    def apply(self, ix: float, iy: float, isense: float = 0.0) -> float:
        """Apply axis/sense currents (amperes). Returns sense pulse amplitude."""
        mmf = ix + iy + isense
        if abs(mmf) < I_FULL - 1e-9:
            return 0.0
        new_state = 1.0 if mmf > 0.0 else -1.0
        pulse = 0.0
        if new_state < 0.0 and self.state > 0.0:
            pulse = SENSE_PULSE
        self.state = new_state
        return pulse
