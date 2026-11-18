# Extension 3 report: do real AI agents' repairs break old successes?

**Status:** complete. Pre-registered test. The protocol (`robot_repair_study/extension3_protocol.md`) and 14 file hashes were frozen and pushed (commit `233a812`) before any agent was called. The proposals and transcripts were hashed and pushed (commit `e549b29`) before any Extension 3 rollout. The post-hoc sensitivity script was committed (`7ec3567`) before the queue finished.

**Bottom line.**
- **Every agent repair worked, and every one broke something.**
  - The 16 valid proposals reduce to 7 distinct edits. All 7 fixed target scenes: 5 to 20 of the 20 that the original controller fails.
  - All 7 also broke 2 to 6 of the 73 old scenes that the original controller solves. No agent produced a loss-free repair.
  - All 7 still solved more scenes overall, because each also rescued 6 to 9 old failures.
  - Pooled with the 50 earlier edits, 28 of 28 target-improving edits broke old successes (Wilson 95% interval 88–100%). The frozen analysis counts the 4 copies twice; counted as distinct parameter settings, it is 24 of 24, which is what the paper reports.
- **P1 is supported by its pre-registered criterion.** The 8-scene history suite, built from the 50 earlier edits, caught a loss in 6 of 7 lossy agent edits (0.86). An 8-scene uniform suite is expected to catch 0.39.
  - The difference is +0.47, 95% bootstrap CI [0.12, 0.68]. The lower bound is above 0.
- **Main caveat.** 4 of the 7 distinct edits are exact copies of earlier audited edits, and they reproduced those runs exactly.
  - A post-hoc leave-own-out check leaves P1 unchanged.
  - On the 3 genuinely new edits alone, the suite caught 2 of 3. That sample is too small to show anything.
- **Memory prompt.** Agents shown the loss history lost fewer old scenes per proposal: 2.9 vs 4.6, permutation p = 0.02. But 5 of their 8 proposals copied the same earlier edit, r44. Of the two edits in their table that fixed the whole target, r44 had 2 losses and r14 had 16. The memory prompt led agents to pick the best past edit, not to produce a new, safer one.

## 1. Run integrity

| Check | Result |
|---|---|
| Proposals | 20 requested: 5 agents × 2 conditions × 2 samples. 16 valid, all on the first attempt, with zero tool calls. 4 excluded (Gemini, see §2). |
| Batches | 8 of 8 complete: the parent plus 7 distinct edits. All exited 0, with no retries and no `failed*` folders. |
| Rollouts | 960 of 960 |
| Wall time | 07:09:09 to 08:52:50 UTC on Nov 18 (1 h 44 min). Proposals were collected 07:07–07:08 UTC. |
| Parent replay against Extension 1 | 120 of 120 audit labels agree, with identical final errors and step counts. This was a separate process, run days later. |
| Copied edits against their earlier runs (post hoc) | 4 of 4 agree on 120 of 120 labels, with identical final errors and step counts (`results/exploratory/ext3_copy_replay.json`) |
| Frozen-manifest checks | `analyze_ext3.py` asserts the runner snapshot hash and the manifest for every folder; all passed |

Detection is read from the audit itself, so the Extension 2 caveat about suite-batch versus audit order does not apply.

## 2. Agents and proposals

| Agent (CLI) | Blind prompt (2 samples) | Memory prompt (2 samples) |
|---|---|---|
| Claude Opus 5.5 (Claude Code 2.1.327) | lift 0.15; lift 0.15 | copy of r44 ×2 |
| Claude Sonnet 5.5 | lift 0.15; lift 0.20 + tolerance 0.022 | copy of r44 ×2 |
| Claude Haiku 5.5 | lift 0.20 (= candidate A); tolerance 0.022 | tolerance 0.033 (= r04); copy of r44 |
| GPT `gpt-6-astra` (Codex CLI 0.170.0) | tolerance 0.025 (= candidate B) ×2 | tolerance 0.022 ×2 |
| Gemini (Gemini CLI 0.68.0) | excluded | excluded |

