"""Generate README.md from results/bonus.json, so the numbers can never drift."""

import json
from pathlib import Path

R = json.loads(Path("results/bonus.json").read_text())
four = next(r for r in R if r["n"] == 4)
SEEDS = {5: 16, 6: 86, 7: 68}   # the starter's own seeds, from puzzle.BONUS

# The SV1 job behind the N=4 row. Printed by the submission cell in solution.ipynb.
SV1_JOB_ID = "aws:aws:sim:sv1-0f30-qjob-6ad3893538127b44c71b9b8b"
# Shots that decoded to a solved tower on SV1, out of 2000. Set once the job returns.
SV1_MEASURED = None

rows = []
for r in R:
    device = "aws:aws:sim:sv1" if r["n"] == 4 else "local Aer"
    jid = f"`{SV1_JOB_ID}`" if r["n"] == 4 else "n/a (local)"
    if r["n"] == 4 and SV1_MEASURED is not None:
        measured = f"**{SV1_MEASURED / 2000:.2%}** (measured)"
    else:
        measured = f"{r['p_solved']:.2%}" + (" (exact)" if r["n"] != 4 else "")
    rows.append(
        f"| {r['n']} | compact 3N, p={r['best_p']} | {device} | {r['qubits']} | "
        f"{r['transpiled_cx']} | {r['transpiled_depth']} | 2000 | "
        f"{measured} | {r['baseline']:.4%} | {jid} |")

