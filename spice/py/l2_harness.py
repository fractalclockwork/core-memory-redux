"""Build and run L2 driver e2e transients for GATE-L2-E2E."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_ns

from l1_harness import CORE_STATE, _array_netlist
from ngspice_compat import patch_ngspice_stderr_false_positives

ROOT = Path(__file__).resolve().parents[2]
CHAN_LIB = ROOT / "spice" / "models" / "chan_core.lib"
CCS_LIB = ROOT / "spice" / "models" / "ideal_ccs.lib"
DMOS_LIB = ROOT / "spice" / "models" / "dmos_ahc.lib"

I_HALF = 0.3


def _driver_netlist() -> str:
    """AHC decode → line enables → ideal CCS (L1 current plant).

    Pin-faithful n=2 subset of decode_block + DMOS call model (naming.md).
    DMOS/SS14 polarity is represented by active-low HS / active-high LS decode
    outs gating the CCS path (behavioral abstraction — not transistor-level).
    FWD_EN_n / REV_EN_n active-low; DEC_EN active-high.
    Mutex: both banks requested → neither drives.
    """
    return """
* Mutex + chip enable
Bfwd_ok fwd_ok 0 V={u(0.5-V(fwd_en_n)) * u(V(rev_en_n)-0.5) * u(V(dec_en)-0.5)}
Brev_ok rev_ok 0 V={u(0.5-V(rev_en_n)) * u(V(fwd_en_n)-0.5) * u(V(dec_en)-0.5)}
Bfwd_bank fwd_bank_n 0 V={1 - V(fwd_ok)}
Brev_bank rev_bank_n 0 V={1 - V(rev_ok)}

* HS held at line-group 0 for n=2 (line = 8*HS + LS with HS=0)
Vaddr_xh addr_xh 0 0
Vaddr_yh addr_yh 0 0

* X: 138 HS (active-low) + 238 LS (active-high) × FWD/REV
xdec_x_fwd_ls addr_x0 fwd_bank_n dec_en x_fwd_ls0_en x_fwd_ls1_en ahc238_2line
xdec_x_fwd_hs addr_xh fwd_bank_n dec_en x_fwd_hs0_n x_fwd_hs1_n ahc138_2line
xdec_x_rev_ls addr_x0 rev_bank_n dec_en x_rev_ls0_en x_rev_ls1_en ahc238_2line
xdec_x_rev_hs addr_xh rev_bank_n dec_en x_rev_hs0_n x_rev_hs1_n ahc138_2line

* Y decode
xdec_y_fwd_ls addr_y0 fwd_bank_n dec_en y_fwd_ls0_en y_fwd_ls1_en ahc238_2line
xdec_y_fwd_hs addr_yh fwd_bank_n dec_en y_fwd_hs0_n y_fwd_hs1_n ahc138_2line
xdec_y_rev_ls addr_y0 rev_bank_n dec_en y_rev_ls0_en y_rev_ls1_en ahc238_2line
xdec_y_rev_hs addr_yh rev_bank_n dec_en y_rev_hs0_n y_rev_hs1_n ahc138_2line

* DMOS input polarity: HS active-low AND LS active-high → channel on
Bsel_xf0 sel_x_fwd0 0 V={u(0.5-V(x_fwd_hs0_n)) * u(V(x_fwd_ls0_en)-0.5)}
Bsel_xr0 sel_x_rev0 0 V={u(0.5-V(x_rev_hs0_n)) * u(V(x_rev_ls0_en)-0.5)}
Bsel_yf0 sel_y_fwd0 0 V={u(0.5-V(y_fwd_hs0_n)) * u(V(y_fwd_ls0_en)-0.5)}
Bsel_yr0 sel_y_rev0 0 V={u(0.5-V(y_rev_hs0_n)) * u(V(y_rev_ls0_en)-0.5)}

Benx en_x 0 V={V(sel_x_fwd0) + V(sel_x_rev0)}
Beny en_y 0 V={V(sel_y_fwd0) + V(sel_y_rev0)}

* Polarity: REV WRITE = +1, FWD READ = -1 (coincident bank)
Bpol pol_xy 0 V={u(V(sel_x_rev0)+V(sel_y_rev0)-0.5) - u(V(sel_x_fwd0)+V(sel_y_fwd0)-0.5)}
* If neither, pol=0 (safe)

* Proven L1 current plant on XA0/YA0, gated by decode
xsw_xd xa0_d 0 en_x ideal_drive_switch
xsw_yd ya0_d 0 en_y ideal_drive_switch
xccs_x xa0_r 0 en_x pol_xy ideal_ccs
xccs_y ya0_r 0 en_y pol_xy ideal_ccs

* Symbolic SS14 drop on returns (steer presence)
xss_x xa0_r xa0_r_d ss14
Rss_x xa0_r_d 0 1Meg
xss_y ya0_r ya0_r_d ss14
Rss_y ya0_r_d 0 1Meg

* Inhibit outside Drive/Decode
xsw_inh ya65 0 en_i ideal_drive_switch
xccs_i yb66 0 en_i pol_i ideal_ccs

* Sense comparator (strobe surface)
xcmp ya65 yb66 dout tlv3501
"""


def run_l2_transient(
    *,
    addr_x0: float = 0.0,
    addr_y0: float = 0.0,
    fwd_en_n_pwl: str,
    rev_en_n_pwl: str,
    dec_en_pwl: str,
    en_i_pwl: str = "PWL(0 0)",
    pol_i_pwl: str = "PWL(0 1)",
    end_time: float,
    state_ic: dict[str, float] | None = None,
    step_time: float = 5e-9,
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, np.ndarray, float]:
    """Returns time, states, sense diff, dout, en_x, elapsed."""
    patch_ngspice_stderr_false_positives()

    if state_ic is None:
        state_ic = {"m00": -1.0, "m01": -1.0, "m10": -1.0, "m11": -1.0}

    circuit = Circuit("GATE-L2-E2E")
    circuit.raw_spice += CHAN_LIB.read_text(encoding="utf-8") + "\n"
    circuit.raw_spice += CCS_LIB.read_text(encoding="utf-8") + "\n"
    circuit.raw_spice += DMOS_LIB.read_text(encoding="utf-8") + "\n"
    circuit.raw_spice += _array_netlist()
    circuit.raw_spice += _driver_netlist()
    circuit.raw_spice += f"""
Vaddr_x0 addr_x0 0 {addr_x0}
Vaddr_y0 addr_y0 0 {addr_y0}
Vfwd fwd_en_n 0 {fwd_en_n_pwl}
Vrev rev_en_n 0 {rev_en_n_pwl}
Vdec dec_en 0 {dec_en_pwl}
Veni en_i 0 {en_i_pwl}
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
    dout = np.asarray(analysis["dout"], dtype=float)
    en_x = np.asarray(analysis["en_x"], dtype=float)
    return time_s, states, sense, dout, en_x, elapsed


def sample_at(time_s: np.ndarray, values: np.ndarray, t: float) -> float:
    return float(values[np.argmin(np.abs(time_s - t))])


def peak_abs(time_s: np.ndarray, values: np.ndarray, t0: float, t1: float) -> float:
    mask = (time_s >= t0) & (time_s <= t1)
    if not np.any(mask):
        return 0.0
    return float(np.max(np.abs(values[mask])))


def peak_time(time_s: np.ndarray, values: np.ndarray, t0: float, t1: float) -> float:
    mask = (time_s >= t0) & (time_s <= t1)
    if not np.any(mask):
        return float("nan")
    idx = np.argmax(np.abs(values[mask]))
    return float(time_s[mask][idx])
