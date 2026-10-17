# Instant Insanity on 12 qubits

**Qiskit Fall Fest Connecticut 2026 · qBraid challenge · UConn Quantum Computing**

**Team:** Daksh Goswami, Rueben, Ishal
**Level reached:** **Core** + **Bonus**

## The puzzle

You get four cubes. Every face is painted one of four colours. Stack them so that
each of the four sides of the tower shows all four colours exactly once.

There are 331,776 ways to stack them. Exactly one works.

## What we did

We solved it with QAOA, using an encoding that needs **half the qubits** of the
one in the starter notebook, and **no penalty terms at all**.

### The idea

In a tower, a cube puts one pair of opposite faces on the front/back axis, and a
*different* pair on the left/right axis. So a cube only ever has
**3 x 2 = 6 legal choices**.

Six choices fit inside **3 qubits**, which hold 8 states. We map all 8 states
onto the 6 choices, so two states are duplicates. The payoff:

**every bitstring now decodes to a legal cube orientation.**

That matters more than it sounds. The starter notebook uses 6 qubits per cube in
a "one-hot" layout, where most bitstrings are nonsense (two pairs on one axis, or
the same pair on both). It has to add penalty terms to the cost to push the
circuit away from them, and a special XY mixer to stay in the legal subspace.
We get those rules for free, just from how we labelled things.

| | one-hot (starter) | compact (ours) |
|---|---|---|
| Qubits, 4 cubes | 24 | **12** |
| Qubits, N cubes | 6N | **3N** |
| Illegal bitstrings | most of them | **none** |
| Penalty terms | required | **none** |
| Mixer | XY + W-state prep | **plain X** |

### The cost function

For each axis and each colour `k`, count how many chosen pairs show that colour.
Call it `d_k`. A solved tower shows every colour once per side, so twice per
axis. That means `d_k = 2` for every colour. So:

```
cost = sum over both axes, over all colours, of (d_k - 2)^2
```

It is a sum of squares, so it can never go below zero, and it hits zero
**only** when every `d_k` is exactly 2 — which is exactly a solved tower.
Nothing to tune, no weights to pick.

### Two things that surprised us

**1. The labelling is a free speedup.**
Two of the eight states are duplicates, and *which* two is our choice. Each
cube's colour count becomes a polynomial in that cube's three Z operators, so
relabelling changes which Z strings end up in the Hamiltonian. We tried all
720 x 36 labellings and scored each by how many CX gates one cost layer needs:

**1216 CX -> 460 CX**, a 2.6x saving, with the longest Z string dropping from
6 qubits to 4. Same Hamiltonian, same answers, cheaper circuit. It is ordinary
classical preprocessing and runs in about 40 seconds.

**2. The classical optimiser mattered more than the circuit.**
Our first approach — COBYLA from random starting angles, minimising the average
cost — tops out at **4.2%** (at p=6) and then gets *worse* with more layers
(3.8% at p=8). Run `python src/run_core.py` to see that for yourself.

Two changes fixed it, on the *identical* Hamiltonian and circuit:

- **CVaR instead of the average.** Minimising the average cost is not the same as
  maximising the chance of a solved tower, because the average is dominated by
  the huge number of bad bitstrings. CVaR scores only the best 30% of the
  distribution, so the optimiser chases the low-cost tail where answers live.
- **Growing layer by layer.** Optimising all 2p angles from a random start is
  hard. Instead solve p=1, stretch those angles into a p=2 schedule, re-optimise,
  and repeat. Each layer starts from a good guess.

Result: **44.6%** at p=12, and it keeps improving with p instead
of stalling.

## Results

| Puzzle (N cubes) | Encoding | Device | Qubits | Two-qubit gates | Depth | Shots | P(correct tower) | Random-guess baseline | qBraid job ID |
|---|---|---|---|---|---|---|---|---|---|
| 4 | compact 3N, p=12 | aws:aws:sim:sv1 | 12 | 4704 | 4361 | 2000 | **44.20%** (measured) | 0.1465% | `aws:aws:sim:sv1-0f30-qjob-6ad3893538127b44c71b9b8b` |
| 5 | compact 3N, p=10 | local Aer | 15 | 7620 | 6538 | 2000 | 13.37% (exact) | 0.0366% | n/a (local) |
| 6 | compact 3N, p=10 | local Aer | 18 | 10780 | 7803 | 2000 | 8.43% (exact) | 0.0069% | n/a (local) |
| 7 | compact 3N, p=8 | local Aer | 21 | 11440 | 9366 | 2000 | 1.04% (exact) | 0.0002% | n/a (local) |

Two-qubit gates and depth are counted after
`transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1)`.
P(correct tower) is the fraction of shots that decode to a tower the **starter
notebook's own `solves()`** accepts — not just a low energy.

**On AWS SV1: 884 of 2000 shots = 44.20%, against a
0.146% random-guess baseline. A 302x lift.**

The exact simulation predicted 44.62% for that circuit. We measured
44.20%. Those are 0.4 standard errors apart
(one standard error is 1.11% at 2000 shots), so the circuit that really
ran on SV1 — transpiled, with a marker qubit, decoded from counts — behaves the
way our model says it should. That agreement checks the whole pipeline, not just
the maths.

