"""IVA Brain Experiment 05: discover reusable action chunks from experience.

This experiment is deliberately not Q-learning. It mines short action sequences
from the agent's own interaction history, scores them by repeatability and
observed usefulness, then tests whether replaying a discovered skill can move
the agent in a new start/goal situation. The skill library is an explicit,
inspectable memory structure; it is not a claim of general intelligence.
"""
from __future__ import annotations
import argparse
import random
from collections import Counter, defaultdict
import torch
from experiments.experiment_01 import World, OnlineAgent, ACTIONS

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def collect(agent, world, episodes=35, steps=45, seed=505):
    rng = random.Random(seed)
    traces = []
    for _ in range(episodes):
        world.position = (rng.randrange(world.size), rng.randrange(world.size))
        while world.position in world.walls:
            world.position = (rng.randrange(world.size), rng.randrange(world.size))
        trace = []
        obs = world.observe()
        for _ in range(steps):
            action = rng.randrange(4)
            before = world.position
            nxt = world.step(action)
            agent.learn(obs, action, nxt)
            trace.append((before, action, world.position))
            obs = nxt
        traces.append(trace)
    return traces

def discover_skills(traces, min_count=3, max_len=4):
    counts = Counter()
    outcomes = defaultdict(list)
    for trace in traces:
        for length in range(2, max_len + 1):
            for i in range(len(trace) - length + 1):
                chunk = trace[i:i + length]
                actions = tuple(item[1] for item in chunk)
                start, end = chunk[0][0], chunk[-1][2]
                # Utility is net displacement per action, with blocked steps
                # naturally receiving zero displacement.
                utility = manhattan(start, end) / length
                counts[actions] += 1
                outcomes[actions].append(utility)
    skills = []
    for actions, count in counts.items():
        if count < min_count:
            continue
        utilities = outcomes[actions]
        mean_utility = sum(utilities) / len(utilities)
        # Prefer repeatable chunks that reliably produce a non-zero effect.
        consistency = 1.0 / (1.0 + (sum((u-mean_utility)**2 for u in utilities)/len(utilities)))
        score = mean_utility * consistency * (count ** 0.5)
        if mean_utility > 0:
            skills.append({"actions": actions, "count": count,
                           "mean_utility": mean_utility, "score": score})
    skills.sort(key=lambda s: (s["score"], s["count"]), reverse=True)
    # Keep a compact and diverse library, not every possible substring.
    chosen = []
    seen = set()
    for skill in skills:
        if skill["actions"] in seen:
            continue
        chosen.append(skill)
        seen.add(skill["actions"])
        if len(chosen) == 20:
            break
    return chosen

def replay_skill(world, start, goal, skill):
    world.position = start
    initial_distance = manhattan(start, goal)
    for action in skill["actions"]:
        world.step(action)
    final_distance = manhattan(world.position, goal)
    return initial_distance - final_distance, world.position

def evaluate(skills, trials=100, seed=506):
    rng = random.Random(seed)
    world = World()
    free = [(x, y) for x in range(world.size) for y in range(world.size)
            if (x, y) not in world.walls]
    results = []
    for skill in skills:
        gains = []
        for _ in range(trials):
            start = rng.choice(free)
            goal = rng.choice(free)
            while goal == start:
                goal = rng.choice(free)
            gain, _ = replay_skill(world, start, goal, skill)
            gains.append(gain)
        results.append((skill, sum(gains)/len(gains),
                        sum(g > 0 for g in gains)/len(gains)))
    return results

def run(episodes=35, steps=45, seed=505):
    torch.manual_seed(seed)
    random.seed(seed)
    agent = OnlineAgent(seed=seed)
    world = World()
    traces = collect(agent, world, episodes, steps, seed)
    skills = discover_skills(traces)
    results = evaluate(skills)
    print("IVA Brain Experiment 05 | experience-based skill discovery")
    print(f"Experience: {episodes * steps} transitions")
    print(f"Discovered reusable action chunks: {len(skills)}")
    for skill, gain, positive_rate in results[:5]:
        print(f"Skill {skill['actions']} | occurrences={skill['count']} "
              f"| mean_gain={gain:.3f} | positive_goal_rate={positive_rate:.1%}")
    if not skills:
        print("No skills passed the discovery threshold; increase collection episodes.")
    torch.save({"models": [m.state_dict() for m in agent.models],
                "steps": agent.steps, "skills": skills},
               "iva_exp05_checkpoint.pt")
    print("Checkpoint saved: iva_exp05_checkpoint.pt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=35)
    parser.add_argument("--steps", type=int, default=45)
    parser.add_argument("--seed", type=int, default=505)
    args = parser.parse_args()
    run(args.episodes, args.steps, args.seed)
