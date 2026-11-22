# Experiment 03 — Autonomous Curiosity-Driven Goals

## Question
Can IVA select destinations without the experimenter specifying a goal, and then use its learned transition model to attempt to reach them?

## Mechanism
1. Explore randomly and learn dynamics from self-generated transitions (online updates).
2. Select an intrinsic goal using novelty (visit counts), a small uncertainty bonus, and a distance penalty.
3. Plan short action sequences with the learned ensemble model.
4. Execute one action, observe the result, and update from the new experience.
5. Replace a goal when reached or when its action budget expires.

This is a simple explicit curiosity heuristic, not genuine subjective desire. It is useful because the goal selection and planning are measurable and replaceable.

## Run
```bash
pip install -r requirements-experiment01.txt
python -m experiments.experiment_03
```

Options: `--pretrain 900 --steps 700 --seed 123`.

## Metrics
Visited cells, goals selected, goals reached, repeated visits. A successful run does not prove general intelligence; it tests autonomous goal selection and model-based action in this tiny sandbox.

## Known limitations
- The world model is approximate and can produce planning errors.
- Novelty is based on visit counts, not semantic curiosity.
- Candidate-goal selection uses a simple geometric distance, which is not a true obstacle-aware route cost.
- Goal reaching is not guaranteed.
- The experiment has not been run in this commit; numbers must be recorded only after an actual run.