### How it scales

| N | Qubits | CX/layer | Zero-cost bitstrings | Baseline | Best p | P(solved) | Lift |
|---|---|---|---|---|---|---|---|
| 4 | 12 | 460 | 6 of 4,096 | 1.46e-03 | 12 | 44.62% | 305x |
| 5 | 15 | 890 | 12 of 32,768 | 3.66e-04 | 10 | 13.37% | 365x |
| 6 | 18 | 1264 | 18 of 262,144 | 6.87e-05 | 10 | 8.43% | 1227x |
| 7 | 21 | 1686 | 4 of 2,097,152 | 1.91e-06 | 8 | 1.04% | 5457x |

Every one of these puzzles has **exactly one tower**. The "zero-cost bitstrings"
count is bigger than one because our labelling gives some choices more than one
of the eight states, so the same tower can be spelled a few different ways. We
measure the baseline from that count rather than assuming it, which is why it
differs for each N.

The puzzles for N > 4 come from the starter's `make_puzzle(n, seed)`, using the
seeds it says give exactly one tower: N=5 seed 16, N=6 seed 86, N=7 seed 68.

**The lift over random guessing grows with N. The absolute success rate falls.**
Both are true: the fraction of bitstrings that are answers shrinks faster than
the algorithm gains. We report both, not just the flattering one.

## What we are NOT claiming

**This is not faster than classical.** Brute force solves the four-cube puzzle in
well under a second — far quicker than building, optimising and sampling these
circuits. The fair comparison, and the one in every table above, is against
random guessing inside our own encoding. The general N-cube problem is
NP-complete (Robertson and Munro, 1978) and nothing here changes that.

## How we know it is right

Run `python src/verify_model.py`. For every puzzle it checks:

1. **The Hamiltonian equals the classical cost on every single bitstring.** All
   4,096 of them for N=4. The difference is exactly `0.0e+00` — not "within a
   tolerance".
2. **Two separate implementations of the cost agree** — a fast vectorised one and
   a plain-Python one written straight from the definition.
3. **The decoder is correct in both directions.** No zero-cost bitstring fails
   the starter's `solves()`, and no positive-cost bitstring passes it. Checking
   only one direction would let us silently inflate our success rate.
4. **The zero-cost count matches `count_answers`**, adjusted for the duplicated
   states.

Separately, the notebook checks the fast statevector simulator we optimise with
against Qiskit's own `Statevector` on the real circuit: they agree to 1e-15. We
did that *before* trusting any number it produced.

A low energy is not proof. Every tower we report was rebuilt and handed to the
starter notebook's checker.

## How to run it

In qBraid Lab, credentials load automatically, so no API key goes anywhere:

```
Open solution.ipynb and run every cell from the top.
```

On your own machine:

```bash
pip install -r requirements.txt
jupyter lab solution.ipynb
```

Without qBraid credentials the SV1 cell falls back to the local Aer simulator and
says so, so the notebook always runs end to end. All random seeds are fixed at
`SEED = 7`. `build_all.sh` regenerates every file in this repo from `src/`.

```
README.md          this file
slides.pdf         8 slides
solution.ipynb     the notebook, saved with outputs
src/               compact_qaoa.py  the encoding, Hamiltonian, simulator, circuit
                   alias_search.py  the search over labellings
                   optimise.py      CVaR and layer-by-layer growth
                   verify_model.py  the classical checks
                   puzzle.py        the starter's functions, used as our checker
                   run_core.py      the baseline we abandoned
                   run_bonus.py     the N = 4..7 runs
resources/         helpers.py and __init__.py from the challenge repo
results/           every number in this README, as JSON
figures/           the plots and diagrams
```

## AI use

We used **Claude (Claude Code)** as a coding agent, following the repository's
`AGENTS.md`.

**What it did:** suggested the compact 3-qubits-per-cube encoding and worked out
how to turn the cost into Z operators; wrote the labelling search, the CVaR
objective, the layer-by-layer growth, the verification script and the scaling
study; drafted this README and the notebook.

**How we kept it honest.** This is the part that mattered:

- Every change to the encoding was checked against brute force **before** any
  quantum run, and the check lives in the notebook, not just in a chat window.
- The decoder was tested in **both** directions, because a decoder that is wrong
  one way quietly inflates the success rate.
- The fast simulator the agent wrote for speed was checked against Qiskit before
  we reported anything from it.
- We caught the agent reporting an old number: an earlier draft said the baseline
  optimiser "stalled around 2%". Re-running the code we actually shipped gave
  **4.2%**. We corrected it. The number in this README is the one
  `src/run_core.py` prints today.
- One intermediate scaling run was **thrown away** instead of reported, because
  we could not work out which version of the code produced it.

## Credits

Challenge by qBraid for Qiskit Fall Fest Connecticut 2026, hosted by UConn
Quantum Computing. The puzzle, `make_puzzle`, `count_answers`, `orientations`,
`solves` and `resources/helpers.py` come from the challenge repository and are
used here as our independent checker. Original challenge idea from IonQ's
SC Quantathon v2. Apache-2.0.
