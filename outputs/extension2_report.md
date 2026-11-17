# Extension 2 report: do loss histories predict future regressions?

**Status:** complete. This was a pre-registered, confirmatory test of a hypothesis generated post hoc from Extension 1 data. The protocol (`robot_repair_study/extension2_protocol.md`) and 42 file hashes were frozen and pushed (commit `1a49f07`) before the first rollout.

**Bottom line.** H1 is supported by its pre-registered criterion.
- **Detection.** Among the 20 new random edits that lost at least one old success on the full audit, the 8-scene loss-history suite detected a loss in 14 (70%). An 8-scene uniform suite is expected to detect 36%.
  - The difference is +0.34, 95% bootstrap CI [0.16, 0.51]. The lower bound is above 0.
- **Not shown.** A single realized uniform suite was not significantly worse (McNemar p = 0.09).
- **Practical cost.** As a zero-loss gate, the history suite became very strict. It cut admitted losses from 28 to 2 compared with a uniform suite, but rejected 9 of the 10 candidates that were useful under the aggregate objective.

## 1. Run integrity

| Check | Result |
|---|---|
| Batches | 51 of 51 complete, exit 0, no retries, no `failed*` folders |
| Rollouts | 3,520 of 3,520 |
| Wall time | 05:52:39 to 12:06:30 UTC on Nov 17 (6 h 14 min) |
| Gate commit | `committed_utc` 06:54:01.50, 0.2 s after the last suite batch ended. The first audit batch started at 06:54:03.55. |
| Parent replay against Extension 1 | 120 of 120 audit labels agree, with identical final errors and step counts. This is a separate process, about a day later. |
| Validation parent repeat | 20 of 20 agree, with identical final errors and step counts |
| Frozen-manifest checks | `analyze_ext2.py` asserts the runner snapshot hash, manifest and override match for every folder; all passed |

## 2. Population

- **Candidates.** 24 seeded random edits, r25–r48, on the Extension 1 audit panel: 30 target and 90 old scenes. The parent solves 73 old scenes and 10 of 30 target scenes.
- **No-op edits.** Four edits (r25, r27, r34, r45) reproduce the parent on all 120 labels with identical final errors. Each changes only the grasp tolerance, or the grasp tolerance plus a short dwell.
- **Lossy edits.** 20 edits lose at least one old success, 97 losses in total.
- **Target improvers.** 11 edits improve the target, and all 11 lose old successes (Wilson 95% interval 74–100%).
  - Pooled with Extension 1, 21 of 21 target-improving candidates lost old successes (Wilson 85–100%).
- **Useful candidates.**
  - Under the zero-loss objective: none in either population.
  - Under the aggregate objective: 10 of 24 (target net > 0 and old net ≥ 0).
  - Under the 5% tolerance: 6 of 24.

## 3. Primary result (P1)

| Suite, 8 scenes | Detected at least one loss (n = 20 lossy) |
|---|---|
| History suite, read from the suite batch | **14 / 20 = 0.70** |
| Uniform suite, hypergeometric expectation | 0.36 |
| Difference (bootstrap 95% CI, 10,000 resamples, seed 20261125) | **+0.34 [0.16, 0.51]**; H1 supported |

## 4. Secondary results (pre-registered, reported regardless of outcome)

- **S1. Realized uniform suite.** It detected 7 of 20 (0.35) in the suite batch.
  - History-only detections: 10. Uniform-only: 3.
  - Exact McNemar p = 0.092. This single uniform draw is not significantly worse than the history suite at α = 0.05.
- **S2. k = 4.**
  - The history suite detected 12 of 20 (0.60). The uniform expectation is 0.22, a difference of +0.38 [0.19, 0.57].
  - "Current practice", 8 old scenes drawn from all 90 including parent failures, is expected to detect 0.31.
- **S3. Concentration.** 31 of the 97 new losses (32%) fell on the 8 history scenes, which are 11% of the eligible pool. Only 6 (6%) fell on the uniform suite.
- **S4. Suite batch against audit.** The 20-scene suite batch runs scenes in a different order from the 120-scene audit.
  - On the 16 suite scenes, candidate outcomes agree in 367 of 384 labels (95.6%). Parent outcomes agree in 16 of 16. See §6.
- **S5. Replay.** Exact; see §1.

**Admissions**, all gates zero-loss, 24 rollouts each (12 for target-only). Audit losses are counted against 73 parent old successes.

