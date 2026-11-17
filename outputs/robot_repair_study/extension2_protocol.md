# Extension 2: do loss histories predict future regressions? (frozen protocol)

**Frozen:** November 16, 2026, before any Extension 2 rollout. SHA-256 values of every file listed in §8 are in `extension2_frozen_hashes.json`, recorded at freeze time and committed to the project repository before launch.

**Status:** a *confirmatory* test of a hypothesis generated post hoc from Extension 1 data (§9). It is reported as an add-on; it does not change the first audit or Extension 1. Designed by Claude at the user's request.

## 1. Question and hypotheses

Different edits to the same controller appear to break the *same* fragile old scenes. If so, an evolving agent can record which old successes past updates broke, and check those first. Then a small regression check catches more of a new update's losses than a randomly chosen check of the same size.

- **H1 (primary).** Among new candidates with at least one audit loss, an 8-scene *history suite* detects at least one loss (in its suite batch) more often than an 8-scene *uniform* suite is expected to.
  - **Test.** Paired over candidates: mean of (history detection, 0/1) minus (uniform expected detection), with a bootstrap 95% CI over candidates (10,000 resamples, seed 20261125).
  - **Criterion.** H1 is supported if and only if the CI's lower bound is above 0. This is fixed before data collection.
- **Secondary questions** (reported regardless of outcome):
  - the realized uniform suite (exact McNemar test);
  - the k = 4 version;
  - whether new losses concentrate on the history suite;
  - gate admissions with audit losses, and missed useful candidates;
  - agreement between suite-batch and audit outcomes;
  - parent replay against Extension 1.

## 2. Candidates

- **What.** 24 new seeded random edits, `r25`–`r48`, written to `proposals/ext2/` by `make_ext2_materials.py` (seed 20261121).
- **Generator.** The same rules as Extension 1 (`make_random_proposals.py`):
  - k ∈ {1, 2} parameters with equal probability;
  - parameters chosen uniformly without replacement from the six-parameter interface;
  - each value uniform within the runner's bounds, rounded to 3 decimals.
- **Status.** None has ever been run.
- **Labelling.** They form a non-agent proposal distribution and say nothing about proposer quality. No assistant candidates are included.

## 3. Regression panel and suites

- **Panel.** The Extension 1 audit panel (`ext1_audit_scenes.json`, 30 target + 90 old scenes) is reused *by design*: a loss history is defined over a fixed set of old scenes. The unit of replication is the new edit, not the scene.
- **Construction.** Suites are built only from data recorded before Extension 2: the Extension 1 audit parent and the 26 Extension 1 candidate audits. The 73 old scenes the parent solved are the eligible pool.
- **History suite.** The 8 eligible scenes most often lost by the 26 Extension 1 candidates; ties are broken by a seeded random order (seed 20261122).
  - Members, with Extension 1 loss counts: ao083 (10), ao052 (9), ao020 (9), ao002 (7), ao018 (7), ao048 (6), ao001 (6), ao034 (5).
  - Its first 4 form the k = 4 secondary suite.
- **Uniform suite.** 8 eligible scenes drawn uniformly without replacement (seed 20261123).
  - Members, with Extension 1 loss counts: ao005 (1), ao014 (0), ao024 (2), ao027 (2), ao028 (0), ao056 (4), ao057 (2), ao077 (1).
  - It does not overlap the history suite.
- **Record.** Both suites are written to `ext2_suites.json`.

## 4. Suite (validation) batch

`ext2_validation_scenes.json` contains:
- the Extension 1 validation targets vt01–vt04;
- the 16 suite scenes;
- 20 scenes in total, in one shuffled order (seed 20261124) shared by all configurations.

The parent runs this batch once; its rollouts are shared by all candidates.

## 5. Gates (committed before any audit rollout)

`ext2_gates.py` writes `results/ext2/ext2_gate_decisions.json` after all suite batches. Every gate is zero-loss, paired against the suite-batch parent, and spends 4 target + k old pairs.

| Gate | Admits when |
|---|---|
| `history_gate` | target net > 0 on vt01–vt04, ≥ 1 parent success in the history suite, and zero history-suite losses |
| `uniform_gate` | the same, using the uniform suite |
| `history4_gate` | the same, using the k = 4 history suite (secondary) |
| `target_gate` | target net > 0 (reference) |

## 6. Audit and analyses (`analyze_ext2.py`)

**Audit.** The parent and each candidate run the full 120-scene Extension 1 panel in its original order.

