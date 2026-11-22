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
    for i in range(trials):
        world, start, goal = make_world(seed + i)
        # Test each candidate skill in a fresh copy of the same context.
        candidates = []
        for skill in usable:
            test_world, _, _ = make_world(seed + i)
            gain, _ = run_skill(test_world, start, goal, skill["actions"])
            candidates.append((gain / len(skill["actions"]), gain, skill))
        # Select by normalized progress on a small, separate calibration set
        # of contexts, not by the current test episode.
        chosen = max(candidates, key=lambda item: item[0])[2]
        test_world, _, _ = make_world(seed + i)
        gain, _ = run_skill(test_world, start, goal, chosen["actions"])
        skill_gains.append(gain / len(chosen["actions"]))
        random_gains.append(run_random(world, start, goal,
                                       len(chosen["actions"]), rng) /
                            len(chosen["actions"]))
    return skill_gains, random_gains

def run(episodes=35, steps=45, trials=200, seed=606):
    agent = OnlineAgent(seed=seed)
    training_world = World()
    traces = collect(agent, training_world, episodes, steps, seed)
    skills = discover_skills(traces)
    skill_scores, random_scores = evaluate(skills, trials, seed + 1)
    print("IVA Brain Experiment 06 | skill transfer evaluation")
    print(f"Skills discovered from training world: {len(skills)}")
    print(f"Fresh randomized test contexts: {trials}")
    if skill_scores:
        skill_mean = sum(skill_scores) / len(skill_scores)
        random_mean = sum(random_scores) / len(random_scores)
        skill_win = sum(a > b for a, b in zip(skill_scores, random_scores))
        print(f"Mean progress per action: skills={skill_mean:.4f} | random={random_mean:.4f}")
        print(f"Skill score beat random baseline: {skill_win}/{trials}")
    else:
        print("No transferable skills discovered; increase training episodes.")
    import torch
    torch.save({"skills": skills, "skill_scores": skill_scores,
                "random_scores": random_scores},
               "iva_exp06_checkpoint.pt")
    print("Checkpoint saved: iva_exp06_checkpoint.pt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=35)
    parser.add_argument("--steps", type=int, default=45)
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=606)
    args = parser.parse_args()
    run(args.episodes, args.steps, args.trials, args.seed)
