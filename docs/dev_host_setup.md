# Dev-host setup (Ubuntu)

**Status:** `sketch` (derived host procedure — does not override design owners)  
**Owns:** Ubuntu apt + `uv` install steps for the planned SIL/generator host  
**Does not own:** ICD, BOM, timing, or fabric ABI — see [AUTHORITY.md](AUTHORITY.md)

The steps below install the **host baseline** for L0–L3 sim/SIL and L4 schematic fabric (`kicad-cli` ERC). Design contracts stay under [`docs/`](./); do not invent ad-hoc environments.

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

`uv sync` creates `.venv` from [`pyproject.toml`](../pyproject.toml) and the committed `uv.lock`. L0–L3 modules live under `spice/`; L4 fabric generators under `generators/` emit into `kicad/`.

## 4. KiCad 10.0.6 (required for GATE-L4-FABRIC)

KiCad is **not** required for L0–L3 PySpice gates. It **is** required to emit/check L4 hierarchical schematics (`kicad-cli sch erc`).

**Pinned host version:** **10.0.6** (current stable). Use the official [KiCad 10.0 releases PPA](https://launchpad.net/~kicad/+archive/ubuntu/kicad-10.0-releases) — do **not** rely on the Ubuntu universe package (often years behind on 22.04/24.04). Upstream install notes: [kicad.org/download/ubuntu](https://www.kicad.org/download/details/ubuntu/).

### Install (official 10.0 PPA)

```bash
sudo add-apt-repository --yes ppa:kicad/kicad-10.0-releases
sudo apt update
sudo apt install --install-recommends -y kicad
```

That installs the GUI (`kicad`), CLI (`kicad-cli`), and recommended libraries. Confirm the package version lands on 10.0.6:

```bash
apt-cache policy kicad | head -20
# Candidate should look like: 10.0.6~ubuntu24.04.1 (or ~ubuntu22.04.1)
```

If an older distro `kicad` was already installed, the PPA upgrade should replace it after `apt update` + install. Prefer removing leftover nightly/testing PPAs (`kicad-10.0-nightly`, etc.) so apt does not prefer a non-stable build.

### Verify CLI

```bash
kicad-cli --version
kicad-cli sch --help
```

Expect a **10.0.6** version string and a `sch` subcommand that lists `erc`.

### ERC smoke (after generators have produced a project)

```bash
# From repo root, after: uv run python -m generators.cli --n 2
kicad-cli sch erc --format report --output /tmp/bringup_erc.rpt \
  kicad/bringup_2x2/driver.kicad_sch
```

Or run the gate wrapper (preferred):

```bash
uv run python scripts/run_gate.py GATE-L4-FABRIC
# or: uv run python scripts/run_kicad_erc.py
```

### NgSpice / PySpice coexistence

KiCad may pull in `libngspice-kicad`, which can collide with `libngspice0` / `libngspice0-dev`. If PySpice then fails to find `libngspice.so`, create a symlink to the versioned library (paths may vary by arch):

```bash
# amd64 example — adjust libdir for arm64 if needed
sudo ln -sf /usr/lib/x86_64-linux-gnu/libngspice.so.0 \
  /usr/lib/x86_64-linux-gnu/libngspice.so
```

Re-run `uv run python scripts/check_pyspice.py` after installing KiCad.

### GUI (optional)

```bash
kicad   # or open kicad/bringup_2x2/*.kicad_pro from the file manager
```

Help → About is fine for a human sanity check; gates use `kicad-cli` only.

## 5. Explicitly not installed

- **RP2040 / Pico SDK** — deferred; not part of the current host setup. Timing design still assumes programmable I/O in the ICD; firmware tooling waits until bring-up.

## 6. Verify checklist

- [ ] `uv --version`
- [ ] `ngspice -v`
- [ ] `uv run python -c "import PySpice; print(PySpice.__version__)"`
- [ ] `uv run python scripts/check_pyspice.py`
- [ ] `uv run python scripts/run_gate.py GATE-L0-PHYSICS` (or `uv run pytest tests/test_l0_physics.py`)
- [ ] `uv run python scripts/run_gate.py GATE-L1-CYCLE` (or `uv run pytest tests/test_l1_cycle.py`)
- [ ] `uv run python scripts/run_gate.py GATE-L2-E2E` (or `uv run pytest tests/test_l2_e2e.py`)
- [ ] `uv run python scripts/run_gate.py GATE-L3-SIL` (or `uv run pytest tests/test_l3_sil.py`)
- [ ] `kicad-cli --version` shows **10.0.6** (required for L4; from `ppa:kicad/kicad-10.0-releases`)
- [ ] `uv run python scripts/run_gate.py GATE-L4-FABRIC` (or `uv run pytest tests/test_l4_fabric.py`)
