"""GATE-L3-SIL harness: synthetic PIO/decode stimuli over L3Plant."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from ideal_core import I_HALF
from l3_plant import L3Plant

# REQ-ICD-TIMING stand-ins (seconds).
T_DRIVE = 700e-9
T_STROBE = 200e-9  # mid of ~150–300 ns window after READ edge
T_INHIBIT = 500e-9
T_GAP = 100e-9


@dataclass
class AccessResult:
    bit: int  # 1 or 0 as read
    sense_peak: float
    elapsed_s: float


def _addr_ok(n: int, x: int, y: int) -> None:
    if not (0 <= x < n and 0 <= y < n):
        raise IndexError(f"addr ({x},{y}) out of range for n={n}")


def _settle(plant: L3Plant, duration: float) -> None:
    """Advance sim time by max(requested, line R/L/C settle)."""
    plant.advance(max(duration, plant.line_settle()))


def pio_write(plant: L3Plant, x: int, y: int, bit: int) -> float:
    """Program a bit: destructive clear (−Ic/2) then WRITE/RESTORE (+Ic/2).

    bit=1 → no inhibit (full-select sets stored-1).
    bit=0 → inhibit on sense during WRITE so core holds 0 (REQ-ICD-TIMING).
    """
    _addr_ok(plant.n, x, y)
    t0 = time.perf_counter()
    _settle(plant, T_GAP)

    # Clear to 0 (same polarity as READ).
    plant.coincident(x, y, -I_HALF, isense=0.0)
    _settle(plant, T_DRIVE)

    isense = -I_HALF if bit == 0 else 0.0
    if bit == 0:
        plant.inhibit_all(isense)
        _settle(plant, T_INHIBIT)

    plant.coincident(x, y, +I_HALF, isense=isense)
    _settle(plant, T_DRIVE)
    _settle(plant, T_GAP)
    return time.perf_counter() - t0


def pio_read(plant: L3Plant, x: int, y: int) -> AccessResult:
    """Destructive READ (−Ic/2); sense valid at strobe after line settle."""
    _addr_ok(plant.n, x, y)
    t0 = time.perf_counter()
    _settle(plant, T_GAP)

    # Drive edge, then wait ICD strobe window (≥ line R/L/C settle).
    sense_peak = plant.coincident(x, y, -I_HALF, isense=0.0)
    _settle(plant, max(T_STROBE, plant.line_settle()))
    _settle(plant, max(0.0, T_DRIVE - T_STROBE))

    state_after = plant.cores[x][y].state
    bit = 1 if sense_peak > 0.5 else 0
    if bit == 1 and state_after > 0.0:
        raise AssertionError("destructive READ left stored-1")

    _settle(plant, T_GAP)
    return AccessResult(bit=bit, sense_peak=sense_peak, elapsed_s=time.perf_counter() - t0)


def pio_read_restore(plant: L3Plant, x: int, y: int) -> AccessResult:
    """Full READ / RESTORE cycle (restores the bit that was read)."""
    result = pio_read(plant, x, y)
    pio_write(plant, x, y, result.bit)
    return result


def run_diagonal_pattern(n: int) -> tuple[L3Plant, float]:
    """Write 1s on the diagonal, 0s elsewhere; verify with read/restore."""
    plant = L3Plant(n)
    t0 = time.perf_counter()
    for i in range(n):
        for j in range(n):
            pio_write(plant, i, j, 1 if i == j else 0)
    for i in range(n):
        for j in range(n):
            got = pio_read_restore(plant, i, j)
            expect = 1 if i == j else 0
            if got.bit != expect:
                raise AssertionError(
                    f"diagonal mismatch at ({i},{j}): got {got.bit} expect {expect}"
                )
    return plant, time.perf_counter() - t0


def run_random_sparse(
    n: int,
    *,
    n_cells: int,
    seed: int = 0,
) -> tuple[L3Plant, float]:
    """Write a sparse random pattern; verify with read/restore."""
    rng = np.random.default_rng(seed)
    cells: set[tuple[int, int]] = set()
    while len(cells) < n_cells:
        cells.add((int(rng.integers(0, n)), int(rng.integers(0, n))))
    bits = {c: int(rng.integers(0, 2)) for c in cells}

    plant = L3Plant(n)
    t0 = time.perf_counter()
    for (x, y), bit in bits.items():
        pio_write(plant, x, y, bit)
    for (x, y), bit in bits.items():
        got = pio_read_restore(plant, x, y)
        if got.bit != bit:
            raise AssertionError(
                f"sparse mismatch at ({x},{y}): got {got.bit} expect {bit}"
            )
    return plant, time.perf_counter() - t0


def run_continuous_sparse(
    n: int,
    *,
    cycles: int,
    seed: int = 1,
) -> float:
    """Many random access cycles; returns wall seconds (GATE-L3 runtime)."""
    rng = np.random.default_rng(seed)
    plant = L3Plant(n)
    for _ in range(min(n, 16)):
        x, y = int(rng.integers(0, n)), int(rng.integers(0, n))
        pio_write(plant, x, y, int(rng.integers(0, 2)))

    t0 = time.perf_counter()
    for _ in range(cycles):
        x, y = int(rng.integers(0, n)), int(rng.integers(0, n))
        if rng.random() < 0.5:
            pio_write(plant, x, y, int(rng.integers(0, 2)))
        else:
            pio_read_restore(plant, x, y)
    return time.perf_counter() - t0
