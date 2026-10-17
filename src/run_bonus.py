"""Bonus: how the compact encoding scales with N cubes and N colours.

For each N we:
  1. build the puzzle with the starter's make_puzzle(n, seed),
  2. verify the Hamiltonian equals the classical cost on every bitstring,
  3. search the alias map for the cheapest cost layer,
  4. grow QAOA angles layer by layer with a CVaR objective,
  5. record qubits, Z terms, CX per layer, transpiled depth, P(solved) and the
     random-guess baseline.

N=8 is 24 qubits: 16.8M amplitudes, which is the practical ceiling for an
exact statevector search on a laptop-sized machine.
"""

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alias_search import terms_for_alias
from compact_qaoa import (BEST_ALIAS, CHOICES, classical_cost_all, classical_cost_one, cx_cost,
                          hamiltonian_diagonal, hamiltonian_terms, qaoa_circuit)
from optimise import grow
from puzzle import BONUS, CUBES, make_puzzle

SEED = 7


def cheapest_alias(cubes, budget=None):
    """Search choice orderings for the cheapest cost layer. Returns (alias, terms)."""
    best = None
    perms = list(itertools.permutations(range(6)))
    rng = np.random.default_rng(SEED)
    if budget and len(perms) * 36 > budget:
        perms = [perms[i] for i in rng.choice(len(perms), size=max(1, budget // 36), replace=False)]
    for perm in perms:
        base = [CHOICES[i] for i in perm]
        for dup in itertools.product(range(6), repeat=2):
            alias = base + [CHOICES[perm[dup[0]]], CHOICES[perm[dup[1]]]]
            t = terms_for_alias(cubes, alias)
            score = (cx_cost(t), len(t))
            if best is None or score < best[0]:
                best = (score, alias, t)
    return best[1], best[2]


def study(n, cubes, p_max, alpha=0.3, do_alias_search=True, seed=SEED, maxiter=250):
    nq = 3 * n
    t0 = time.perf_counter()

    alias, terms = (cheapest_alias(cubes) if do_alias_search
                    else (BEST_ALIAS, hamiltonian_terms(cubes, BEST_ALIAS)))
    naive_cx = cx_cost(hamiltonian_terms(cubes, None if False else __import__(
        "compact_qaoa").NAIVE_ALIAS))

    cost = classical_cost_all(cubes, alias).astype(float)
    diag = hamiltonian_diagonal(terms, nq)
    gap = np.abs(diag - cost).max()
    rng = np.random.default_rng(seed)
    sample = rng.integers(0, 2 ** nq, 200)
    gap_py = max(abs(cost[i] - classical_cost_one(cubes, int(i), alias)) for i in sample)
    wins = np.flatnonzero(cost == 0)
    baseline = len(wins) / len(cost)
    assert gap < 1e-6 and gap_py == 0, f"model check failed for N={n}"

    print(f"\nN={n}: {nq} qubits, {len(terms)} Z terms, {cx_cost(terms)} CX/layer "
          f"(naive alias {naive_cx}), {len(wins)} solutions of {len(cost):,}, "
          f"baseline {baseline:.2e}, |H-cost|={gap:.0e}")
    trace = grow(diag, cost, nq, p_max=p_max, alpha=alpha, seed=seed,
                 restarts=8, maxiter=maxiter)

    top = max(trace, key=lambda e: e["p_solved"])
    qc = qaoa_circuit(terms, nq, top["angles"][:top["p"]], top["angles"][top["p"]:])
    from qiskit import transpile
    tq = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1)
    out = {"n": n, "qubits": nq, "terms": len(terms), "cx_per_layer": cx_cost(terms),
           "naive_cx_per_layer": naive_cx, "solutions": int(len(wins)), "baseline": baseline,
           "best_p": top["p"], "p_solved": top["p_solved"],
           "lift": top["p_solved"] / baseline, "alias": alias,
           "angles": top["angles"], "transpiled_cx": tq.count_ops().get("cx", 0),
           "transpiled_depth": tq.depth(), "trace": [
               {k: v for k, v in e.items() if k != "angles"} for e in trace],
           "seconds": time.perf_counter() - t0}
    print(f"  best p={top['p']}: P(solved) {top['p_solved']:.3%}, lift x{out['lift']:.0f}, "
          f"transpiled {out['transpiled_cx']} cx depth {out['transpiled_depth']} "
          f"({out['seconds']:.0f}s)")
    return out


if __name__ == "__main__":
    Path("results").mkdir(exist_ok=True)
    out = Path("results/bonus.json")

    # (N, cubes, p_max, optimiser budget per layer). The budget is flat, not p-scaled:
    # each objective call costs O(p * 3N * 2^3N), so a p-scaled budget is quadratic in p
    # and unaffordable past N=6.
    plan = [(4, CUBES, 12, 600),
            (5, make_puzzle(5, BONUS[5]), 10, 400),
            (6, make_puzzle(6, BONUS[6]), 10, 250),
            (7, make_puzzle(7, BONUS[7]), 8, 120)]

    results = []
    for n, cubes, p_max, budget in plan:
        results.append(study(n, cubes, p_max=p_max, maxiter=budget))
        out.write_text(json.dumps(results, indent=2))   # save after every N
        print(f"  -> saved {out} with {len(results)} puzzles")
    print("\ndone")
