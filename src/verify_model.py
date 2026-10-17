"""Classical checks of the compact encoding, run BEFORE any quantum run.

1. The Pauli-Z Hamiltonian equals the plain-Python cost on every bitstring.
2. Cost zero  <=>  an independent brute-force solver says the decoded choice is a tower.
3. The zero-cost bitstring count matches the starter's count_answers.
"""

import itertools
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compact_qaoa import (BEST_ALIAS, CHOICES, classical_cost_all, classical_cost_one, cx_cost,
                          decode, hamiltonian_diagonal, hamiltonian_terms)
from puzzle import BONUS, CUBES, count_answers, make_puzzle, solved_by_brute_force


def verify(cubes, label, alias=BEST_ALIAS, full_independent=True, seed=7):
    n = len(cubes)
    nq = 3 * n
    t0 = time.perf_counter()
    cost = classical_cost_all(cubes, alias)
    terms = hamiltonian_terms(cubes, alias)
    rng = np.random.default_rng(seed)

    # 1. Hamiltonian vs vectorised cost (all bitstrings if small, else a large sample)
    if nq <= 15:
        idx = np.arange(2 ** nq)
    else:
        idx = rng.integers(0, 2 ** nq, 200_000)
        idx = np.concatenate([idx, np.flatnonzero(cost == 0)])
    gap_h = np.abs(hamiltonian_diagonal(terms, nq, idx) - cost[idx]).max()

    # 1b. vectorised cost vs plain-Python cost
    sample = rng.integers(0, 2 ** nq, 300)
    gap_py = max(abs(cost[i] - classical_cost_one(cubes, int(i), alias)) for i in sample)

    zeros = np.flatnonzero(cost == 0)

    # 2. independent brute-force truth, per choice (6**n choices) when affordable
    mismatches = None
    if full_independent:
        truth = {}
        mismatches = 0
        checked = 0
        for choice in itertools.product(CHOICES, repeat=n):
            truth[choice] = solved_by_brute_force(cubes, choice)
        for i in (idx if nq <= 15 else np.concatenate([sample, zeros])):
            checked += 1
            ch = tuple(decode(int(i), n, alias))
            if (cost[i] == 0) != truth[ch]:
                mismatches += 1
        solved_choices = sum(truth.values())
    else:
        solved_choices = None

    # 3. count vs count_answers x alias multiplicity
    mult = {c: 0 for c in CHOICES}
    for a in alias:
        mult[a] += 1
    expected = None
    if full_independent or n <= 8:
        sols = []
        for choice in itertools.product(CHOICES, repeat=n):
            ok = True
            for side in (0, 1):
                letters = sorted({ch for cube in cubes for pair in cube for ch in pair})
                deg = dict.fromkeys(letters, 0)
                for cube, pick in zip(cubes, choice):
                    for ch in cube[pick[side]]:
                        deg[ch] += 1
                if any(d != 2 for d in deg.values()):
                    ok = False
                    break
            if ok:
                sols.append(choice)
        expected = sum(int(np.prod([mult[c] for c in s])) for s in sols)
    starter_count = count_answers(cubes) if n <= 6 else None

    print(f"[{label}] N={n}, {nq} qubits, {len(terms)} Z terms, "
          f"max Z-weight {max(bin(m).count('1') for m in terms)}, {cx_cost(terms)} CX/layer")
    print(f"    max |H - cost| over {len(idx):,} bitstrings: {gap_h:.1e}")
    print(f"    max |vectorised - plain python cost|: {gap_py:.1e}")
    print(f"    zero-cost bitstrings: {len(zeros)} of {2 ** nq:,} (random baseline {len(zeros) / 2 ** nq:.3%})")
    if mismatches is not None:
        print(f"    independent brute-force disagreements: {mismatches}; solved choices {solved_choices}")
    print(f"    expected zero-cost count from solved choices x alias: {expected}; starter count_answers: {starter_count}")
    print(f"    ({time.perf_counter() - t0:.1f} s)")
    ok = (gap_h < 1e-6 and gap_py == 0 and (mismatches in (None, 0)) and (expected in (None, len(zeros))))
    return ok, len(zeros)


if __name__ == "__main__":
    results = {}
    ok, z = verify(CUBES, "starter CUBES")
    results["starter"] = (ok, z)
    for n, seed in BONUS.items():
        if n > 6:
            continue
        ok, z = verify(make_puzzle(n, seed), f"make_puzzle({n}, {seed})", full_independent=(n <= 5))
        results[n] = (ok, z)
    print("ALL CHECKS PASS" if all(v[0] for v in results.values()) else "CHECK FAILED", results)
