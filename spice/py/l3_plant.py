"""N×N ideal_core plant + line R/L/C for GATE-L3-SIL.

Driven by synthetic PIO/decode stimuli (no MCU firmware in-tree yet).
Fold model: REQ-ICD-FOLD series sense path; inhibit is sense-wire current.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ideal_core import IdealCore

# Line impedance (sim assumption for settling; not a frozen ICD).
LINE_R = 2.0  # Ω
LINE_L = 200e-9  # H
LINE_C = 50e-12  # F


@dataclass
class LineRLC:
    """Lumped R/L/C used to compute a first-order settle time."""

    R: float = LINE_R
    L: float = LINE_L
    C: float = LINE_C

    @property
    def tau(self) -> float:
        """Dominant inductive settle τ = L/R; C is tracked for budget checks."""
        _ = self.C  # retained for GATE-L3 line R/L/C completeness
        return self.L / self.R if self.R > 0 else 0.0

    def settle_time(self, n_tau: float = 5.0) -> float:
        return n_tau * self.tau


@dataclass
class L3Plant:
    """Square array of IdealCore with per-line R/L/C metadata."""

    n: int
    cores: list[list[IdealCore]] = field(init=False)
    x_lines: list[LineRLC] = field(init=False)
    y_lines: list[LineRLC] = field(init=False)
    sense_line: LineRLC = field(init=False)
    sim_time: float = 0.0

    def __post_init__(self) -> None:
        if self.n < 2:
            raise ValueError("L3 plant requires n>=2")
        self.cores = [[IdealCore(-1.0) for _ in range(self.n)] for _ in range(self.n)]
        self.x_lines = [LineRLC() for _ in range(self.n)]
        self.y_lines = [LineRLC() for _ in range(self.n)]
        self.sense_line = LineRLC()

    def line_settle(self) -> float:
        """Worst-case line settle among X/Y/sense (seconds)."""
        return max(
            self.x_lines[0].settle_time(),
            self.y_lines[0].settle_time(),
            self.sense_line.settle_time(),
        )

    def advance(self, dt: float) -> None:
        self.sim_time += dt

    def coincident(
        self,
        x: int,
        y: int,
        i_half: float,
        isense: float = 0.0,
    ) -> float:
        """Apply settled currents once: full-select (x,y), half-select neighbors.

        Returns sense pulse from the addressed core only.
        """
        if not (0 <= x < self.n and 0 <= y < self.n):
            raise IndexError(f"addr ({x},{y}) out of range for n={self.n}")

        # Half-select along driven X (other Y): must not flip.
        for j in range(self.n):
            if j == y:
                continue
            self.cores[x][j].apply(i_half, 0.0, isense)
        # Half-select along driven Y (other X).
        for i in range(self.n):
            if i == x:
                continue
            self.cores[i][y].apply(0.0, i_half, isense)

        return self.cores[x][y].apply(i_half, i_half, isense)

    def inhibit_all(self, isense: float) -> None:
        """Series inhibit through fold: sense current on every core (half-select)."""
        for i in range(self.n):
            for j in range(self.n):
                self.cores[i][j].apply(0.0, 0.0, isense)

    def state_matrix(self) -> np.ndarray:
        return np.array(
            [[c.state for c in row] for row in self.cores], dtype=float
        )
