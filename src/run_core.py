"""Core: optimize QAOA angles for the four-cube puzzle on the compact 12-qubit encoding.

Everything here runs on the local simulator. The SV1 submission happens in the
notebook, with the angles this script finds.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compact_qaoa import (classical_cost_all, hamiltonian_diagonal, hamiltonian_terms,
                          qaoa_circuit, qaoa_probabilities)
from puzzle import CUBES

SEED = 7


def optimise(cubes, p, seed=SEED, restarts=6, maxiter=400):
    """Minimise the expected cost over 2p angles; return the best angles and its P(solved)."""
    n_q = 3 * len(cubes)
    terms = hamiltonian_terms(cubes)
    diag = hamiltonian_diagonal(terms, n_q)
    cost = classical_cost_all(cubes)
    assert np.abs(diag - cost).max() < 1e-6, "Hamiltonian does not match the cost"
    wins = np.flatnonzero(cost == 0)
    rng = np.random.default_rng(seed)

    def expected(angles):
        probs = qaoa_probabilities(diag, n_q, angles[:p], angles[p:])
        return float(probs @ cost)

    best = None
    for r in range(restarts):
        x0 = np.concatenate([rng.uniform(0, 0.6, p), rng.uniform(0, np.pi / 2, p)])
        res = minimize(expected, x0, method="COBYLA", options={"maxiter": maxiter})
        probs = qaoa_probabilities(diag, n_q, res.x[:p], res.x[p:])
        record = (float(res.fun), float(probs[wins].sum()), res.x.copy())
        if best is None or record[0] < best[0]:
            best = record
    return best, wins, len(cost)


if __name__ == "__main__":
    out = {}
    print(f"four cubes, compact encoding: {3 * len(CUBES)} qubits")
    for p in (1, 2, 3, 4, 6, 8):
        t0 = time.perf_counter()
        (fun, psolved, angles), wins, total = optimise(CUBES, p)
        baseline = len(wins) / total
        print(f"p={p:>2}: expected cost {fun:6.3f}, P(solved tower) {psolved:7.3%}, "
              f"x{psolved / baseline:6.1f} over random {baseline:.3%}   ({time.perf_counter() - t0:.1f}s)")
        out[p] = {"expected_cost": fun, "p_solved": psolved, "angles": angles.tolist(),
                  "baseline": baseline}
    Path("results").mkdir(exist_ok=True)
    Path("results/core_angles.json").write_text(json.dumps(out, indent=2))
    print("saved results/core_angles.json")
