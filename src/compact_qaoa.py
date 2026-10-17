"""Compact (3 qubits per cube) QAOA for Instant Insanity with N cubes and N colours.

Encoding
--------
A cube is three opposite-face pairs. In a tower each cube puts one pair on the
front/back axis and a DIFFERENT pair on the left/right axis, so it has
3 * 2 = 6 legal choices. Six choices fit in 3 qubits, which hold 8 states.

We map all 8 states onto the 6 legal choices (two states are duplicates). That
is the point of the encoding: EVERY bitstring decodes to a legal choice, so the
"exactly one pair per axis" and "a pair cannot serve both axes" rules are built
into the encoding and need no penalty terms. Compare the starter's one-hot
layout: 6 qubits per cube plus penalties to keep the state legal.

  one-hot : 6N qubits, 24 for four cubes, most bitstrings illegal
  compact : 3N qubits, 12 for four cubes, every bitstring legal

Qubit 3*c + j is bit j of cube c's state; Qiskit counts keys put qubit 0 last.

Which state maps to which choice is a free choice and it changes the cost's
Walsh expansion, so `alias_search.py` picks the map with the fewest CX gates.
BEST_ALIAS below is that map for the starter's four cubes (460 CX per cost
layer, down from 1216 for the naive map). Every map is exact; this one is cheap.

Cost
----
For each axis (front/back, left/right) and each colour k, let d_k be how many
chosen pairs show colour k. A solved tower has d_k = 2 everywhere, so

    cost = sum over axes, colours of (d_k - 2)^2

is zero exactly for a solved tower and positive otherwise. A cube's contribution
to d_k is a function of its own 3 qubits, so in Z operators the cost has strings
on at most 6 qubits (two cubes at a time).
"""

import itertools

import numpy as np

CHOICES = list(itertools.permutations(range(3), 2))  # (front/back pair, left/right pair)

# naive map: the six choices in order, then two spares folded onto the first two
NAIVE_ALIAS = CHOICES + [CHOICES[0], CHOICES[1]]

# cheapest map found by alias_search.py for the starter's four cubes
BEST_ALIAS = [(0, 2), (1, 2), (0, 1), (2, 1), (2, 0), (1, 0), (2, 1), (2, 1)]


def letters_of(cubes):
    return sorted({ch for cube in cubes for pair in cube for ch in pair})


def decode(bits_int, n_cubes, alias=BEST_ALIAS):
    """Bitstring integer -> list of (front/back pair, left/right pair) per cube."""
    return [alias[(bits_int >> (3 * c)) & 7] for c in range(n_cubes)]


def _tables(cubes, alias):
    """T[side][colour][cube][state] = colour count that cube adds on that axis."""
    letters = letters_of(cubes)
    T = np.zeros((2, len(letters), len(cubes), 8), dtype=np.int64)
    for c, cube in enumerate(cubes):
        for idx in range(8):
            for side in (0, 1):
                pair = cube[alias[idx][side]]
                for k, colour in enumerate(letters):
                    T[side, k, c, idx] = pair.count(colour)
    return T


def classical_cost_all(cubes, alias=BEST_ALIAS):
    """Cost of every one of the 8**N bitstrings, indexed by the bitstring integer."""
    n = len(cubes)
    T = _tables(cubes, alias)
    idx = np.arange(8 ** n, dtype=np.int64)
    cost = np.zeros(8 ** n, dtype=np.int32)
    for side in (0, 1):
        for k in range(T.shape[1]):
            d = np.zeros(8 ** n, dtype=np.int32)
            for c in range(n):
                d += T[side, k, c][(idx >> (3 * c)) & 7].astype(np.int32)
            cost += (d - 2) ** 2
    return cost


def classical_cost_one(cubes, bits_int, alias=BEST_ALIAS):
    """Plain-Python cost of one bitstring: the reference the fast paths are checked against."""
    letters = letters_of(cubes)
    choice = decode(bits_int, len(cubes), alias)
    total = 0
    for side in (0, 1):
        for colour in letters:
            d = sum(cubes[c][choice[c][side]].count(colour) for c in range(len(cubes)))
            total += (d - 2) ** 2
    return total


