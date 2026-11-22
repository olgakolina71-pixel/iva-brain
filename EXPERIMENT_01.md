# Experiment 01 — Online World Model

## Hypothesis
An untrained neural network can improve its predictions of a simple environment by collecting transitions through interaction and updating its weights online, without a training dataset.

## Sandbox
7×7 grid with a few fixed obstacles. Observations contain normalized position and four local obstacle flags. Actions are north/east/south/west. Invalid moves leave the agent in place.

## Learning
Three small neural predictors are trained online from the agent's own experience buffer. The action selector favors under-explored state/action combinations and predictor disagreement. This is a basic curiosity/exploration heuristic, not human-like motivation.

## Run
Python 3.10+ and PyTorch:
```bash
pip install -r requirements-experiment01.txt
python experiments/experiment_01.py
```
The script saves a checkpoint in the working directory.

## Initial local result (seed 42, 2,000 interactions)
- All 44 non-wall cells visited.
- 176 state/action combinations explored.
- Online prediction loss generally fell over training chunks.
- Generated validation MSE: untrained ensemble 0.2076; learned ensemble 0.0397.

This demonstrates learning a narrow sandbox's transition dynamics. It does **not** demonstrate general intelligence, consciousness, or transfer to a real-world environment. The validation set is generated from the same sandbox rules, not an external dataset.
