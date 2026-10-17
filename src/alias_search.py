"""Search the 3-qubit -> 6-choice map for the cheapest Hamiltonian.

Eight bitstrings must cover six legal choices, so two states are duplicates. WHICH
state means which choice is free, and it changes the Walsh expansion of the cost:
a map that lines the choices up with the cube structure needs fewer and lower-weight
Z strings, which means fewer CX gates. Every map is still exact - we re-verify.
"""

import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compact_qaoa import CHOICES


def terms_for_alias(cubes, alias):
    """Hamiltonian term dict for a given 8-entry alias map (list of (fb, lr))."""
    letters = sorted({ch for cube in cubes for pair in cube for ch in pair})
    n = len(cubes)
    polys = {}
    for side in (0, 1):
        for k, colour in enumerate(letters):
            for c, cube in enumerate(cubes):
                f = np.array([cube[alias[i][side]].count(colour) for i in range(8)], float)
                poly = {}
                for mask in range(8):
                    w = sum(f[i] * (-1) ** bin(i & mask).count("1") for i in range(8)) / 8
                    if abs(w) > 1e-12:
                        poly[mask] = float(w)
                polys[side, k, c] = poly
    H = {}
    for side in (0, 1):
        for k in range(len(letters)):
            P = {0: -2.0}
            for c in range(n):
                for m, w in polys[side, k, c].items():
                    g = m << (3 * c)
                    P[g] = P.get(g, 0.0) + w
            for a, wa in P.items():
                for b, wb in P.items():
                    g = a ^ b
                    H[g] = H.get(g, 0.0) + wa * wb
    return {m: w for m, w in H.items() if abs(w) > 1e-9}


def cx_cost(terms):
    """CX gates one cost layer needs: a weight-w Z string costs 2(w-1) CX."""
    return sum(2 * (bin(m).count("1") - 1) for m in terms if bin(m).count("1") >= 2)


def search(cubes, verbose=True):
    """Every ordering of the 6 choices, times every choice of the 2 duplicated states."""
    best = None
    results = []
    for perm in itertools.permutations(range(6)):
        base = [CHOICES[i] for i in perm]
        for dup in itertools.product(range(6), repeat=2):
            alias = base + [CHOICES[perm[dup[0]]], CHOICES[perm[dup[1]]]]
            t = terms_for_alias(cubes, alias)
            score = (cx_cost(t), len(t))
            results.append((score, perm, dup))
            if best is None or score < best[0]:
                best = (score, alias, t)
                if verbose:
                    print(f"  new best: {score[0]} CX/layer, {score[1]} terms, "
                          f"perm {perm}, dup {dup}")
    return best, results