# ------------------------------------------------------------------ Hamiltonian

def hamiltonian_terms(cubes, alias=BEST_ALIAS):
    """Cost Hamiltonian as {mask: coeff}; bit q of mask means a Z on qubit q.

    Each cube's colour count is turned into a polynomial in its own three Z's by a
    Walsh-Hadamard transform of its 8 values. Squaring the degree sum multiplies
    those polynomials, and a product of Z strings is the Z string on the XOR of
    their masks.
    """
    T = _tables(cubes, alias)
    n = len(cubes)
    polys = {}
    for side in (0, 1):
        for k in range(T.shape[1]):
            for c in range(n):
                f = T[side, k, c]
                poly = {}
                for mask in range(8):
                    w = sum(f[i] * (-1) ** bin(i & mask).count("1") for i in range(8)) / 8
                    if abs(w) > 1e-12:
                        poly[mask] = float(w)
                polys[side, k, c] = poly
    H = {}
    for side in (0, 1):
        for k in range(T.shape[1]):
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


def hamiltonian_diagonal(terms, n_qubits, indices=None):
    """Evaluate the Z-string Hamiltonian on bitstring integers (all of them by default)."""
    idx = (np.arange(2 ** n_qubits, dtype=np.int64) if indices is None
           else np.asarray(indices, dtype=np.int64))
    out = np.zeros(len(idx))
    for mask, w in terms.items():
        v = idx & mask
        parity = np.zeros(len(idx), dtype=np.int64)
        while v.any():
            parity ^= v & 1
            v = v >> 1
        out += w * (1 - 2 * parity)
    return out


def cx_cost(terms):
    """CX gates one cost layer needs: a weight-w Z string costs 2(w-1) CX."""
    return sum(2 * (bin(m).count("1") - 1) for m in terms if bin(m).count("1") >= 2)


# ------------------------------------------------------------------ fast exact simulator

def _apply_rx_all(state, n, beta):
    """exp(-i beta X) on every qubit, in place."""
    c, s = np.cos(beta), -1j * np.sin(beta)
    for j in range(n):
        v = state.reshape(-1, 2, 2 ** j)
        a, b = v[:, 0, :].copy(), v[:, 1, :]
        v[:, 0, :] = c * a + s * b
        v[:, 1, :] = s * a + c * b
    return state


def qaoa_probabilities(diag, n_qubits, gammas, betas):
    """p-layer QAOA output probabilities for a diagonal cost. Exact, no sampling."""
    state = np.full(2 ** n_qubits, 2 ** (-n_qubits / 2), dtype=np.complex128)
    for g, b in zip(gammas, betas):
        state *= np.exp(-1j * g * diag)
        _apply_rx_all(state, n_qubits, b)
    return np.abs(state) ** 2


# ------------------------------------------------------------------ circuit

def multi_z_rotation(qc, qubits, angle):
    """exp(-i angle/2 * Z..Z) on the given qubits, with a CX ladder."""
    if len(qubits) == 1:
        qc.rz(angle, qubits[0])
        return
    for a, b in zip(qubits[:-1], qubits[1:]):
        qc.cx(a, b)
    qc.rz(angle, qubits[-1])
    for a, b in reversed(list(zip(qubits[:-1], qubits[1:]))):
        qc.cx(a, b)


def qaoa_circuit(terms, n_qubits, gammas, betas):
    """QAOA: |+>^n, then per layer exp(-i gamma H) and exp(-i beta sum_q X_q).

    The plain X mixer is the right one here: every bitstring is a legal choice,
    so the mixer never has to avoid an illegal subspace.
    """
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))
    # longer Z strings first: the transpiler then cancels more of the CX ladders
    ordered = sorted((m for m in terms if m), key=lambda m: -bin(m).count("1"))
    for g, b in zip(gammas, betas):
        for mask in ordered:
            qubits = [q for q in range(n_qubits) if (mask >> q) & 1]
            multi_z_rotation(qc, qubits, 2 * g * terms[mask])
        qc.rx(2 * b, range(n_qubits))
    return qc
