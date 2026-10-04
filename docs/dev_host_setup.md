# Dev-host setup (Ubuntu)

**Status:** `sketch` (derived host procedure — does not override design owners)  
**Owns:** Ubuntu apt + `uv` install steps for the planned SIL/generator host  
**Does not own:** ICD, BOM, timing, or fabric ABI — see [AUTHORITY.md](AUTHORITY.md)

This repository is **docs-bootstrap**: generators, KiCad trees, and SPICE decks are not in-tree yet. The steps below install the **host baseline** so that work can start without inventing ad-hoc environments.

**Target OS:** Ubuntu 22.04 / 24.04 (package names below match both unless noted).

## 1. System packages (required for SIL host)

```bash
sudo apt update
sudo apt install -y \
  build-essential curl git ca-certificates \
  ngspice libngspice0-dev
```

| Package | Role |
|---------|------|
| `build-essential` | Compilers / make for native Python wheels when needed |
| `curl` / `git` / `ca-certificates` | Fetch uv, clone, TLS |
| `ngspice` | CLI SPICE engine |
| `libngspice0-dev` | Shared library plus unversioned `libngspice.so` symlink that PySpice expects |

## 2. Install uv

Prefer the [official standalone installer](https://docs.astral.sh/uv/getting-started/installation/) over distro `pip`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Ensure `~/.local/bin` is on your `PATH` (open a new shell or source your profile), then:

```bash
uv --version
```

## 3. Project Python environment

From the repository root:

```bash
uv python install 3.12
uv sync
uv run python -c "import PySpice; print(PySpice.__version__)"
```

NgSpice / PySpice smoke check (use this, not upstream `--check-install`):

```bash
uv run python scripts/check_pyspice.py
```

**Note (Ubuntu 24.04 / ngspice 42 + PySpice 1.5):** Upstream
`uv run pyspice-post-installation --check-install` fails with
`NgSpiceCommandError: Command 'run' failed` even when the transient
succeeds. Newer ngspice prints `Using SPARSE 1.3 as Direct Linear Solver`
on stderr; PySpice 1.5 treats any non-`Warning:` stderr as fatal
([PySpice#379](https://github.com/PySpice-org/PySpice/issues/379)).
`scripts/check_pyspice.py` ignores that informational line and verifies a
real transient.

`uv sync` creates `.venv` from [`pyproject.toml`](../pyproject.toml) and the committed `uv.lock`. Generators and SIL modules are **not present yet**; this env is the host baseline for upcoming work.

## 4. Optional later: KiCad

Not required for Phase 0–2 SIL. Install when starting L4 schematic fabric work:

```bash
sudo apt install -y kicad
```

**NgSpice note:** KiCad may pull in `libngspice-kicad`, which can collide with `libngspice0` / `libngspice0-dev`. If PySpice then fails to find `libngspice.so`, create a symlink to the versioned library (paths may vary by arch):

```bash
sudo ln -sf /usr/lib/x86_64-linux-gnu/libngspice.so.0 \
  /usr/lib/x86_64-linux-gnu/libngspice.so
```

## 5. Explicitly not installed

- **RP2040 / Pico SDK** — deferred; not part of the current host setup. Timing design still assumes programmable I/O in the ICD; firmware tooling waits until bring-up.

## 6. Verify checklist

- [ ] `uv --version`
- [ ] `ngspice -v`
- [ ] `uv run python -c "import PySpice; print(PySpice.__version__)"`
- [ ] `uv run python scripts/check_pyspice.py`
- [ ] `uv run python scripts/run_gate.py GATE-L0-PHYSICS` (or `uv run pytest tests/test_l0_physics.py`)
- [ ] `uv run python scripts/run_gate.py GATE-L1-CYCLE` (or `uv run pytest tests/test_l1_cycle.py`)
- [ ] (optional) `kicad-cli --version` or Help → About in the KiCad GUI
