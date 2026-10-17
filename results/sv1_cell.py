# Instant Insanity - compact 12-qubit QAOA  ->  AWS SV1 via qBraid
# Self-contained: no local imports needed.
import itertools, numpy as np
from qiskit import QuantumCircuit, transpile
from qbraid.runtime import QbraidProvider

CUBES = [["GR","BR","GY"], ["GY","RB","BY"], ["BR","RG","RY"], ["YR","RG","BG"]]
COLOURS = "RGBY"
CHOICES = list(itertools.permutations(range(3), 2))
ALIAS = [(0,2),(1,2),(0,1),(2,1),(2,0),(1,0),(2,1),(2,1)]   # searched map: 460 CX/layer
P = 12
ANGLES = np.array([-0.1937739959, -0.2696178406, -0.325678672, -0.3687656048, -0.4030719141, -0.4310076127, -0.4540320291, -0.4734863843, -0.4914263695, -0.5114547239, -0.5395538113, -0.5849181984, 0.4309992806, 0.3883089894, 0.3538166424, 0.3266742343, 0.3054552388, 0.2883614225, 0.2734296589, 0.2587387422, 0.2426162019, 0.2238451161, 0.2018709261, 0.1770082501])

def hamiltonian_terms(cubes, alias=ALIAS):
    """Cost  = sum over axes, colours of (d_k - 2)^2,  as {Z-mask: coeff}."""
    letters = sorted({c for cu in cubes for pr in cu for c in pr})
    n = len(cubes)
    T = np.zeros((2, len(letters), n, 8), dtype=int)
    for c, cube in enumerate(cubes):
        for i in range(8):
            for side in (0, 1):
                for k, col in enumerate(letters):
                    T[side, k, c, i] = cube[alias[i][side]].count(col)
    H = {}
    for side in (0, 1):
        for k in range(len(letters)):
            Pg = {0: -2.0}
            for c in range(n):
                f = T[side, k, c]
                for m in range(8):
                    w = sum(f[i]*(-1)**bin(i & m).count("1") for i in range(8))/8
                    if abs(w) > 1e-12:
                        g = m << (3*c); Pg[g] = Pg.get(g, 0.0) + w
            for a, wa in Pg.items():
                for b, wb in Pg.items():
                    H[a ^ b] = H.get(a ^ b, 0.0) + wa*wb
    return {m: w for m, w in H.items() if abs(w) > 1e-9}

def multi_z(qc, qs, ang):
    if len(qs) == 1: qc.rz(ang, qs[0]); return
    for a, b in zip(qs[:-1], qs[1:]): qc.cx(a, b)
    qc.rz(ang, qs[-1])
    for a, b in reversed(list(zip(qs[:-1], qs[1:]))): qc.cx(a, b)

def qaoa_circuit(terms, nq, gammas, betas):
    qc = QuantumCircuit(nq); qc.h(range(nq))
    order = sorted((m for m in terms if m), key=lambda m: -bin(m).count("1"))
    for g, b in zip(gammas, betas):
        for m in order:
            multi_z(qc, [q for q in range(nq) if (m >> q) & 1], 2*g*terms[m])
        qc.rx(2*b, range(nq))
    return qc

# ---- independent classical checker: rebuild the tower and test all four sides
def orientations(cube):
    views = []
    for a, b in itertools.permutations(range(3), 2):
        for fa in (0, 1):
            for fb in (0, 1):
                p, q = cube[a], cube[b]
                views.append((p[fa], p[1-fa], q[fb], q[1-fb]))
    return views

def solves(tower):
    return all(len({v[s] for v in tower}) == len(tower) for s in range(4))

def tower_is_solved(bits):
    v = int(bits, 2)                      # Qiskit key: qubit 0 is rightmost
    views = []
    for c, cube in enumerate(CUBES):
        k = CHOICES.index(ALIAS[(v >> (3*c)) & 7])
        views.append(orientations(cube)[4*k:4*k+4])
    return any(solves(t) for t in itertools.product(*views))

NQ = 12
TERMS = hamiltonian_terms(CUBES)
print(f"{len(TERMS)} Z terms, longest {max(bin(m).count('1') for m in TERMS)}")

# ---- build, add marker qubit, measure, transpile
circ = qaoa_circuit(TERMS, NQ, ANGLES[:P], ANGLES[P:])
qc = QuantumCircuit(NQ + 1)
qc.compose(circ, range(NQ), inplace=True)
qc.x(NQ)                                  # marker, always 1: shows key orientation
qc.measure_all()
qc = transpile(qc, basis_gates=["rz","sx","x","cx"], optimization_level=1)
print(f"submitting: {qc.num_qubits} qubits, {qc.count_ops().get('cx',0)} cx, depth {qc.depth()}")

# ---- submit to SV1
SHOTS = 2000
device = QbraidProvider().get_device("aws:aws:sim:sv1")
print(device.id, "|", device.status().name, "|", device.num_qubits, "qubits")
job = device.run(qc, shots=SHOTS)
print("JOB ID:", job.id)
raw = job.result().data.get_counts()

def strip_marker(raw):
    if all(k[0] == "1" for k in raw):  return {k[1:]: n for k, n in raw.items()}
    if all(k[-1] == "1" for k in raw): return {k[:-1][::-1]: n for k, n in raw.items()}
    raise ValueError("marker bit not found")

counts = strip_marker(raw)
good = sum(n for b, n in counts.items() if tower_is_solved(b))
print(f"\n{good} of {SHOTS} shots decode to a SOLVED TOWER  ->  {good/SHOTS:.2%}")
print(f"exact prediction  {0.44616:.2%}")
print(f"random baseline   {0.001465:.3%}")
print(f"lift              x{(good/SHOTS)/0.00146484:.0f}")
print("\nJOB ID (put this in README.md):", job.id)