- **r44.** Position tolerance 0.03 with grasp tolerance 0.019. It is row 46 in the memory prompt's table. "Tolerance" means `position_tolerance`.
- **Gemini.** Google rejected the free personal tier ("IneligibleTierError"). Per the frozen exclusion rule, it contributes no proposals. All 8 failed attempts are recorded in `proposals/ext3/transcripts/`.
- **GPT model name.** The Codex CLI does not report a model name in its output. The model recorded is the one requested.
- **Deduplication.** Of the 16 valid proposals, 9 duplicate another proposal and 0 are no-ops, which leaves 7 distinct edits.
  - **Copies.** Four distinct edits match earlier audited edits exactly: candidate A, candidate B, r04 and r44.
  - **New.** Three are new: lift 0.15; lift 0.20 + tolerance 0.022; tolerance 0.022.
  - **Convergence.** Blind agents twice rediscovered the two original repair candidates. Memory-prompted agents mostly copied r44. In the table they were given, two edits fixed all 20 target failures: r44 lost 2 old successes and r14 lost 16. Two other edits lost only 1 each, but each fixed a single target scene.

## 3. Distinct edits on the audit panel

The parent solves 10 of 30 target scenes and 73 of 90 old scenes.

| Edit (first proposal) | Overrides | Target net | Old lost | Old gained | Caught by history-8 | Uniform-8 expected |
|---|---|---|---|---|---|---|
| opus_b1 (new) | lift 0.15 | +5 | 4 | 8 | yes | 0.38 |
| opus_m1 (= r44) | tolerance 0.03, grasp 0.019 | +20 | 2 | 8 | yes | 0.21 |
| sonnet_b2 (new) | lift 0.20, tolerance 0.022 | +18 | 6 | 9 | **no** | 0.51 |
| haiku_b1 (= A) | lift 0.20 | +5 | 6 | 8 | yes | 0.51 |
| haiku_b2 (new) | tolerance 0.022 | +14 | 5 | 6 | yes | 0.45 |
| haiku_m1 (= r04) | tolerance 0.033 | +19 | 3 | 9 | yes | 0.30 |
| gpt_b1 (= B) | tolerance 0.025 | +17 | 4 | 7 | yes | 0.38 |

- **Usefulness.**
  - Under the aggregate objective (target net > 0 and old net ≥ 0): all 7 edits.
  - Under the zero-loss objective: none.
  - Under the 5% tolerance: 2 (r44 and r04).
- **Comparison with earlier edits.** Mean conditional loss among target improvers was 5.9% for the agents and 7.1% for the 21 earlier improvers.

## 4. Primary result (P1)

| Suite, 8 scenes | Caught at least one loss (n = 7 lossy distinct edits) |
|---|---|
| History suite, built from the 50 earlier edits | **6 / 7 = 0.86** |
| Uniform suite, hypergeometric expectation | 0.39 |
| Difference, 95% bootstrap CI (10,000 resamples, seed 20261132) | **+0.47 [0.12, 0.68]** |

There were 7 lossy distinct edits, above the frozen minimum of 5, so H1 was tested. It is supported because the lower bound is above 0.

**Secondary results (frozen).**
- **k = 4.** The history suite caught 5 of 7 (0.71); the uniform expectation is 0.22. The difference is +0.50 [0.15, 0.81].
- **Extension 2's history suite** (built from 26 edits, 8 scenes): 5 of 7 (0.71). The difference is +0.32 [−0.05, 0.66]. The CI includes 0.
- **Concentration.** 13 of the 30 losses (43%) fell on the 8 history scenes, against 11% expected if losses were spread uniformly.
- **The miss.** sonnet_b2 combines a lower lift with a looser tolerance. All 6 of its losses fall on scenes outside the suite. Two of them, ao073 and ao078, are also lost by the other new lower-lift edit, opus_b1, which the suite caught through a single scene (ao064).