**Definitions.**
- **Losses** are relative to the Extension 2 audit parent: old parent successes that the candidate fails.
- **Usefulness** uses the same objectives as before, measured on the full audit:
  - aggregate: target net > 0 and old net ≥ 0;
  - zero-loss: target net > 0 and no losses;
  - secondary: conditional loss ≤ 5%.

**Primary (P1).**
- **History detection** is read from the suite batch: at least one loss among the history-suite scenes.
- **Uniform expected detection** is 1 − C(n − m, 8) / C(n, 8), where n is the number of old parent successes and m the candidate's audit losses.

**Secondary.**
- **S1.** Realized uniform-suite detection in the suite batch, with an exact McNemar test against history detection.
- **S2.** The k = 4 versions, plus the expected detection of current practice: 8 old scenes drawn uniformly from all 90, including parent failures.
- **S3.** The share of all new losses that fall on the history suite, against 8/n.
- **Admissions.** Per gate: admitted candidates, those with audit losses, total audit losses among them, and admitted and missed useful candidates.
- **S4.** Agreement between suite-batch and audit outcomes on the 16 suite scenes, for candidates and the parent.
- **S5.** Replay: the Extension 2 audit parent against the Extension 1 audit parent (120 labels); the validation parent repeat against the validation parent.

**Exploratory, labelled as such.** Leave-one-out history suites built from the new population alone, and from Extension 1 plus the new population.

**Uncertainty.** Intervals cover candidates drawn from this proposal distribution, on one panel, robot, task and context.

## 7. Execution (`work/run_extension2.ps1`)

**Order:**
1. Suite batches: parent, then r25–r48 (25 × 20 rollouts).
2. Gate commit.
3. Audits: parent, then r25–r48 (25 × 120 rollouts).
4. Validation parent repeat (20 rollouts).

That is 3,520 rollouts in total, about 6.5 hours serial.

**Launch and failure handling.** Same as Extension 1:
- the timeout launcher allows 40 minutes per suite batch and 150 minutes per audit batch;
- a failed batch is renamed `failed<n>_<name>` and rerun whole, once;
- a candidate whose suite batch fails twice is excluded from the gates;
- a candidate whose audit fails twice is excluded from the analysis and reported;
- the queue is resumable and never overwrites;
- an idle-sleep request is held while it runs.

**Ordering guarantee.** No result triggers any change.

**Dry run.** The pipeline was dry-run end to end on clearly labelled synthetic stand-in data (scratch directory, not part of the results). The dry run found and fixed one bug before freezing: PowerShell 5.1 counted the manifest as one scene.

## 8. Frozen files

- **Protocol and materials:** this protocol; `make_ext2_materials.py`; `proposals/ext2/*`; `ext2_suites.json`; `ext2_validation_scenes.json`.
- **Gate and analysis scripts:** `ext2_gates.py`; `analyze_ext2.py`.
- **Queue and simulator:** `work/run_extension2.ps1`; `work/launch_isaac_ps51_timeout.ps1`; `run_stock_scene.py`.
- **Inputs:** `ext1_audit_scenes.json`; `ext1_validation_scenes.json`.
- **Exploratory scripts:** `explore_margin.py`; `explore_history.py`; `explore_history_strict.py`.
- **Exploratory outputs:** `results/exploratory/*`.

## 9. What was known before freezing

These are exploratory, post-hoc analyses of Extension 1 data; outputs are in `results/exploratory/`, generated Nov 17 05:48 UTC.

**Parent margin (`margin.json`).**
- For the two assistant repairs in the first audit, a smaller parent placement margin predicted losses (AUC 0.81).
- For the 26 Extension 1 candidates, it did not (pooled AUC 0.49).
- This idea is not pursued.

**Loss history (`history_loo.txt`, `history_loo_strict.txt`).** In Extension 1:
- the 10 most-lost scenes (14% of parent successes) carried 42% of the 163 losses;
- lost sets overlapped about 2.3× more than chance (mean Jaccard 0.104 against 0.045).

Leave-one-candidate-out detection of at least one loss, out of 23 candidates with losses:

| Suite size | History suite (all other edits) | History suite (edits sharing no parameter) | Uniform expectation |
|---|---|---|---|
| 4 | 0.83 | 0.78 | 0.33 |
| 8 | 0.91 | 0.91 | 0.53 |

These numbers motivated H1. Extension 2 tests H1 on edits that did not exist when the suite was built.
