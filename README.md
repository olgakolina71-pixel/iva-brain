# IVA Brain

IVA Brain is an experimental project exploring learning from its own interaction—not from external training datasets, SFT, or LoRA. It is **not** a finished AI or evidence of consciousness.

## IVA Language v0.4 — conversation learning

Run with Python 3.10+:

```bash
python iva_chat.py
```

IVA now has three small learning mechanisms:
- **Facts:** `/teach робот это машина` stores a simple subject-relation-object fact.
- **Word patterns:** `/generate` recombines word transitions from taught examples.
- **Dialogue retrieval:** `/learn привет || Привет! Как настроение?` stores a question/answer pair. Later, IVA can reuse that answer when a new message has enough keyword overlap with the learned question.

Other commands: `/facts`, `/memory`, `/reset`, `/help`, `/exit`.

Example:

```text
/learn привет || Привет! Как настроение?
/learn что ты любишь || Я люблю изучать новые вещи.
/learn расскажи про роботов || Роботы — это машины, которые могут выполнять задачи.
/memory
```

This is example-based retrieval, not neural training: IVA compares keywords and reuses a stored answer. It does not reliably understand paraphrases, verify truth, or generalize like a language model. Its ordinary chat history is logged, but is not automatically treated as correct training data. Teach it only examples you want it to learn; local memory is plain-text JSON, so do not store private information there.

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
