# IVA Brain

IVA Brain is an experimental project exploring learning from its own interaction—not from datasets, SFT, or LoRA. It is **not** a finished AI or evidence of consciousness.

## Current status
The repository contains a small online world-model prototype and five focused experiments. These test separate learning mechanisms; they do not yet constitute a general-purpose intelligence.

## Experiments
1. **Experiment 01 — Online world model:** learn a tiny sandbox's transitions from self-generated experience.
2. **Experiment 02 — Model-based planning:** use the learned predictor to plan toward an externally supplied goal.
3. **Experiment 03 — Intrinsic goals:** select goals from novelty/uncertainty heuristics and attempt them using the learned model.
4. **Experiment 04 — Changing world:** change the environment mid-run and measure prediction surprise and online adaptation.
5. **Experiment 05 — Skill discovery:** mine repeated action chunks from self-generated experience, store useful chunks as skills, and test their transfer to new start/goal pairs. This is not Q-learning.

These are narrow, controlled experiments. Curiosity and goal selection are explicit heuristics, not human-like feelings or evidence of consciousness.

## Run all experiments
Python 3.10+ and PyTorch are required.

```bash
pip install -r requirements-experiment01.txt
python -m experiments.experiment_01
python -m experiments.experiment_02
python -m experiments.experiment_03
python -m experiments.experiment_04
python -m experiments.experiment_05
```

Each experiment writes a checkpoint in the current working directory. Experiments 02–05 reuse the online learner from Experiment 01.

## Project constraints
- No external training dataset for these experiments.
- Learn from generated observations, actions, outcomes, and feedback.
- IVA Nano is a separate project.
- Do not claim consciousness or human-like feelings.
- Windows control, video perception, ESP32, and robotics are future integrations, not implemented.

## Research questions
- Can online learning generalize to changed maps and dynamics?
- Does model-based planning improve goal success over simple baselines?
- Can intrinsic-goal selection be evaluated without tuning to one environment?
- Can the agent detect when its model becomes unreliable and adapt efficiently?
- Do discovered action chunks transfer to new contexts better than random chunks?
- How should experience and checkpoints persist across restarts?
