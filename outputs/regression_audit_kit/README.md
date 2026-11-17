# Directional regression audit kit

Use this to audit an update to a persistent skill (a robot controller, a policy, a prompt or a tool) against the behaviour the skill already had. It accompanies the paper *Repair Without Regression?* and implements its protocol in one dependency-free Python file, [`regaudit.py`](regaudit.py).

**The idea in one sentence:** count the old successes an update breaks separately from the ones it fixes, and check new updates first on the old behaviours that past updates broke.

## The protocol

1. **Certify replay.** Run the unchanged parent twice over the same ordered scene sequence (`replay_check`). If it reproduces exactly, every success-to-failure flip after an edit is caused by the edit, not by reset noise. Parent runs can then be shared across candidates.
2. **Pair and split.** Run each candidate on the same scenes. Report old-scene losses L and gains G separately, with the conditional loss (losses ÷ parent successes) and a Wilson interval (`directional`).
   - Net change is G − L. It depends on how many parent failures the panel contains, so do not gate on it alone.
3. **Calibrate with a null proposer.** Generate seeded random edits from the same bounded interface (`null_population`) and audit them the same way. Their losses are the baseline any real proposer, such as an agent, should be compared against.
4. **Keep a loss history.** Record which old successes each audited edit broke (`loss_history`). The scenes broken most often form a small history suite (`history_suite`).
5. **Gate, then audit.**
   - Admit a new edit only if it improves the target and loses nothing on the history suite (`zero_loss_gate`).
   - Commit the decision before running the full audit, then run the full audit to measure what the gate missed.

In the paper's robot study, an 8-scene suite built from earlier edits' losses caught a held-out edit's regressions far more often than 8 random old scenes. That finding was exploratory (leave-one-out on Extension 1). The paper reports its pre-registered test on new edits, Extension 2.

## Data format

One record per rollout:

```python
{'config': 'parent' or an edit id, 'scene': 'scene id', 'success': 0 or 1}
```

`outcomes(records, config)` turns these into a `{scene: 0/1}` map. Mark which scenes are old (previously solved behaviour) and which are target (the failure being repaired). Keep the same scene IDs across configurations.

## Applying it to your own system

```python
import regaudit as ra

parent  = run(parent_config, scenes)            # your simulator or test harness -> {scene: 0/1}
parent2 = run(parent_config, scenes)
assert ra.replay_check(parent, parent2)['exact']   # otherwise add repeats and model noise

eligible = [s for s in old_scenes if parent[s]]  # old behaviours the parent has
history = []                                     # lost-scene sets of past audited edits
for edit in incoming_edits:                      # e.g. agent proposals, or ra.null_population(...)
    suite = ra.history_suite(ra.loss_history(history), eligible, k=8, seed=0)
    small = run(edit, target_check + suite)      # cheap pre-check
    decision = ra.zero_loss_gate(parent, small, target_check, suite)   # commit before the audit
    full = run(edit, scenes)                     # full audit
    history.append(set(ra.directional(parent, full, old_scenes)['lost']))
```

## Try it without a simulator

```bash
python example_synthetic.py          # SYNTHETIC demo data, not robot results
python -m unittest -v test_regaudit.py
```

## Limits

- **Exact replay.** The cheapest version of this protocol needs exact parent replay. Without it, repeat each scene and treat flips statistically.
- **Fixed panel.** A loss history is defined over a fixed set of old scenes. It helps when updates keep being checked against the same behaviours. When the panel is redrawn, it has to be rebuilt.
- **One case.** The evidence behind it is one robot, one task and one repair context, with seeded random edits and two assistant-proposed repairs. Check that the pattern holds in your own system before relying on it.
- **No guarantees.** Zero observed losses on a small suite is not a safety guarantee.
