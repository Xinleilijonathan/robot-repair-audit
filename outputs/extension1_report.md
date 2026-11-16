# Extension 1: candidate-population audit (results)

**Status:** complete, Nov 15, 2026, 23:39 local. **Post-hoc:** designed after the first audit's results were known, and reported as an add-on that does not amend the first audit. Protocol: `robot_repair_study/extension1_protocol.md`, frozen 16:47:22 (39 files, SHA-256 in `extension1_frozen_hashes.json`; all 39 re-verified unchanged after the run).

**Evidence label:** one robot, one task, one repair context. The 24 random candidates are a seeded non-agent proposal distribution. Intervals describe this proposal distribution and these scene populations only.

## Run integrity

- **Rollouts.** 3,800 of 3,800 completed: 27 × 20 validation, 27 × 120 audit, plus a 20-rollout parent repeat. The run took 16:47–23:39.
- **Failures.** Every batch exited 0 on its first attempt. There are no `failed*` folders, and no candidate was excluded.
- **Gate commit.** `results/ext1/audit_gate_decisions.json` was written at 01:50:01 UTC. The first audit batch started at 01:50:04 UTC.
- **Parent repeat.** The end-of-queue validation parent repeat matched on 20/20 outcomes, with a maximum final-error difference of 0.0 m and no step-count mismatches.
- **Interim look (disclosure).** At about 22:54 local, at the user's request, I printed a read-only tally of the 23 completed candidate audits using the frozen helper functions. Nothing was written, and no queue, gate, analysis or protocol element changed. The queue was fixed in advance and has no adaptive step, so the look could not affect any result.

## Outputs

- `results/ext1/audit_analysis.json`: frozen `analyze_audit.py`, all 26 candidates in queue order.
- `results/ext1/population_analysis.json`: frozen `analyze_population.py`, with `--first-audit`.
- Figure: `paper/fig_population.pdf` and `outputs/population_map.png`, from `plot_population.py`.
- Table: `paper/population_table.tex`, from `paper/make_population_table.py`.

## Audit panel

- **Panel.** 30 target and 90 old scenes.
- **Parent.** 10/30 target successes; 73/90 old successes.
- **Parent target failures.** Lift stalls and approach timeouts.
- **Parent old failures (17).**

  | Mode | Count |
  |---|---|
  | Interior placement failures, parent error 3.0–4.5 cm | 8 |
  | Approach timeouts at r ≥ 0.80 m | 7 |
  | Lift stalls | 2 |

## Per-candidate audit outcomes

Target is parent → candidate, out of 30. Old gain and old loss are out of the parent's 17 failures and 73 successes respectively. Gates show the committed validation decisions: A = admit, - = reject.

| id | edit | target | old gain | old loss | agg | pres | t-only | P(agg) − P(pres) |
|---|---|---|---|---|---|---|---|---|
| candidate_a | lift 0.20 | 10→15 | 8 | 6 | A | A | A | 0.106 |
| candidate_b | pos tol 0.025 | 10→27 | 7 | 4 | A | A | A | 0.119 |
| r01 | approach 0.152 | 10→11 | 7 | 8 | - | - | A | 0.025 |
| r02 | grasp tol 0.012 | 10→10 | 0 | 0 | - | - | - | 0 |
| r03 | lift 0.397, pos tol 0.026 | 10→0 | 6 | 6 | - | - | - | 0 |
| r04 | pos tol 0.033 | 10→29 | 9 | 3 | A | A | A | 0.120 |
| r05 | approach 0.397, dwell 0.21 | 10→0 | 5 | 7 | - | - | - | 0 |
| r06 | approach 0.073, grasp tol 0.011 | 10→11 | 8 | 3 | - | - | A | 0.014 |
| r07 | pos tol 0.012, dwell 0.749 | 10→2 | 8 | 3 | - | - | - | 0 |
| r08 | lift 0.395 | 10→0 | 7 | 10 | - | - | - | 0 |
| r09 | dwell 0.134 | 10→10 | 5 | 3 | - | - | - | 0 |
| r10 | approach 0.156 | 10→11 | 8 | 10 | - | - | A | 0.033 |
| r11 | stability 0.267 | 10→8 | 8 | 9 | - | - | - | 0 |
| r12 | lift 0.361, pos tol 0.009 | 10→0 | 5 | 10 | - | - | - | 0 |
| r13 | grasp tol 0.021 | 10→10 | 0 | 0 | - | - | - | 0 |
| r14 | approach 0.178, pos tol 0.026 | 10→30 | 10 | 16 | A | - | A | 0.295 |
| r15 | approach 0.249, grasp tol 0.025 | 10→10 | 8 | 14 | - | - | - | 0 |
| r16 | grasp tol 0.026 | 10→10 | 0 | 0 | - | - | - | 0 |
| r17 | approach 0.394 | 10→0 | 6 | 5 | - | - | - | 0 |
| r18 | dwell 0.896 | 10→11 | 7 | 2 | - | - | A | 0.010 |
| r19 | approach 0.062, grasp tol 0.018 | 10→11 | 7 | 5 | - | - | A | 0.021 |
| r20 | grasp tol 0.006, dwell 0.44 | 10→10 | 6 | 15 | - | - | - | 0 |
| r21 | approach 0.325 | 10→5 | 7 | 3 | - | - | - | 0 |
| r22 | stability 0.164 | 10→10 | 5 | 5 | - | - | - | 0 |
| r23 | approach 0.244 | 10→9 | 7 | 12 | - | - | - | 0 |
| r24 | lift 0.105, dwell 0.202 | 10→15 | 9 | 4 | A | A | A | 0.087 |

