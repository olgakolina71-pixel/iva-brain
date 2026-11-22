# IVA Brain

IVA Brain is an experimental project exploring learning from its own interaction—not from external training datasets, SFT, or LoRA. It is **not** a finished AI or evidence of consciousness.

## Text conversation

Run with Python 3.10+:

```bash
python iva_chat.py
```

IVA Language v0.3 includes:
- simple Russian text dialogue;
- explicit local teaching with `/teach your example`;
- a small word-transition generator with `/generate`;
- a symbolic fact memory for a few patterns, such as `робот это машина`, `IVA изучает язык`, or `IVA помогает человеку`;
- answers to limited questions such as `что такое робот?`, `что изучает iva?`, and `кто изучает язык?`;
- `/facts` to inspect learned relations, `/memory` for counts, and `/reset` to clear local memory.

Example lesson sequence:

```text
/teach робот это машина
/teach IVA изучает язык
/teach IVA помогает человеку
что такое робот?
что изучает iva?
кто изучает язык?
/facts
```

The fact layer extracts only a few explicit sentence patterns. It does not infer facts, understand arbitrary language, or know whether a taught statement is true. The word-transition generator can produce nonsense. This is a small symbolic experiment, not a neural language model. All examples and facts are stored in local plain-text `iva_memory.json`; keep private information out of it.

## World-model experiments

1. **Experiment 01 — Online world model:** learn a tiny sandbox's transitions from self-generated experience.
2. **Experiment 02 — Model-based planning:** use the learned predictor to plan toward an externally supplied goal.
3. **Experiment 03 — Intrinsic goals:** select goals from novelty/uncertainty heuristics and attempt them using the learned model.
4. **Experiment 04 — Changing world:** change the environment mid-run and measure prediction surprise and online adaptation.
5. **Experiment 05 — Skill discovery:** mine repeated action chunks from self-generated experience and store useful chunks as skills.
6. **Experiment 06 — Skill transfer:** test a skill library learned in one map against fresh randomized maps and compare progress with a random-action baseline.

These are narrow, controlled experiments. Curiosity and goal selection are explicit heuristics, not human-like feelings or evidence of consciousness.

## Run world-model experiments

Python 3.10+ and PyTorch are required.

```bash
pip install -r requirements-experiment01.txt
python -m experiments.experiment_01
python -m experiments.experiment_02
python -m experiments.experiment_03
python -m experiments.experiment_04
python -m experiments.experiment_05
python -m experiments.experiment_06
```

## Project constraints

- No external training dataset for the world-model experiments.
- Learn from generated observations, actions, outcomes, and feedback.
- IVA Nano is a separate project.
- Do not claim consciousness or human-like feelings.
- Windows control, video perception, ESP32, and robotics are future integrations, not implemented.
