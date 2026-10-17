"""Puzzle definitions copied verbatim from the challenge's starter_notebook.ipynb.

These are the organizers' reference functions. We use them as the INDEPENDENT
checker for our own encoding, so they are deliberately not rewritten.
"""

import itertools
import random

COLOURS = "RGBY"

CUBES = [
    ["GR", "BR", "GY"],   # cube 1
    ["GY", "RB", "BY"],   # cube 2
    ["BR", "RG", "RY"],   # cube 3
    ["YR", "RG", "BG"],   # cube 4
]

CHOICES = list(itertools.permutations(range(3), 2))  # (front/back pair, left/right pair)


def orientations(cube):
    """The 24 ways a cube can sit, as (front, back, left, right) colours."""
    views = []
    for a, b in itertools.permutations(range(3), 2):   # front/back pair, left/right pair
        for fa in (0, 1):
            for fb in (0, 1):
                fb_pair, lr_pair = cube[a], cube[b]
                views.append((fb_pair[fa], fb_pair[1 - fa], lr_pair[fb], lr_pair[1 - fb]))
    return views


def solves(tower):
    """True when each of the four sides shows four different colours."""
    return all(len({view[side] for view in tower}) == len(tower) for side in range(4))


def make_puzzle(n, seed):
    """N cubes, N colours, a planted answer: two random cycles through all colours."""
    rng = random.Random(seed)
    letters = "".join(chr(ord("A") + i) for i in range(n))
    cycles = []
    for _ in range(2):
        order = rng.sample(letters, n)
        lines = [order[i] + order[(i + 1) % n] for i in range(n)]
        rng.shuffle(lines)
        cycles.append(lines)
    cubes = []
    for i in range(n):
        third = rng.choice(letters) + rng.choice(letters)
        pairs = ["".join(rng.sample(pair, 2)) for pair in (cycles[0][i], cycles[1][i], third)]
        rng.shuffle(pairs)
        cubes.append(pairs)
    return cubes


def count_answers(cubes):
    """How many of the 6**n cases solve the puzzle."""
    letters = sorted({ch for cube in cubes for pair in cube for ch in pair})
    total = 0
    for choice in itertools.product(CHOICES, repeat=len(cubes)):
        for side in (0, 1):
            deg = dict.fromkeys(letters, 0)
            for cube, pick in zip(cubes, choice):
                for ch in cube[pick[side]]:
                    deg[ch] += 1
            if any(d != 2 for d in deg.values()):
                break
        else:
            total += 1
    return total


# seeds the starter notebook says give exactly one tower
BONUS = {5: 16, 6: 86, 7: 68, 8: 4}


def solved_by_brute_force(cubes, choice):
    """Independent truth for one (fb, lr) choice per cube: does ANY flip of the
    two axes give a tower that `solves`? Uses only `orientations` and `solves`."""
    views = []
    for cube, (fb, lr) in zip(cubes, choice):
        mine = []
        for v in orientations(cube):
            pass
        # restrict the 24 views to those using this (fb, lr) pair assignment
        k = CHOICES.index((fb, lr))
        mine = orientations(cube)[4 * k: 4 * k + 4]
        views.append(mine)
    return any(solves(t) for t in itertools.product(*views))
