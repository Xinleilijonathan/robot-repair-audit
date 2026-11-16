# Frozen single-context audit protocol

Frozen November 15, 2026, ~15:05 America/Los_Angeles, before any audit or validation rollout. These files are SHA-256 hashed in `audit_frozen_hashes.json` before launch:

- this protocol
- both manifests
- `make_audit_manifest.py`, `audit_gates.py`, `analyze_audit.py`, `audit.py`, `run_stock_scene.py`
- the two proposal JSONs
- the queue script

Any change after launch requires a dated amendment and a new, untouched audit. This audit was designed by Claude, continuing the Codex-run pilot. No new candidate proposals are generated: only the two frozen proposals A and B are evaluated.

## 1. Purpose and scope

The audit uses scenes not used in development. For the single repair context `r80_a-60` it measures:

- (a) whether each candidate's target repair carries over to the target's neighbourhood;
- (b) old-scene gains and losses on fresh draws from the development workspace;
- (c) what budget-matched gates decide on a small validation draw committed before the audit runs, and how those decisions fare on the withheld audit.

It is a **case study**: 1 robot, 1 task, 1 repair context, 2 interactively generated candidates. It cannot estimate how often repairs regress in general, measure agent competence, or certify safety.

## 2. Fixed elements

- **Controller and runner.** Stock NVIDIA Franka pick-and-place controller via `run_stock_scene.py` (runner SHA-256 `b0982ed0…3c58`).
- **Evaluator.** v2, unchanged (0.030 m placement tolerance plus all other predicates).
- **Physics.** CPU at 60 Hz, 1800-step horizon.
- **Configurations.**
  - parent: no overrides
  - A: `{"lift_height": 0.20}`
  - B: `{"position_tolerance": 0.025}`
- **Resets.** One reset per scene (`--repeats 1`). Each manifest has one fixed shuffled execution order, shared by every configuration. The pilot showed that the ordered sequence reproduces exactly across processes (75/75 labels), so parent rollouts are shared between candidates.

## 3. Scene populations (`make_audit_manifest.py`, seed 20261115)

Pick positions are planar: x = r cos a, y = r sin a, z = 0.0258 m. Place is fixed at (0, 0.5, 0.0258). Cube orientation is identity.

- **Target neighbourhood:** r ~ U[0.79, 0.81] m and a ~ U[−62°, −58°], around the selected failure `r80_a-60`.
- **Old (deployment workspace):** r ~ U[0.35, 0.85] m and a ~ U[−60°, 60°], the development panel's bounding region. Draws falling in r ∈ [0.77, 0.83] and a ∈ [−64°, −56°] are rejected so old and target scenes stay disjoint. Old scenes therefore include the boundary ring, as in development: some are parent failures (possible gains) and some may be unreachable.

The draw order is fixed: 12 validation target (`vt01–vt12`), 8 validation old (`vo01–vo08`), 40 audit target (`at001–at040`), 120 audit old (`ao001–ao120`).

**Sizes.** Validation follows the research plan's budget-matched gate sizes. Audit sizes were enlarged from the plan's provisional 16 target / 24 old because measured throughput (§7) allows it. At 24 old scenes a ~5% conditional loss rate cannot be told apart from 0%. At ~100 parent old successes, the Wilson 95% half-width is about ±4–5 percentage points.

## 4. Gates (committed by `audit_gates.py` before any audit batch runs)

Rollouts are paired parent vs candidate outcomes on the same scene label.

- **Frozen:** always keeps the parent.
- **Target-only:** admit if candidate successes exceed parent successes on `vt01–vt12` (12 pairs, 24 rollouts).
- **Aggregate (primary):** on 4 target pairs (`vt01–vt04`) plus 8 old pairs (`vo01–vo08`), admit if target net > 0, old net ≥ 0, and at least one parent old success was observed. This also costs 24 rollouts.
- **Preservation:** admit if aggregate admits *and* old losses = 0. It uses the identical 24 rollouts.
- **Aggregate, unrestricted (secondary):** like aggregate but without the parent-old-success eligibility condition.

**Delivered controller.** Among admitted candidates, deliver the one with more candidate successes on that gate's own evidence; ties go to A, the first proposal. If none is admitted, the parent is delivered.

Invalid configurations and exhausted budgets would keep the parent (neither is expected; both proposals are valid). The zero-loss rule is a deployment preference, not a safety guarantee.

## 5. Primary audit outcomes (`analyze_audit.py`)

**Per candidate, separately for target and old regimes:**

- all four paired cells;
- parent and candidate success;
- unconditional and conditional loss (loss / parent successes);
- conditional gain (gain / parent failures);
- net change;
- Wilson 95% intervals over scenes.

**Useful update (declared now):**

- *Aggregate objective:* audit target net > 0 and audit old net ≥ 0.
- *Preservation objective:* audit target net > 0 and zero audit old losses.
- *Secondary:* a 5% conditional-loss tolerance.

**Per gate:**

- delivered-controller target and old success, with the parent kept after rejection;
- missed useful updates under each objective;
- admitted candidates with audit losses.

## 6. Secondary, diagnostic analyses (declared now)

1. **Decision stability.** Use 5,000 draws (seed 20261116) of validation-sized samples from the *audit* pools (4 target + 8 old; 12 target for target-only), without replacement, and report the admission probability for each gate × candidate. This reuses audit data and is labelled diagnostic.
2. **Placement-margin shift.** Paired final-error change on old parent successes.
3. **Approximate tolerance sensitivity** at 0.020–0.040 m. It re-scores with the final-frame error while keeping the other predicates; the frozen 0.030 m result stays primary.
4. **Geometry.** Radius and angle of each loss and gain.
5. **Parent reproducibility check.** Re-run the validation parent once more at the end of the queue; report outcome agreement and the maximum error difference.

## 7. Execution and stopping rule (`work/run_audit_batches.ps1`)

**Order:**

1. `audit_validation_parent`
2. `audit_validation_candidate_a`
3. `audit_validation_candidate_b`
4. `audit_gates.py` writes `results/audit_gate_decisions.json` (refuses to overwrite)
5. `audit_parent`
6. `audit_candidate_a`
7. `audit_candidate_b`
8. `audit_validation_parent_repeat`

**Size and time.** That is 60 + 480 + 20 = 560 rollouts. The pilot measured 6–12 s median execution per rollout plus 9–14 s startup per process, so the estimate is roughly 1–2 hours serial.

**Rules:**

- Every batch runs to completion; there is no early stopping on outcomes.
- Batches run one at a time; never start a second simulator concurrently.
- Folders are never overwritten.
- If a batch exits nonzero or is incomplete, the queue stops. Partial data are preserved. That batch is rerun *whole* into a new folder suffixed `_restart1`, because outcomes depend on the full ordered sequence, and the restart is documented.
- A failed launch is an infrastructure event, not a robot failure.

## 8. Reporting commitments

The report and paper will include:

- every denominator;
- both candidates, whatever their outcomes;
- the committed gate decisions and their timestamp relative to the audit batches;
- intervals for one context only;
- the tolerance-dependence finding from the pilot.

The paper will not claim that the preservation gate is "better". It will report what each gate delivered and missed under each declared objective.
