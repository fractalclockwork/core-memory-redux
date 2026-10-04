#!/usr/bin/env python3
"""Render writeup figures from the existing L0–L3 harnesses.

Stimulus strings match the gate tests. This script does not modify decks,
harnesses, or tests. It writes PNGs and results.json under writeup/figures/.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "spice" / "py"))

from ideal_core import I_HALF  # noqa: E402
from l0_harness import (  # noqa: E402
    peak_abs as l0_peak_abs,
)
from l0_harness import (  # noqa: E402
    run_l0_transient,
    sample_at as l0_sample_at,
)
from l1_harness import (  # noqa: E402
    peak_abs as l1_peak_abs,
)
from l1_harness import (  # noqa: E402
    run_l1_transient,
    sample_at as l1_sample_at,
)
from l2_harness import (  # noqa: E402
    peak_abs as l2_peak_abs,
)
from l2_harness import (  # noqa: E402
    run_l2_transient,
    sample_at as l2_sample_at,
)
from l3_harness import (  # noqa: E402
    pio_write,
    run_continuous_sparse,
    run_diagonal_pattern,
    run_random_sparse,
)
from l3_plant import L3Plant  # noqa: E402

FIG = ROOT / "writeup" / "figures"

# Same experiments as tests/test_l0_physics.py, test_l1_cycle.py,
# test_l2_e2e.py, and test_l3_sil.py.
L0_HALF_IX = (
    f"PWL(0 0 50n 0 100n {I_HALF} 800n {I_HALF} 850n 0 "
    f"1.2u 0 1.25u {I_HALF} 2.0u {I_HALF} 2.05u 0)"
)
L0_HALF_IY = f"PWL(0 0 50n 0 100n {I_HALF} 800n {I_HALF} 850n 0 1.2u 0 2.05u 0)"
L0_READ1_IX = (
    f"PWL(0 0 50n 0 100n {I_HALF} 800n {I_HALF} 850n 0 "
    f"1.5u 0 1.55u {-I_HALF} 2.3u {-I_HALF} 2.35u 0)"
)
L0_READ0_IX = (
    f"PWL(0 0 50n 0 100n {-I_HALF} 800n {-I_HALF} 850n 0 "
    f"1.5u 0 1.55u {-I_HALF} 2.3u {-I_HALF} 2.35u 0)"
)
L0_RESTORE_IX = (
    f"PWL(0 0 50n 0 100n {I_HALF} 600n {I_HALF} 650n 0 "
    f"1.2u 0 1.25u {-I_HALF} 1.9u {-I_HALF} 1.95u 0 "
    f"2.5u 0 2.55u {I_HALF} 3.2u {I_HALF} 3.25u 0)"
)
L1_EN_XY = (
    "PWL(0 0 50n 0 100n 1 800n 1 850n 0 "
    "1.5u 0 1.55u 1 2.3u 1 2.35u 0 "
    "2.7u 0 3.5u 0 "
    "3.55u 1 4.2u 1 4.25u 0)"
)
L1_EN_I = "PWL(0 0 2.8u 0 2.85u 1 3.4u 1 3.45u 0)"
L1_POL = "PWL(0 1 1.4u 1 1.45u -1 2.4u -1 2.45u 1 5u 1)"
L1_ZERO = {"m00": -1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0}
L2_REV = "PWL(0 1 50n 1 100n 0 800n 0 850n 1 5u 1)"
L2_FWD = "PWL(0 1 1.5u 1 1.55u 0 2.3u 0 2.35u 1 5u 1)"
L2_T_READ = 1.55e-6
L2_T_STROBE = 200e-9


def _us(time_s: np.ndarray) -> np.ndarray:
    return np.asarray(time_s, dtype=float) * 1e6


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.alpha": 0.35,
            "grid.linewidth": 0.6,
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "legend.frameon": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _save(fig: plt.Figure, name: str) -> str:
    path = FIG / f"{name}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}", flush=True)
    return path.name


def _num(value: float) -> float:
    return float(value)


def render_l0(results: dict) -> None:
    print("L0 half-select", flush=True)
    t, state, _sense, mmf, elapsed = run_l0_transient(
        L0_HALF_IX, L0_HALF_IY, end_time=2.5e-6, state_ic=1.0
    )
    after_write = l0_sample_at(t, state, 1.0e-6)
    during_half = l0_sample_at(t, mmf, 1.6e-6)
    after_half = l0_sample_at(t, state, 2.3e-6)

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(7.2, 5.2))
    axes[0].plot(_us(t), state, color="#1f4e79", lw=1.6)
    axes[0].set_ylabel("remanent state")
    axes[0].set_ylim(-1.15, 1.15)
    axes[0].set_title("Half-select holds a stored 1")
    axes[0].axvspan(1.25, 2.00, color="#1f4e79", alpha=0.08, lw=0)
    axes[1].plot(_us(t), mmf, color="#9a3412", lw=1.6)
    axes[1].set_ylabel("MMF (A)")
    axes[1].set_xlabel("time (µs)")
    axes[1].axvspan(1.25, 2.00, color="#1f4e79", alpha=0.08, lw=0)
    fig.tight_layout()
    half_name = _save(fig, "l0_half_select")

    print("L0 read discrimination", flush=True)
    t1, st1, s1, _m1, e1 = run_l0_transient(
        L0_READ1_IX, L0_READ1_IX, end_time=3.0e-6, state_ic=1.0
    )
    t0, st0, s0, _m0, e0 = run_l0_transient(
        L0_READ0_IX, L0_READ0_IX, end_time=3.0e-6, state_ic=1.0
    )
    peak1 = l0_peak_abs(t1, s1, 1.5e-6, 2.5e-6)
    peak0 = l0_peak_abs(t0, s0, 1.5e-6, 2.5e-6)

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot(_us(t1), s1, color="#1f4e79", lw=1.6, label="read of stored 1")
    ax.plot(_us(t0), s0, color="#9a3412", lw=1.6, label="read of stored 0")
    ax.axvspan(1.5, 2.5, color="#1f4e79", alpha=0.08, lw=0)
    ax.set_xlabel("time (µs)")
    ax.set_ylabel("sense (V)")
    ax.set_title("Destructive read: stored 1 versus stored 0")
    ax.legend(loc="upper right")
    fig.tight_layout()
    read_name = _save(fig, "l0_read_discrimination")

    print("L0 restore", flush=True)
    tr, sr, _ss, _mm, er = run_l0_transient(
        L0_RESTORE_IX, L0_RESTORE_IX, end_time=3.8e-6, state_ic=1.0
    )
    after_w = l0_sample_at(tr, sr, 0.9e-6)
    after_r = l0_sample_at(tr, sr, 2.2e-6)
    after_rest = l0_sample_at(tr, sr, 3.5e-6)

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot(_us(tr), sr, color="#1f4e79", lw=1.6)
    for x, label in ((0.9, "after write"), (2.2, "after read"), (3.5, "after restore")):
        ax.axvline(x, color="#57534e", lw=0.8, ls="--")
        ax.text(x + 0.05, 0.15, label, rotation=90, va="bottom", fontsize=9, color="#57534e")
    ax.set_xlabel("time (µs)")
    ax.set_ylabel("remanent state")
    ax.set_title("Write, destructive read, write-back")
    fig.tight_layout()
    restore_name = _save(fig, "l0_restore")

    results["l0"] = {
        "half_select": {
            "figure": half_name,
            "elapsed_s": _num(elapsed),
            "state_after_write": _num(after_write),
            "mmf_during_half_a": _num(during_half),
            "state_after_half": _num(after_half),
        },
        "read_discrimination": {
            "figure": read_name,
            "elapsed_read1_s": _num(e1),
            "elapsed_read0_s": _num(e0),
            "sense_peak_read1_v": _num(peak1),
            "sense_peak_read0_v": _num(peak0),
            "state_after_read1": _num(l0_sample_at(t1, st1, 2.7e-6)),
            "state_after_write0": _num(l0_sample_at(t0, st0, 1.0e-6)),
        },
        "restore": {
            "figure": restore_name,
            "elapsed_s": _num(er),
            "state_after_write": _num(after_w),
            "state_after_read": _num(after_r),
            "state_after_restore": _num(after_rest),
        },
    }


def render_l1(results: dict) -> None:
    print("L1 cycle", flush=True)
    t, states, sense, mmf, elapsed = run_l1_transient(
        en_x_pwl=L1_EN_XY,
        en_y_pwl=L1_EN_XY,
        en_i_pwl=L1_EN_I,
        pol_xy_pwl=L1_POL,
        pol_i_pwl="PWL(0 1)",
        end_time=5.0e-6,
        state_ic=dict(L1_ZERO),
    )
    colors = {
        "m00": "#1f4e79",
        "m01": "#0f766e",
        "m10": "#b45309",
        "m11": "#7c3aed",
    }
    labels = {
        "m00": "(0,0) addressed",
        "m01": "(0,1) half-select",
        "m10": "(1,0) half-select",
        "m11": "(1,1) unselected",
    }
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(7.4, 7.2))
    for key, series in states.items():
        axes[0].plot(_us(t), series, color=colors[key], lw=1.5, label=labels[key])
    axes[0].set_ylabel("remanent state")
    axes[0].set_title("2×2 write, read, inhibit, restore")
    axes[0].legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9)
    axes[1].plot(_us(t), sense, color="#1f4e79", lw=1.4)
    axes[1].set_ylabel("sense (V)")
    axes[2].plot(_us(t), mmf, color="#9a3412", lw=1.4)
    axes[2].set_ylabel("addressed MMF (A)")
    axes[2].set_xlabel("time (µs)")
    for ax in axes:
        ax.axvspan(0.10, 0.80, color="#1f4e79", alpha=0.06, lw=0)
        ax.axvspan(1.55, 2.30, color="#9a3412", alpha=0.08, lw=0)
        ax.axvspan(2.85, 3.40, color="#0f766e", alpha=0.08, lw=0)
        ax.axvspan(3.55, 4.20, color="#1f4e79", alpha=0.06, lw=0)
    fig.tight_layout()
    cycle_name = _save(fig, "l1_cycle")

    print("L1 current-source failure", flush=True)
    tf, states_f, _sf, _mf, elapsed_f = run_l1_transient(
        en_x_pwl="PWL(0 0)",
        en_y_pwl="PWL(0 0 50n 0 100n 1 800n 1 850n 0)",
        en_i_pwl="PWL(0 0)",
        pol_xy_pwl="PWL(0 1)",
        end_time=1.5e-6,
        state_ic={"m00": 1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0},
    )
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot(_us(tf), states_f["m00"], color="#1f4e79", lw=1.6, label="(0,0)")
    ax.plot(_us(tf), states_f["m01"], color="#0f766e", lw=1.2, label="(0,1)")
    ax.plot(_us(tf), states_f["m10"], color="#b45309", lw=1.2, label="(1,0)")
    ax.plot(_us(tf), states_f["m11"], color="#7c3aed", lw=1.2, label="(1,1)")
    ax.set_xlabel("time (µs)")
    ax.set_ylabel("remanent state")
    ax.set_title("X current source open: addressed core holds")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9)
    fig.tight_layout()
    fail_name = _save(fig, "l1_ccs_failure")

    results["l1"] = {
        "cycle": {
            "figure": cycle_name,
            "elapsed_s": _num(elapsed),
            "state_00_after_write": _num(l1_sample_at(t, states["m00"], 1.0e-6)),
            "state_01_after_write": _num(l1_sample_at(t, states["m01"], 1.0e-6)),
            "state_10_after_write": _num(l1_sample_at(t, states["m10"], 1.0e-6)),
            "state_00_after_read": _num(l1_sample_at(t, states["m00"], 2.5e-6)),
            "sense_peak_v": _num(l1_peak_abs(t, sense, 1.5e-6, 2.5e-6)),
            "mmf_during_inhibit_a": _num(l1_sample_at(t, mmf, 3.1e-6)),
            "state_00_after_restore": _num(l1_sample_at(t, states["m00"], 4.5e-6)),
        },
        "ccs_failure": {
            "figure": fail_name,
            "elapsed_s": _num(elapsed_f),
            "state_00_after": _num(l1_sample_at(tf, states_f["m00"], 1.0e-6)),
        },
    }


def render_l2(results: dict) -> None:
    print("L2 address path", flush=True)
    t, states, sense, _dout, en_x, elapsed = run_l2_transient(
        addr_x0=0.0,
        addr_y0=0.0,
        fwd_en_n_pwl=L2_FWD,
        rev_en_n_pwl=L2_REV,
        dec_en_pwl="PWL(0 1)",
        end_time=3.0e-6,
        state_ic=dict(L1_ZERO),
    )
    strobe_us = (L2_T_READ + L2_T_STROBE) * 1e6
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(7.2, 6.6))
    axes[0].plot(_us(t), states["m00"], color="#1f4e79", lw=1.6, label="(0,0)")
    axes[0].plot(_us(t), states["m01"], color="#0f766e", lw=1.2, label="(0,1)")
    axes[0].plot(_us(t), states["m10"], color="#b45309", lw=1.2, label="(1,0)")
    axes[0].set_ylabel("remanent state")
    axes[0].set_title("Address pins: reverse write, then forward read")
    axes[0].legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9)
    axes[1].plot(_us(t), sense, color="#1f4e79", lw=1.4)
    axes[1].set_ylabel("sense (V)")
    axes[2].plot(_us(t), en_x, color="#9a3412", lw=1.4)
    axes[2].set_ylabel("X line enable")
    axes[2].set_xlabel("time (µs)")
    for ax in axes:
        ax.axvline(strobe_us, color="#57534e", lw=0.9, ls="--")
    axes[1].text(
        strobe_us + 0.04,
        axes[1].get_ylim()[1],
        "strobe",
        fontsize=9,
        color="#57534e",
        va="top",
    )
    fig.tight_layout()
    addr_name = _save(fig, "l2_address_path")

    print("L2 mutex", flush=True)
    tm, states_m, _sm, _dm, en_m, elapsed_m = run_l2_transient(
        fwd_en_n_pwl="PWL(0 0)",
        rev_en_n_pwl="PWL(0 0)",
        dec_en_pwl="PWL(0 1)",
        end_time=1.0e-6,
        state_ic={"m00": 1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0},
    )
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(7.2, 4.8))
    axes[0].plot(_us(tm), en_m, color="#9a3412", lw=1.6)
    axes[0].set_ylabel("X line enable")
    axes[0].set_title("Forward and reverse both asserted")
    axes[0].set_ylim(-0.05, 1.05)
    axes[1].plot(_us(tm), states_m["m00"], color="#1f4e79", lw=1.6)
    axes[1].set_ylabel("remanent state")
    axes[1].set_ylim(-1.15, 1.15)
    axes[1].set_xlabel("time (µs)")
    fig.tight_layout()
    mutex_name = _save(fig, "l2_mutex")

    t_strobe = L2_T_READ + L2_T_STROBE
    results["l2"] = {
        "address_path": {
            "figure": addr_name,
            "elapsed_s": _num(elapsed),
            "state_00_after_write": _num(l2_sample_at(t, states["m00"], 1.0e-6)),
            "state_01_after_write": _num(l2_sample_at(t, states["m01"], 1.0e-6)),
            "state_10_after_write": _num(l2_sample_at(t, states["m10"], 1.0e-6)),
            "state_00_after_read": _num(l2_sample_at(t, states["m00"], 2.5e-6)),
            "state_00_at_strobe": _num(l2_sample_at(t, states["m00"], t_strobe)),
            "en_x_at_strobe": _num(l2_sample_at(t, en_x, t_strobe)),
            "sense_peak_v": _num(l2_peak_abs(t, sense, L2_T_READ - 50e-9, L2_T_READ + 150e-9)),
            "strobe_us": _num(strobe_us),
        },
        "mutex": {
            "figure": mutex_name,
            "elapsed_s": _num(elapsed_m),
            "en_x_mid": _num(l2_sample_at(tm, en_m, 0.5e-6)),
            "state_00_late": _num(l2_sample_at(tm, states_m["m00"], 0.8e-6)),
        },
    }


def render_l3(results: dict) -> None:
    print("L3 8×8 diagonal map", flush=True)
    plant = L3Plant(8)
    for i in range(8):
        for j in range(8):
            pio_write(plant, i, j, 1 if i == j else 0)
    matrix = plant.state_matrix()
    fig, ax = plt.subplots(figsize=(5.4, 4.8))
    image = ax.imshow(
        matrix,
        origin="upper",
        cmap="coolwarm",
        vmin=-1.0,
        vmax=1.0,
        interpolation="nearest",
    )
    ax.set_xlabel("Y")
    ax.set_ylabel("X")
    ax.set_title("8×8 after a diagonal write")
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="state")
    fig.tight_layout()
    map_name = _save(fig, "l3_diagonal_n8")

    print("L3 runtimes", flush=True)
    _p8, t_diag8 = run_diagonal_pattern(8)
    _ps8, t_sparse8 = run_random_sparse(8, n_cells=16, seed=42)
    _p64, t_diag64 = run_diagonal_pattern(64)
    _ps64, t_sparse64 = run_random_sparse(64, n_cells=64, seed=7)
    t_cont = run_continuous_sparse(64, cycles=500, seed=3)

    labels = [
        "8×8 diagonal",
        "8×8 sparse (16)",
        "64×64 diagonal",
        "64×64 sparse (64)",
        "64×64 × 500 cycles",
    ]
    times = [t_diag8, t_sparse8, t_diag64, t_sparse64, t_cont]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = np.arange(len(labels))
    ax.barh(y, times, color="#1f4e79", height=0.62)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(1e-4, max(times) * 12)
    for yi, val in zip(y, times):
        if val >= 1.0:
            label = f"{val:.2f} s"
        else:
            label = f"{val * 1e3:.2f} ms"
        ax.text(val * 1.35, yi, label, va="center", fontsize=9, color="#1f4e79")
    ax.set_xlabel(f"wall time (s, log) on {platform.node()}")
    ax.set_title("Ideal-core pattern runs")
    fig.tight_layout()
    bar_name = _save(fig, "l3_runtimes")

    ones = int(np.sum(matrix > 0.5))
    results["l3"] = {
        "diagonal_n8": {
            "figure": map_name,
            "ones_on_diagonal": ones,
            "shape": [8, 8],
        },
        "runtimes": {
            "figure": bar_name,
            "host": platform.node(),
            "diagonal_n8_s": _num(t_diag8),
            "sparse_n8_s": _num(t_sparse8),
            "diagonal_n64_s": _num(t_diag64),
            "sparse_n64_s": _num(t_sparse64),
            "continuous_n64_s": _num(t_cont),
        },
    }


def main() -> None:
    _style()
    FIG.mkdir(parents=True, exist_ok=True)
    results: dict = {
        "rendered_on": date.today().isoformat(),
        "rendered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": platform.node(),
        "ic_a": 0.6,
        "i_half_a": _num(I_HALF),
        "note": "Ic = 600 mA is a simulation assumption in the harnesses.",
    }
    render_l0(results)
    render_l1(results)
    render_l2(results)
    render_l3(results)
    out = FIG / "results.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