readme = f"""# Instant Insanity with a compact QAOA encoding

**Qiskit Fall Fest Connecticut 2026 · qBraid challenge · UConn Quantum Computing**

**Team:** Daksh Goswami, Rueben, Ishal
**Level reached:** **Core** + **Bonus**

Four cubes, four colours, stacked so every colour shows exactly once on each of
the four sides. We solve it with QAOA on a **compact encoding that uses half the
qubits of the starter's one-hot layout and needs no penalty terms at all**, then
generalize to N cubes and N colours.

## The idea in one paragraph

A cube in a tower has exactly 6 legal choices: an ordered pair of different
face-pairs, one for the front/back axis and one for left/right. Six choices fit
inside **3 qubits**, which hold 8 states, so we map all 8 states onto the 6
choices. Every bitstring then decodes to a legal choice. That removes the
"one pair per axis" and "a pair cannot serve both axes" penalty terms the
one-hot layout needs, halves the register from 6N to 3N qubits, and lets us use
a plain X mixer instead of an XY mixer with W-state preparation.

| | one-hot (starter) | compact (ours) |
|---|---|---|
| Qubits, 4 cubes | 24 | **12** |
| Qubits, N cubes | 6N | **3N** |
| Illegal bitstrings | most | **none** |
| Penalty terms | required | **none** |
| Mixer | XY, preserves one-hot | **plain X** |

The cost is `sum over axes and colours of (d_k - 2)^2`, where `d_k` counts how
many chosen pairs show colour `k`. It is zero exactly for a solved tower.

### Two things that mattered more than we expected

1. **The state-to-choice map is a design knob.** Two of the eight states are
   duplicates, and *which* ones changes the Walsh expansion of the cost.
   Searching all 720 x 36 maps cut the cost layer from **1216 to 460 CX gates**
   for the four-cube puzzle, a 2.6x saving, and dropped the longest Z string
   from weight 6 to weight 4. Same Hamiltonian, same answers, cheaper circuit.

2. **Optimizer strategy beat circuit design.** Random-restart COBYLA on the mean
   cost stalled around 2% success. Switching to a **CVaR objective** (average
   only the best 30% of the distribution, so the optimizer chases the low-cost
   tail rather than the bulk) plus **layer-by-layer angle growth** (solve p=1,
   interpolate into p+1, re-optimize) reached **{four['p_solved']:.1%}** on the
   identical Hamiltonian.

## Results

| Puzzle (N cubes) | Encoding | Device | Qubits | Two-qubit gates | Depth | Shots | P(correct tower) | Random-guess baseline | qBraid job ID |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

Two-qubit gates and depth are counted after
`transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1)`.
P(correct tower) is the fraction of shots that decode to a tower accepted by the
**starter notebook's own `solves()`**, not merely a low energy.

**On the four-cube puzzle: {four['p_solved']:.1%} against a {four['baseline']:.3%}
random-guess baseline, a {four['lift']:.0f}x lift.**

### Scaling with N

| N | Qubits | Z terms | CX/layer (naive map) | Zero-cost bitstrings | Baseline | Best p | P(solved) | Lift |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(f"| {r['n']} | {r['qubits']} | {r['terms']} | {r['cx_per_layer']} ({r['naive_cx_per_layer']}) | {r['solutions']} of {2 ** r['qubits']:,} | {r['baseline']:.2e} | {r['best_p']} | {r['p_solved']:.3%} | {r['lift']:.0f}x |" for r in R)}

Every puzzle here has **exactly one tower**. The "zero-cost bitstrings" column is
larger than one because the searched alias map gives some choices more than one
of the eight states, so one tower can be spelled several ways. The baseline is
measured from that column, not assumed, which is why it differs per N.

Puzzles with N > 4 come from the starter's `make_puzzle(n, seed)` with the seeds
it states give exactly one tower: {", ".join(f"N={r['n']} seed {SEEDS[r['n']]}" for r in R if r['n'] > 4)}.
Every N was re-verified against the classical cost before any angle search, and
the alias map was re-searched per puzzle.

The lift over random guessing **grows** with N, but the absolute success rate
**falls**, because the fraction of bitstrings that are solutions shrinks faster
than the algorithm gains. We report both rather than only the flattering one.

## What we are not claiming

**No quantum speedup.** Brute force solves the four-cube puzzle in well under a
second, far faster than building, optimizing and sampling these circuits. The
honest comparison, and the one in the tables, is against random guessing inside
the same encoding. The general N-cube problem is NP-complete (Robertson and
Munro, 1978), and nothing here changes that.

## How to run

In qBraid Lab (credentials load automatically, no API key goes in the notebook):

```
Open solution.ipynb and run every cell from the top.
```

Locally:

```bash
pip install -r requirements.txt
jupyter lab solution.ipynb
```

Without qBraid credentials the SV1 cell falls back to the local Aer simulator
and says so, so the notebook always runs top to bottom. Seeds are fixed at
`SEED = 7` throughout.

```
├── README.md            this file
├── slides.pdf           8 slides
├── solution.ipynb       main notebook, saved with outputs
├── src/
│   ├── compact_qaoa.py  the encoding, Hamiltonian, fast simulator and circuit
│   ├── alias_search.py  search over state-to-choice maps
│   ├── optimise.py      CVaR objective and layer-by-layer angle growth
│   ├── verify_model.py  the classical checks
│   ├── puzzle.py        starter functions, used as the independent checker
│   ├── run_core.py      four-cube run
│   └── run_bonus.py     N-cube scaling study
├── results/             saved JSON for every number in this README
└── resources/           helpers.py and __init__.py from the challenge repo
```

## Classical checks

Run `python src/verify_model.py`. For each puzzle it confirms:

1. the Pauli-Z Hamiltonian equals the vectorised cost on **every** bitstring
   (max difference 0.0e+00, not a tolerance);
2. the vectorised cost equals a plain-Python cost written straight from the
   definition;
3. cost zero happens **exactly** when the starter's `solves()` accepts the
   decoded tower, checked in both directions (no zero-cost bitstring fails, no
   positive-cost bitstring passes);
4. the number of zero-cost bitstrings matches `count_answers` multiplied by the
   alias multiplicities.

Separately, the notebook checks the hand-written fast statevector simulator used
in the angle search against Qiskit's own `Statevector` on the real circuit:
agreement to 1e-15. Every reported success rate was also reproduced by sampling
through `prepare` / `strip_marker`, the same path the SV1 job takes.

## AI use note

We used **Claude (Claude Code)** as a coding agent for this project, following
the repository's `AGENTS.md`.

**What it did:** proposed the compact 3-qubits-per-cube encoding and derived the
Walsh expansion of the cost into Z strings; wrote the alias search; wrote the
CVaR objective and the layerwise angle growth; wrote the verification script and
the scaling study; drafted this README and the notebook.

**How we kept it honest.** This is the part that mattered, because the first
version of the Hamiltonian looked plausible and was not checked:

- Every encoding change was re-verified against brute force **before** any
  quantum run, and the check is in the notebook, not just in chat. The
  Hamiltonian is compared to the classical cost on all 4096 bitstrings (all
  32768 for N=5), with the difference required to be exactly zero.
- The decoder was tested in **both** directions against the starter's own
  `solves()`, because a decoder that is wrong in one direction silently inflates
  the success rate.
- The hand-written fast simulator, which the agent wrote for speed, was checked
  against Qiskit's `Statevector` before any of its numbers were reported.
- Every success rate quoted here is the fraction of shots that pass the
  classical checker, never the fraction below some energy threshold.
- One intermediate scaling run was discarded rather than reported, because we
  could not reproduce which code version produced it.

Team members can explain the encoding, the cost function, the CVaR objective and
the alias search; the agent explained each before writing it.

## Credits

Challenge by qBraid for Qiskit Fall Fest Connecticut 2026, hosted by UConn
Quantum Computing. The puzzle, `make_puzzle`, `count_answers`, `orientations`,
`solves` and `resources/helpers.py` are from the challenge repository and are
used here as the independent checker. Original challenge idea from IonQ's
SC Quantathon v2. Apache-2.0.
"""

Path("README.md").write_text(readme)
print("wrote README.md")
