# Frozen single-context audit: results

November 15, 2026. The queue ran 15:07–16:08 America/Los_Angeles: 560 rollouts in 61 minutes, every batch with exit code 0. The protocol is `robot_repair_study/audit_protocol.md`, with one infrastructure-only change (`audit_amendment_1.md`). All numbers below come from three generated files:

- `results/audit_gate_decisions.json`, written by `audit_gates.py`
- `results/audit_analysis.json`, written by `analyze_audit.py`
- `audit_map.png`, written by `plot_audit_map.py`

This is evidence for **one repair context, two fixed candidates**. Intervals are Wilson 95% intervals over scenes for that context only.

## Integrity

- **Validation batches.** Three batches of 20 rollouts each completed cleanly.
- **Gate decisions** were written at 23:14:22.31 UTC; the first audit rollout appeared at 23:14:44.86 UTC.
- **Audit batches.** Three batches of 160 rollouts each completed cleanly.
- **Parent repeat.** Re-running the validation parent reproduced 20/20 outcomes, with a maximum error difference of 0.0 m and identical step counts.
- **Hashes.** Every frozen file still matches its hash. The queue script matches its amendment-1 hash. Each stderr file contains only the known carb version warning.

## Results

| | Target /40 | Old /120 | Old gain | Old loss | Old net | Conditional loss [95% CI] |
|---|---|---|---|---|---|---|
| Parent | 15 | 106 | — | — | — | — |
| A (lift 0.20 m) | 26 | 102 | 4 | 8 | −4 | 7.5% [3.9, 14.2] |
| B (tolerance 0.025 m) | 38 | 105 | 4 | 5 | −1 | 4.7% [2.0, 10.6] |

### Target neighbourhood

- **Where the parent succeeds.** The parent already succeeds on 15 of 40 target-neighbourhood scenes (r ~ U[0.79, 0.81], a ~ U[−62°, −58°]), all at r < 0.80 m.
- **Two failure modes.** The parent's 25 failures are 11 LIFT stalls and 14 APPROACH_PICK timeouts. The development target showed only the LIFT stall.
- **A** fixes 11/11 lift stalls and 0/14 approach timeouts.
- **B** fixes 11/11 lift stalls and 12/14 approach timeouts. Its two remaining failures now stall in LIFT.
- **By radius:**
  - r ∈ [0.79, 0.80): parent 15/25, A 25/25, B 25/25.
  - r ∈ [0.80, 0.81): parent 0/15, A 1/15, B 13/15.

### Old scenes

- **Parent failures.** The parent fails 14 old scenes: 9 APPROACH_PICK timeouts (all at r ≥ 0.80 m), 4 placement near-misses and 1 LIFT stall.
- **Losses** occur at r = 0.36–0.73 m, in the workspace interior and away from the repaired boundary. Every loss is a placement regression: the parent's errors of 1.3–3.0 cm become 3.0–4.7 cm.
- **Gains** are mostly parent placement near-misses; one boundary LIFT stall is gained by both candidates, and B also gains one APPROACH_PICK timeout.
- **Margin shift.** On the 106 parent old successes, A makes placement worse by more than 5 mm on 19 scenes and better on 10. B is worse on 12 and better on 30.
- **Tolerance sensitivity** (approximate):

  | Tolerance | A old loss / gain | B old loss / gain |
  |---|---|---|
  | 2.0 cm | 14 / 7 | 8 / 13 |
  | 3.0 cm (frozen) | 8 / 4 | 5 / 4 |
  | 4.0 cm | 2 / 1 | 3 / 2 |

  Unlike in development, the losses do **not** vanish at 4 cm.

### Usefulness (declared before the audit)

- **Aggregate objective** (target net > 0 and old net ≥ 0): neither candidate is useful. B misses by one scene (old net −1).
- **Zero-loss objective:** neither candidate is useful.
- **Secondary 5% tolerance:** B is useful (4.7%); A is not (7.5%).

### Gates (committed from the validation draw)

| Gate | A | B | Delivered | Target /40 | Old /120 | Old losses |
|---|---|---|---|---|---|---|
| Frozen | — | — | parent | 15 | 106 | 0 |
| Target-only (12 target pairs) | admit (1→5) | admit (1→12) | B | 38 | 105 | 5 |
| Aggregate (4 target + 8 old pairs) | reject | reject | parent | 15 | 106 | 0 |
| Preservation (same pairs, zero loss) | reject | reject | parent | 15 | 106 | 0 |

- **Validation evidence.** On the target pairs, A went from 0/4 to 2/4 and B from 0/4 to 4/4. On the 8 old pairs, each candidate lost one scene (vo02 under A, vo07 under B, both placement shifts) and gained none. Old net was therefore −1 for both, and aggregate and preservation both rejected.
- **Secondary objective.** Under the 5% tolerance, frozen, aggregate and preservation all miss B, while target-only delivers it.
- **Decision stability** (diagnostic, 5,000 validation-sized resamples from the audit pools):

  | Gate | P(admit A) | P(admit B) |
  |---|---|---|
  | Target-only | 0.99 | 1.00 |
  | Aggregate | 0.47 | 0.74 |
  | Preservation | 0.41 | 0.68 |

  Aggregate and preservation disagree in only 6.4% (A) and 5.8% (B) of draws.

## Development vs audit

- **The pilot's pattern did not replicate.** The pilot's "compensated regression" pattern (aggregate admits, preservation rejects) did not appear on fresh scenes.
- **Why: panel composition.** 9 of the 24 development old scenes lay at r ≥ 0.80 m, and four of them shared the target's LIFT stall. They supplied 9 of A's 10 and 12 of B's 13 development gains. Uniform sampling of the same region puts only 10 of 120 old scenes at r ≥ 0.80 m. A panel built around the failure under repair over-represents that failure's family, and so inflates compensating gains.
- **Paper-relevant conclusions for this case:**
  1. Panel composition determines whether aggregate and zero-loss admission disagree.
  2. When gains are rare, the two rules nearly coincide at a 12-pair budget; what changes the delivered controller is whether old scenes are checked at all.
  3. Whether B (+23 target, −1 old net, 5 losses) should ship depends on a loss tolerance and a precision requirement that must be declared in advance.

## Not established

- **Scope.** There are no claims about agent competence, regression prevalence, which gate is better in general, other tasks or robots, or physical safety.
- **Proposals.** The candidates are interactive proposals, not samples from a frozen model, so nothing here measures proposer quality.
