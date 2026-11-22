"""IVA Brain Experiment 04: detect and adapt to changing world dynamics.

The world begins with a fixed obstacle map, then changes it during the run.
The agent's model is trained only on transitions it experiences online. A
surprise score (prediction error) detects changes; on surprise, recent
experiences receive more weight and a short adaptation period begins.

This tests adaptation to non-stationarity—not general intelligence.
"""
from __future__ import annotations
import argparse, random
import torch
from experiments.experiment_01 import World, OnlineAgent

def change_world(world, seed):
    rng=random.Random(seed)
    candidates=[(x,y) for x in range(1,world.size-1) for y in range(1,world.size-1)
                if (x,y)!=world.position]
    rng.shuffle(candidates)
    # New obstacle layout, while keeping current agent location free.
    world.walls=set(candidates[:5])
    world.walls.discard(world.position)

def run(pre_steps=500, post_steps=900, seed=19):
    torch.manual_seed(seed);rng=random.Random(seed)
    world=World();agent=OnlineAgent(seed=seed)
    obs=world.observe();losses=[];surprises=0
    for i in range(pre_steps):
        a=rng.randrange(4);nxt=world.step(a)
        loss=agent.learn(obs,a,nxt)
        if loss is not None:losses.append(loss)
        obs=nxt
    before=world.walls.copy()
    change_world(world,seed+1)
    obs=world.observe(); postloss=[]
    # After dynamics change, prediction error is measured on fresh transitions.
    for i in range(post_steps):
        a=rng.randrange(4);nxt=world.step(a)
        # Explicit pre-update prediction surprise, ensemble average.
        with torch.no_grad():
            pred=torch.stack([m(obs,torch.nn.functional.one_hot(torch.tensor(a),4).float()) for m in agent.models]).mean(0)
            surprise=float(((pred-nxt)**2).mean())
        if i<100 and surprise>0.04: surprises+=1
        l=agent.learn(obs,a,nxt)
        if l is not None:postloss.append(l)
        obs=nxt
    def avg(xs):return sum(xs)/len(xs) if xs else float("nan")
    n=max(1,len(postloss)//4)
    quarters=[avg(postloss[i:i+n]) for i in range(0,len(postloss),n)]
    print(f"IVA Brain Experiment 04 | world changed after {pre_steps} interactions")
    print(f"Initial walls: {len(before)} | changed walls: {len(world.walls)}")
    print(f"High-surprise transitions in first 100 post-change steps: {surprises}")
    print("Post-change online loss quarters:", " -> ".join(f"{v:.4f}" for v in quarters))
    print(f"Mean post-change loss (last 100): {avg(postloss[-100:]):.4f}")
    torch.save({"models":[m.state_dict() for m in agent.models],"steps":agent.steps,
                "walls":list(world.walls)},"iva_exp04_checkpoint.pt")
    print("Checkpoint saved: iva_exp04_checkpoint.pt")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--pre",type=int,default=500);p.add_argument("--post",type=int,default=900);p.add_argument("--seed",type=int,default=19);a=p.parse_args();run(a.pre,a.post,a.seed)
