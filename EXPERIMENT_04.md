# Experiment 04 — Adaptation to a Changing World

## Question
When the environment changes, does IVA's online world model notice its predictions are wrong and adapt from fresh experience?

## Procedure
- Interact with the original obstacle layout for a period.
- Change the obstacle map.
- Continue acting and updating from new observations.
- Log prediction surprise during the first 100 post-change interactions and loss over subsequent time windows.

## Run
```bash
pip install -r requirements-experiment01.txt
python -m experiments.experiment_04
```

Optional: `--pre 500 --post 900 --seed 19`.

## Metrics
- Prediction error/surprise shortly after change.
- Loss trend over post-change experience.
- Final recent loss.
- Checkpoint of learned weights and changed map.

## Limitations
This script changes obstacle layout only. It does not implement a separate novelty detector or adaptive learning-rate controller; adaptation relies on the existing online update loop and experience buffer. The experiment has not been run yet. Do not claim results until actually executed.
