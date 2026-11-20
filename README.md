# IVA Brain

An experimental cognitive architecture for IVA that learns from interaction and experience—not from datasets, SFT, or LoRA.

## v0.1 goals
- Persistent SQLite memory and experience log
- Working state: energy, fatigue, interest, curiosity, laziness
- Decision policy influenced by internal state
- Sleep/wake cycle and memory consolidation
- Internal clock (configurable; default 1 real hour = 1 IVA day)
- CLI for observing and interacting with the system

> These are simulated cognitive/emotional variables. They are not evidence of consciousness or real feelings.

## Run
Requires Python 3.10+.

```bash
python main.py
```

Commands: `status`, `event <text>`, `feedback <last-action> <good|bad|neutral>`, `sleep`, `wake`, `quit`.

No dataset is loaded. All changes come from runtime events and feedback.
