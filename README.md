# IVA Brain

IVA Brain is an experimental project exploring learning from its own interaction—not from datasets, SFT, or LoRA. It is **not** a finished AI or evidence of consciousness.

## Current status
The repository contains an early behavior simulator/prototype and three focused ML experiments. The prototype's hand-written internal-state rules are not the intelligence core; the experiments test learning mechanisms separately.

## Experiments
1. **Experiment 01 — Online world model:** learn a tiny sandbox's transitions from self-generated experience.
2. **Experiment 02 — Model-based planning:** use the learned predictor to plan toward an externally supplied goal.
3. **Experiment 03 — Intrinsic goals:** select goals from novelty/uncertainty heuristics and attempt them using the learned model.

These are narrow experiments. The current “curiosity” mechanism is an explicit heuristic, not a human-like feeling or a general autonomous mind.

## Run experiments
Python 3.10+ and PyTorch are required.

```bash
pip install -r requirements-experiment01.txt
python -m experiments.experiment_01
python -m experiments.experiment_02
python -m experiments.experiment_03
```

Each experiment writes a checkpoint in the working directory. Experiments 02 and 03 depend on Experiment 01's shared code.

## Project constraints
- No external training dataset for IVA Brain.
- Learn from generated observations, actions, outcomes, and feedback.
- IVA Nano is a separate project.
- Do not claim consciousness or human-like feelings.
- Windows control, video perception, ESP32, and robotics are future integrations, not implemented.

## Next research questions
- Can online learning generalize to changed maps and dynamics?
- Can planning improve task success over random/heuristic baselines?
- Can intrinsic-goal selection be evaluated without tuning to one environment?
- How should experience and checkpoints persist across restarts?