| Gate | Admitted | Admitted with audit losses | Audit losses among admitted | Aggregate-useful admitted / missed | 5%-useful admitted / missed |
|---|---|---|---|---|---|
| Target-only | 8 | 8 | 31 | 8 / 2 | 4 / 2 |
| Uniform suite (k = 8) | 7 | 7 | 28 | 7 / 3 | 3 / 3 |
| History suite (k = 4) | 2 | 2 | 6 | 2 / 8 | 1 / 5 |
| History suite (k = 8) | 1 | 1 | 2 | 1 / 9 | 1 / 5 |

**What the gates did with specific edits:**
- **History gate.** It admitted only r48 (lift 0.24, dwell 0.191): target +5, with 2 old losses against 7 gains.
- **Uniform gate.** It admitted r28, r39, r40, r41, r44, r46 and r48, which lost 5, 7, 2, 4, 2, 6 and 2 old successes.
- **Target-only.** It also admitted r36 (target +17, 3 losses). The uniform suite caught r36.
- **Never admitted.** r30 and r42 each gained one target scene on the audit but none in the 4-scene target check, so no gate admitted them.

**Reading.**
- **What the suite buys.** Because no candidate in either population improved the target without losing something, a zero-loss gate can only keep the parent or admit a lossy edit. The history suite makes that gate do what its name says far more often.
- **What it costs.** Under an aggregate objective, it rejects most candidates that are worth deploying. Which behaviour is wanted depends on the declared loss tolerance, as in the main paper.

## 5. Exploratory (labelled in the protocol)

These are leave-one-candidate-out history suites, with the history-minus-uniform-expectation difference at k = 8:

| Pool | Difference, 95% CI |
|---|---|
| New population only | +0.44 [0.27, 0.60] |
| Extension 1 plus new | +0.49 [0.32, 0.64] |

## 6. Post-hoc analyses (not pre-registered, written after seeing S4)

**Scene outcomes depend on their position in the run.** This is `explore_ext2_agreement.py`, output in `results/exploratory/ext2_agreement.json`.
- **Parent.** The same scene run inside the 20-scene suite batch and inside the 120-scene audit gives final placement errors that differ by up to 12.4 mm (7 of 16 scenes differ). Its binary outcomes did not change.
- **Candidates.**
  - 17 of 384 suite-scene labels flip: 9 fail in the batch and succeed in the audit, and 8 the reverse.
  - The flips fall on 13 history-suite labels and 4 uniform-suite labels, across 11 candidates.
  - In every flip, the failing context left the cube 3.0–4.4 cm from the goal, a placement failure just outside the 3 cm tolerance. The succeeding context left it 0.4–2.9 cm away.
- **Consistency with the paper.** The paper already states that resets within one process differ slightly while an ordered sequence replays exactly across processes. These flips are that effect. Paired comparisons in the audit are unaffected, because parent and candidate share one order. A suite check run in its own batch, however, is an imperfect proxy for the audit.
- **Sensitivity.** Reading history detection from the audit instead of the suite batch gives 15 of 20 (0.75), a difference of +0.39 [0.21, 0.56].
  - In the audit, the realized uniform suite detects only 4 of 20 (0.20). Its three extra batch detections did not replicate. History-only: 11, uniform-only: 0, McNemar p = 0.001.
  - This is post hoc and does not replace the frozen result.

**Which scenes are lost.** This is `explore_ext2_scenes.py`, output in `results/exploratory/ext2_scenes.json`.
- **Rank agreement.** Per-scene loss counts in Extension 1 (26 candidates) and Extension 2 (24 new candidates) have a Spearman correlation of 0.42 over the 73 eligible scenes.
- **Top-ranked scenes.** The Extension 1 top-10 scenes (14% of the pool) carry 44% of the new losses, and the top-20 carry 65%.
- **Scenes Extension 1 never lost.** These 19 scenes (26% of the pool) carry 14 of the 97 new losses (14%).

## 7. What this does and does not show

**Shows.**
- In this robot, task and panel, the old scenes that past random edits broke are the scenes new random edits break.
- A suite built from that history detects a new edit's regressions about twice as often as a same-size uniform suite is expected to.

**Does not show.**
- That this holds for agent-proposed edits, other skills, or a redrawn panel.
- That a history gate is better. It is stricter, and costly under an aggregate objective.
- Any safety guarantee.

**Evidence base.** One robot, task, repair context and panel. The candidates are random edits from one bounded interface, and intervals cover only that proposal distribution.

## 8. Files

- **Raw results.** `results/ext2/`: 50 suite and audit batches plus the parent repeat, `ext2_batch_ledger.json` and `ext2_gate_decisions.json`.
- **Frozen analysis.** `results/ext2/ext2_analysis.json`, produced by `analyze_ext2.py` (frozen).
- **Post hoc.** `results/exploratory/ext2_agreement.json` and `ext2_scenes.json`, produced by `explore_ext2_agreement.py` and `explore_ext2_scenes.py`.
