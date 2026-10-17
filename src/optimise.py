"""Better QAOA angle finding: layer-by-layer growth (INTERP) and a CVaR objective.

Why: minimising the MEAN cost is not the same as maximising P(cost = 0). The mean
is dragged around by the bulk of bad bitstrings. CVaR_alpha averages only the best
alpha-fraction of the distribution, so it pushes weight into the low-cost tail,
which is where the answers are. Layer-by-layer growth gives layer p+1 a good
starting point from layer p, instead of restarting the search blindly.
"""

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compact_qaoa import qaoa_probabilities


def cvar(probs, cost_sorted, order, alpha):
    """CVaR_alpha: the mean cost of the best alpha-fraction of the distribution."""
    p = probs[order]
    c = np.cumsum(p)
    k = int(np.searchsorted(c, alpha) + 1)
    k = min(k, len(p))
    w = p[:k].copy()
    excess = w.sum() - alpha
    if excess > 0:
        w[k - 1] -= excess
    return float(w @ cost_sorted[:k] / max(w.sum(), 1e-15))


def make_objective(diag, cost, n_q, alpha):
    order = np.argsort(cost)
    cost_sorted = cost[order]

    def f(angles):
        p = len(angles) // 2
        probs = qaoa_probabilities(diag, n_q, angles[:p], angles[p:])
        if alpha >= 1.0:
            return float(probs @ cost)
        return cvar(probs, cost_sorted, order, alpha)

    return f


def grow(diag, cost, n_q, p_max, alpha=0.05, seed=7, restarts=8, maxiter=300, verbose=True):
    """Layer-by-layer: optimise p=1 from several starts, then extend to p+1 by
    interpolating the found angles and re-optimising."""
    rng = np.random.default_rng(seed)
    wins = np.flatnonzero(cost == 0)
    baseline = len(wins) / len(cost)
    obj = make_objective(diag, cost, n_q, alpha)

    best_x, trace = None, []
    for _ in range(restarts):
        x0 = np.concatenate([rng.uniform(0, 0.8, 1), rng.uniform(0, np.pi / 2, 1)])
        res = minimize(obj, x0, method="COBYLA", options={"maxiter": maxiter})
        if best_x is None or res.fun < best_fun:
            best_x, best_fun = res.x.copy(), res.fun

    def record(p, x):
        probs = qaoa_probabilities(diag, n_q, x[:p], x[p:])
        entry = {"p": p, "objective": float(obj(x)), "mean_cost": float(probs @ cost),
                 "p_solved": float(probs[wins].sum()), "baseline": baseline,
                 "angles": x.tolist()}
        trace.append(entry)
        if verbose:
            print(f"  p={p:>2}: CVaR {entry['objective']:6.3f}  mean {entry['mean_cost']:6.3f}  "
                  f"P(solved) {entry['p_solved']:7.3%}  x{entry['p_solved'] / baseline:6.1f}")
        return entry

    record(1, best_x)
    x = best_x
    for p in range(2, p_max + 1):
        g, b = x[:p - 1], x[p - 1:]
        # INTERP-style extension: linear ramp keeps the schedule shape, then re-optimise
        g_new = np.interp(np.linspace(0, 1, p), np.linspace(0, 1, p - 1), g)
        b_new = np.interp(np.linspace(0, 1, p), np.linspace(0, 1, p - 1), b)
        x0 = np.concatenate([g_new, b_new])
        # flat evaluation budget per layer: scaling it with p makes big N unaffordable
        res = minimize(obj, x0, method="COBYLA", options={"maxiter": maxiter})
        # keep a perturbed retry if it did not help
        if res.fun > obj(x0):
            res2 = minimize(obj, x0 + rng.normal(0, 0.05, len(x0)), method="COBYLA",
                            options={"maxiter": maxiter})
            res = res2 if res2.fun < res.fun else res
        x = res.x
        record(p, x)
    return trace
