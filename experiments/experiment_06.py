"""IVA Brain Experiment 06: test whether discovered skills transfer to new contexts.

Skills are mined from one set of self-generated trajectories (Experiment 05).
They are then evaluated, without retraining the skill library, in fresh episodes
with randomized obstacle maps and new start/goal pairs. A random-action baseline
uses the same action budget. This is a transfer evaluation, not evidence of AGI.
"""
from __future__ import annotations
import argparse
import random
from experiments.experiment_01 import World
from experiments.experiment_05 import collect, discover_skills
from experiments.experiment_01 import OnlineAgent

def make_world(seed, size=7, wall_count=5):
    rng = random.Random(seed)
    cells = [(x, y) for x in range(size) for y in range(size)]
    walls = set(rng.sample(cells, wall_count))
    start = (0, 0)
    goal = (size - 1, size - 1)
    walls.discard(start)
    walls.discard(goal)
    return World(size=size, walls=walls, position=start), start, goal

def run_skill(world, start, goal, actions):
    world.position = start
    initial = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    for action in actions:
        world.step(action)
    final = abs(world.position[0] - goal[0]) + abs(world.position[1] - goal[1])
    return initial - final, world.position

def run_random(world, start, goal, length, rng):
    world.position = start
    initial = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    for _ in range(length):
        world.step(rng.randrange(4))
    final = abs(world.position[0] - goal[0]) + abs(world.position[1] - goal[1])
    return initial - final

def evaluate(skills, trials=200, seed=606):
    rng = random.Random(seed)
    skill_gains, random_gains = [], []
    usable = [s for s in skills if len(s["actions"]) >= 2]
    if not usable:
        return [], []
    # Choose the skill using training-world statistics only. Do not inspect
    # test-map outcomes to select the skill: that would leak the answer.
    chosen = max(usable, key=lambda skill: skill["score"])
    for i in range(trials):
        world, start, goal = make_world(seed + i)
        gain, _ = run_skill(world, start, goal, chosen["actions"])
        skill_gains.append(gain / len(chosen["actions"]))
        random_world, _, _ = make_world(seed + i)
        random_gains.append(run_random(random_world, start, goal,
                                       len(chosen["actions"]), rng) /
                            len(chosen["actions"]))
    return skill_gains, random_gains

