"""Render the slide figures from results/bonus.json."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VIOLET, GREEN, AMBER, RED, INK = "#8B5CF6", "#2FA95F", "#E8B400", "#D64545", "#1E1B3A"
Path("figures").mkdir(exist_ok=True)
R = json.loads(Path("results/bonus.json").read_text())
four = next(r for r in R if r["n"] == 4)

plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#B8B4C8",
                     "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK, "ytick.color": INK})


def save(fig, name):
    fig.savefig(f"figures/{name}.png", dpi=200, transparent=True, bbox_inches="tight")
    plt.close(fig)
    print("wrote figures/" + name + ".png")


# 1. success rate vs p for the four-cube puzzle
fig, ax = plt.subplots(figsize=(6.2, 3.4))
tr = four["trace"]
ax.plot([e["p"] for e in tr], [100 * e["p_solved"] for e in tr], "o-",
        color=VIOLET, lw=2.4, ms=6, label="compact QAOA")
ax.axhline(100 * four["baseline"], ls="--", lw=2, color=RED,
           label=f"random guess ({four['baseline']:.3%})")
ax.set_xlabel("QAOA layers  p")
ax.set_ylabel("P(solved tower)   [%]")
ax.legend(frameon=False)
ax.grid(alpha=0.22)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "layers")

# 2. qubits: compact vs one-hot
fig, ax = plt.subplots(figsize=(5.0, 3.4))
ns = [r["n"] for r in R]
ax.plot(ns, [6 * n for n in ns], "s--", color=RED, lw=2.2, ms=7, label="one-hot  6N")
ax.plot(ns, [r["qubits"] for r in R], "o-", color=VIOLET, lw=2.6, ms=7, label="compact  3N")
ax.set_xlabel("N cubes")
ax.set_ylabel("qubits")
ax.set_xticks(ns)
ax.legend(frameon=False)
ax.grid(alpha=0.22)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "qubits")

# 3. success vs random as N grows
fig, ax = plt.subplots(figsize=(5.6, 3.4))
ax.semilogy(ns, [100 * r["p_solved"] for r in R], "o-", color=VIOLET, lw=2.6, ms=7, label="compact QAOA")
ax.semilogy(ns, [100 * r["baseline"] for r in R], "s--", color=RED, lw=2.2, ms=7, label="random guess")
ax.set_xlabel("N cubes")
ax.set_ylabel("P(solved)   [%]   log scale")
ax.set_xticks(ns)
ax.legend(frameon=False)
ax.grid(alpha=0.22, which="both")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "scaling")

# 4. alias search saving
fig, ax = plt.subplots(figsize=(5.0, 3.2))
labels = [f"N={r['n']}" for r in R]
x = range(len(R))
ax.bar([i - 0.2 for i in x], [r["naive_cx_per_layer"] for r in R], width=0.4,
       color=RED, label="naive map")
ax.bar([i + 0.2 for i in x], [r["cx_per_layer"] for r in R], width=0.4,
       color=GREEN, label="searched map")
ax.set_xticks(list(x))
ax.set_xticklabels(labels)
ax.set_ylabel("CX gates per cost layer")
ax.legend(frameon=False)
ax.grid(alpha=0.22, axis="y")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "alias")