## 5. Sensitivity to the copied edits (post hoc)

This analysis was written before the queue finished and is labelled post hoc (`explore_ext3_insample.py`, output `results/exploratory/ext3_insample.json`).

| Variant | n | Caught | Uniform expected | Difference, 95% CI |
|---|---|---|---|---|
| Frozen P1 | 7 | 0.86 | 0.39 | +0.47 [0.12, 0.68] |
| Leave-own-out: each copy scored against a suite rebuilt without its own earlier edit | 7 | 0.86 | 0.39 | +0.47 [0.12, 0.69] |
| New edits only | 3 | 0.67 | 0.45 | +0.22 [−0.51, 0.62] |

- **Leave-own-out.** No copy's detection depended on its own earlier losses. Each copy also broke a scene that many other earlier edits broke, mostly ao002 and ao020.
- **New edits only.** Three edits are too few to support or reject anything.
- **Interpretation.** The agents did not explore far from the earlier edits. Their repairs land in the same few edit families, so they break the same near-threshold scenes. That is why a history suite works here, and it is also why this test is not a test on unfamiliar edits.

## 6. Memory versus blind prompt (S2, frozen; proposals as units)

| Condition | Proposals | Mean old lost | Mean old gained | Mean target net | Loss-free improvers |
|---|---|---|---|---|---|
| Blind | 8 | 4.6 | 7.6 | +10.8 | 0 |
| Memory | 8 | 2.9 | 7.6 | +18.4 | 0 |

- **Test.** Permutation p = 0.02 for the mean old loss.
- **Distinct edits.** The 8 memory proposals contain only 3 distinct edits, and 5 of the 8 are the same copy of r44. The 8 blind proposals contain 5 distinct edits.
- **Reading.** The p-value treats agent sessions as independent. It mostly reflects agents converging on the best trade-off in the table they were shown.
- **What the agents said (descriptive, not pre-registered).**
  - Memory-prompted agents named the right risk: release up to 3 cm off target leaves the cube just outside the goal.
  - None of the four blind lift-only proposals anticipated losing old placements (one gave no risk statement), and one expected passing scenes to be "largely unaffected". Those edits lost 4 to 6 old successes.

## 7. What this adds and what it does not

- **Adds.**
  - The paper's central observation now holds for edits proposed by real AI agents, not only seeded random edits. Four models from two vendors, each given the failure and the controller source, all proposed repairs that broke old successes.
  - The history suite, built only from earlier edits, caught 6 of 7.
- **Does not show.**
  - That history suites generalize to edits unlike past ones. 4 of 7 edits were exact copies, and the 3 new ones are too few.
  - That a memory prompt makes agents safer. It made them copy.
- **Scope.** One robot, one task, one panel and one repair context. There is one prompt per condition. The agents could not run the simulator. Gemini was unavailable.

## Files

- **Protocol and hashes:**
  - `extension3_protocol.md`;
  - `extension3_frozen_hashes.json`;
  - `ext3_proposal_hashes.json`.
- **Materials:** `make_ext3_materials.py` → `ext3_suites.json`, `ext3_prompts/{blind,memory}.md` and `ext3_agents.json`.
- **Proposals:** `run_ext3_agents.py` → `proposals/ext3/` (index, configs, transcripts).
- **Queue and results:**
  - queue: `scripts/run_extension3.ps1`;
  - results: `results/ext3/`, with ledger `results/ext3/ext3_batch_ledger.json`.
- **Frozen analysis:** `analyze_ext3.py` → `results/ext3/ext3_analysis.json`.
- **Post hoc:**
  - `explore_ext3_insample.py` → `results/exploratory/ext3_insample.json`;
  - `explore_ext3_copy_replay.py` → `results/exploratory/ext3_copy_replay.json`.
