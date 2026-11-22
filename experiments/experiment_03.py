"""IVA Brain Experiment 03: autonomous curiosity-driven goal formation.

The sandbox provides no externally assigned destination. The agent selects
candidate goals based on its own experience: novelty, model uncertainty, and
estimated travel effort. It then uses the learned world model to plan toward
the selected goal. This remains a small controlled experiment, not AGI.
"""
from __future__ import annotations
import argparse, random, itertools, math
import torch
from experiments.experiment_01 import World, OnlineAgent, action_tensor, ACTIONS

def xy(obs, size=7):
    return (round(float(obs[0])*(size-1)), round(float(obs[1])*(size-1)))

def predict_step(agent, obs, action):
    with torch.no_grad():
        preds=torch.stack([m(obs,action_tensor(action)) for m in agent.models])
    return preds.mean(0), float(preds.var(dim=0,unbiased=False).mean())

def plan_first_action(agent, obs, goal, horizon=3):
    best, best_score=0,float("inf")
    with torch.no_grad():
        for seq in itertools.product(range(4),repeat=horizon):
            state=obs.clone(); unc=0.0
            for a in seq:
                preds=torch.stack([m(state,action_tensor(a)) for m in agent.models])
                unc += float(preds.var(dim=0,unbiased=False).mean())
                state=preds.mean(0)
            px,py=float(state[0])*6,float(state[1])*6
            distance=math.hypot(px-goal[0],py-goal[1])
            score=distance+0.35*unc
            if score<best_score:best,best_score=seq[0],score
    return best

def choose_intrinsic_goal(agent, world, position_visits, goal_visits, rng):
    free=[(x,y) for x in range(world.size) for y in range(world.size) if (x,y) not in world.walls]
    here=world.position; scored=[]
    obs=world.observe()
    for candidate in free:
        if candidate==here:continue
        # Novelty reward fades as this cell is explored. A small distance penalty
        # discourages selecting unreachable-feeling distant goals repeatedly.
        n=position_visits.get(candidate,0)
        novelty=1.0/(1+n)
        distance=math.hypot(candidate[0]-here[0],candidate[1]-here[1])
        # Ensemble uncertainty is queried from the current state for a first-step
        # direction toward this candidate; used as a curiosity bonus.
        dx=candidate[0]-here[0];dy=candidate[1]-here[1]
        action=min(range(4),key=lambda a:-(dx*ACTIONS[a][0]+dy*ACTIONS[a][1]))
        _,unc=predict_step(agent,obs,action)
        score=novelty+0.12*unc-0.035*distance-0.25*goal_visits.get(candidate,0)
        scored.append((score+rng.random()*0.015,candidate))
    return max(scored)[1]

def run(pretrain_steps=900, autonomous_steps=700, seed=123):
    torch.manual_seed(seed);rng=random.Random(seed)
    world=World();agent=OnlineAgent(seed=seed)
    # Learn the world model solely from self-generated interactions.
    obs=world.observe()
    for _ in range(pretrain_steps):
        action=rng.randrange(4);nxt=world.step(action);agent.learn(obs,action,nxt);obs=nxt
    # Now autonomous loop: agent creates an intrinsic destination, acts, observes,
    # and online-updates the model from each new transition.
    pos_visits={};goal_visits={}; reached=0;goal=None;remaining=0
    obs=world.observe();visited=set([world.position]);goal_changes=0
    for step in range(autonomous_steps):
        pos_visits[world.position]=pos_visits.get(world.position,0)+1
        if goal is None or world.position==goal or remaining<=0:
            if goal is not None and world.position==goal:reached+=1
            goal=choose_intrinsic_goal(agent,world,pos_visits,goal_visits,rng)
            goal_visits[goal]=goal_visits.get(goal,0)+1
            remaining=45;goal_changes+=1
        action=plan_first_action(agent,obs,goal,horizon=3)
        nxt=world.step(action)
        agent.learn(obs,action,nxt)
        visited.add(world.position);obs=nxt;remaining-=1
    print(f"IVA Brain Experiment 03 | self-generated goals")
    print(f"Transitions: {pretrain_steps} exploration + {autonomous_steps} goal-driven")
    print(f"Distinct cells visited: {len(visited)}/{world.size*world.size-len(world.walls)}")
    print(f"Goals selected: {goal_changes} | goals reached: {reached}")
    print(f"Unique cells revisited at least 3 times: {sum(v>=3 for v in pos_visits.values())}")
    torch.save({"models":[m.state_dict() for m in agent.models],"steps":agent.steps,
                "position_visits":pos_visits,"goal_visits":goal_visits},
               "iva_exp03_checkpoint.pt")
    print("Checkpoint saved: iva_exp03_checkpoint.pt")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--pretrain",type=int,default=900);p.add_argument("--steps",type=int,default=700);p.add_argument("--seed",type=int,default=123);a=p.parse_args();run(a.pretrain,a.steps,a.seed)
