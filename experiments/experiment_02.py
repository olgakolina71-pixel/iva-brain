"""IVA Brain Experiment 02: use a learned world model for goal-directed planning.

The agent first collects its own transitions by exploration, online-trains the
Experiment 01 predictor, then plans by simulating short action sequences with
the learned model. No external training dataset is used.
"""
from __future__ import annotations
import argparse, random, itertools
import torch
from experiments.experiment_01 import World, OnlineAgent, action_tensor

def train_from_interaction(agent, world, steps=1500, seed=11):
    rng=random.Random(seed); obs=world.observe()
    for _ in range(steps):
        action=rng.randrange(4)
        nxt=world.step(action)
        agent.learn(obs,action,nxt)
        obs=nxt
    return agent

def plan(agent, obs, goal, horizon=4):
    # Receding-horizon model-based planning: score candidate sequences by
    # predicted goal distance and penalize ensemble disagreement.
    best_action=0; best_score=float("inf")
    with torch.no_grad():
        for seq in itertools.product(range(4), repeat=horizon):
            state=obs.clone(); uncertainty=0.0
            for a in seq:
                at=action_tensor(a)
                pred=torch.stack([m(state,at) for m in agent.models])
                uncertainty += float(pred.var(dim=0,unbiased=False).mean())
                state=pred.mean(dim=0)
            dist=((float(state[0])*6-goal[0])**2+(float(state[1])*6-goal[1])**2)**0.5
            score=dist+0.7*uncertainty
            if score<best_score: best_score=score; best_action=seq[0]
    return best_action

def shortest_steps(world, start, goal):
    # Ground-truth BFS only used to select solvable evaluation goals; not given
    # to the learner or its planner.
    q=[(start,0)]; seen={start}
    for pos,d in q:
        if pos==goal:return d
        for dx,dy in world.__class__.__dict__.get("ACTIONS",((0,-1),(1,0),(0,1),(-1,0))):
            nxt=(pos[0]+dx,pos[1]+dy)
            if 0<=nxt[0]<world.size and 0<=nxt[1]<world.size and nxt not in world.walls and nxt not in seen:
                seen.add(nxt);q.append((nxt,d+1))
    return None

def evaluate(agent, trials=30, max_steps=40, seed=77):
    rng=random.Random(seed); world=World(); successes=steps_total=0
    free=[(x,y) for x in range(world.size) for y in range(world.size) if (x,y) not in world.walls]
    for _ in range(trials):
        start=rng.choice(free); goal=rng.choice(free)
        while goal==start:goal=rng.choice(free)
        world.position=start; obs=world.observe()
        for step in range(max_steps):
            if world.position==goal:successes+=1;steps_total+=step;break
            action=plan(agent,obs,goal,horizon=4)
            obs=world.step(action)
        else: steps_total+=max_steps
    return successes,steps_total/trials

def run(collect=1500,trials=30,seed=11):
    torch.manual_seed(seed);random.seed(seed)
    agent=OnlineAgent(seed=seed);world=World()
    train_from_interaction(agent,world,collect,seed)
    success,avg=evaluate(agent,trials)
    print(f"IVA Brain Experiment 02 | transitions collected={collect}")
    print(f"Goal reached: {success}/{trials} within 40 steps")
    print(f"Mean steps (timeouts counted as 40): {avg:.2f}")
    torch.save({"models":[m.state_dict() for m in agent.models],"experience_steps":agent.steps},"iva_exp02_checkpoint.pt")
    print("Saved iva_exp02_checkpoint.pt")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--collect",type=int,default=1500);p.add_argument("--trials",type=int,default=30);a=p.parse_args();run(a.collect,a.trials)
