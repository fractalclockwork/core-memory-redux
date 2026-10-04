# L3 — ideal \(N \times N\) SIL (`GATE-L3-SIL`)

Behavioral `ideal_core` plant (not Chan). Primary surface is Python SIL under
[`spice/py/l3_plant.py`](../py/l3_plant.py) / [`l3_harness.py`](../py/l3_harness.py).

- Model atom: [`spice/models/ideal_core.lib`](../models/ideal_core.lib) (SPICE
  declaration of the same threshold-law abstraction).
- Gate tests: [`tests/test_l3_sil.py`](../../tests/test_l3_sil.py).
- Owner: [docs/system_design_spec.md](../../docs/system_design_spec.md) **GATE-L3-SIL**.