## Pre-registered questions

### Q1. Do target improvements cost old successes?

Every target improvement came with old losses:
- 10 of 26 candidates improve the target, and all 10 lose at least one old success (10/10, Wilson 95% interval 0.72–1.00).
- Their 61 losses are all placement regressions ("did not settle"), at radii 0.35–0.79 m.
- Across all candidates there are 163 old losses, none at r ≥ 0.80 m.
- Losses by candidates that do not improve the target include timeouts: approach, lift and grasp. r20 (grasp tolerance 0.006) accounts for all 14 grasp-timeout losses.

### Q2. How often do gains offset losses, and do the gates disagree?

- **Gains and losses together.** 23 of 26 candidates both gain and lose old scenes. The 3 exceptions are r02, r13 and r16, which edit only the grasp tolerance and reproduce the parent on all 120 scenes.
- **Offsetting gains.** 13 candidates gain at least as many old scenes as they lose (losses > 0).
- **Committed aggregate-vs-preservation disagreements.** There is 1: r14.
- **Resampled disagreement.** The mean is 0.032 over candidates and the maximum is 0.295 (r14).

### Q3. How does each gate perform?

All three gates delivered candidate_b (on the audit: target 27/30, old 76/90, 4 losses, 7 gains).

| Gate | Admitted | With losses | Total losses | Agg-useful admitted | Agg-useful missed | 5%-useful missed |
|---|---|---|---|---|---|---|
| Target-only | 10 | 10 | 61 | 7 | 0 | 0 |
| Aggregate | 5 | 5 | 33 | 4 | 3 (r06, r18, r19) | 2 (r06, r18) |
| Preservation | 4 | 4 | 17 | 4 | 3 (r06, r18, r19) | 2 (r06, r18) |

- **Useful counts.** Aggregate objective: 7 (A, B, r04, r06, r18, r19, r24). Zero-loss objective: 0. 5% conditional-loss tolerance: 3 (r04, r06, r18).
- **Target-only.** It admitted exactly the 10 target improvers, and admitted none that failed to improve the target.

### Q4. Do A and B replicate?

| | First audit (40 + 120) | Extension (30 + 90) |
|---|---|---|
| A target | 15→26/40 | 10→15/30 |
| A old gain / loss | 4 / 8 (net −4) | 8 / 6 (net +2) |
| A conditional loss | 7.5% [3.9, 14.2] | 8.2% [3.8, 16.8] |
| B target | 15→38/40 | 10→27/30 |
| B old gain / loss | 4 / 5 (net −1) | 7 / 4 (net +3) |
| B conditional loss | 4.7% [2.0, 10.6] | 5.5% [2.2, 13.3] |

- **What replicated.** The target improvements and the conditional loss rates.
- **What did not.** The sign of the old net change did not replicate.
- **Where the extra gains come from (descriptive, post hoc).** Most of A's and B's extension gains are interior parent placement failures that settle just outside the 3 cm tolerance: 7 of A's 8 gains and 5 of B's 7. This draw has 8 such scenes among 90 old scenes, against 4 among 120 in the first audit.

## Paper changes

`paper/main.tex` changes:

- **New section.** Adds "Post-hoc Extension: A Candidate Population", containing Figure 2 and Table 4.
- **Other sections.** Updates the abstract, the contribution list, the Discussion bullets and the Limitations.
- **First audit.** Its sections are unchanged.
- **Length.** The paper compiles to 5 pages: a 4-page body, with references starting on page 4 and ending on page 5.
- **Open item.** If the venue counts references toward the 4-page limit, the paper must be cut by about half a column. This needs organizer confirmation.
