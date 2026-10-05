# Record

This folder is a human telling of work already in the repository: the method, the simulation-in-the-loop ladder, the figures from the L0–L3 runs, and the L4 fabric and multi-board boards as they stand. It is a snapshot. The design contracts in [`docs/`](../docs/) and the scale claims in [`docs/coverage_matrix.md`](../docs/coverage_matrix.md) are the source. If this prose and an owner disagree, the owner wins. Nothing here is an input to later design.

Regenerate the figures and the measured numbers with:

```bash
uv run --group writeup python writeup/scripts/render_figures.py
```

The essay is [essay.md](essay.md).
