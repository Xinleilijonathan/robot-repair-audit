# Workshop research plan

## Extension 1 complete — November 15, approximately 23:59

The post-hoc candidate-population extension finished: 26 candidates (A, B and 24 seeded random edits), 3,800 rollouts, no failures. The results are in `extension1_report.md`.

- **Q1.** 10/10 target improvers lost old successes.
- **Q2.** 13/26 candidates gained at least as many old scenes as they lost. The only committed aggregate-vs-preservation disagreement was r14.
- **Q3.** Admitted losses were 61 (target-only), 33 (aggregate) and 17 (preservation). The stricter gates each missed 3 aggregate-useful candidates. All gates delivered B.
- **Q4.** A's and B's conditional loss rates replicated, while the sign of their old net change flipped to positive.

The paper now includes a clearly labelled post-hoc section. The remaining user decisions are unchanged (see below), plus confirmation of whether references count toward the 4-page limit.

## Frozen audit complete — November 15, approximately 16:30

The audit ran 560 rollouts in 61 minutes, every batch with exit code 0; gate decisions were committed 22 s before the first audit rollout, and the parent repeat matched 20/20. Full results are in `audit_report.md`.

- **Target neighbourhood (40 scenes):** parent 15, A 26, B 38.
- **Old scenes (120; parent 106):**
  - A: 8 losses / 4 gains, conditional loss 7.5%.
  - B: 5 losses / 4 gains, conditional loss 4.7%.

  The pilot's compensating gains did not replicate.
- **Committed gates:** aggregate and preservation both rejected both candidates; target-only delivered B.
- **Decision stability:** across resampled draws, aggregate and preservation disagree in about 6% of cases.
- **Explanation:** the development old panel over-represented the repaired failure family.

The manuscript (`../paper/main.tex`, AAAI-27 style, compiled with MiKTeX) now reports these results. Its body is 3 pages, with references on page 4.

The anonymized artifact is `../artifact/robot_repair_artifact.zip`; its leak check passes.

**Remaining before submission (user decisions):**
- Final read-through by the user.
- Confirm with the organizers whether references count toward the page limit.
- Author and OpenReview details.
- Where to host the anonymized artifact.

No submission has been made.

## Pilot complete — November 15, approximately 15:00 (Claude continuation)

All three queued batches finished with exit code 0 and 75/75 rollouts each. Both proposals repaired the target, 3/3 each. Both also lost old successes that were offset by gains on other r80 scenes:

- **A (lift 0.20 m):** 4 losses / 10 gains.
- **B (position tolerance 0.025 m):** 1 loss / 13 gains.

Full-panel aggregate admission admits both candidates; preservation rejects both. All losses are placement-precision misses of 0.034–0.040 m against the 0.030 m tolerance, and they disappear at 0.040 m. The discovery and repeated parents agree on 75/75 labels. Details are in `repair_pilot_report.md`.

Decision: GO for one frozen independent single-context audit (`robot_repair_study/audit_protocol.md`); NO-GO for the 10-context main study before November 19.

**Correction (Nov 15, 15:00):** The 13:05 entry below says the radial grid "passed 45/45". The recorded result is **44/45**: `r75_a+60` repeat 1 missed at 0.0308 m. Target selection is unaffected, because the rule required at least 2 of 3 failures. The original text is kept unchanged below.

## Active repair pilot and handoff — November 15, approximately 13:05

See `../CLAUDE_HANDOFF.md` for a self-contained continuation guide, current process status, exact commands, and publication constraints. Check live files before starting any new simulator.

The original twelve scenes passed 36/36 runs; the additional radial grid passed 45/45. A documented boundary extension found repeatable failures. Target r80_a-60 fails during lift. Two saved proposals are now queued across all 25 radial/boundary scenes: lower lift height to 0.20 m and relax controller convergence to 0.025 m, leaving evaluator thresholds unchanged. A fresh unchanged-parent panel follows them. At checkpoint, candidate A had 25/75 completed successes; this is partial and excludes its target result. Do not infer repair efficacy yet.

Next: complete both 75-rollout candidate panels and the 75-rollout parent repeat; analyze gains/losses and parent repeatability; write the pilot report; make a go/no-go decision for a frozen independent audit; revise the manuscript; format/anonymize for user review. The main empirical study and submission remain incomplete. The official author kit was obtained, but its pdfTeX requirement means the attempted Tectonic/XeTeX compilation cannot be used.

## November 15 completion update

- Completed Windows installation, headless startup, stock Franka execution, and six-scene/three-repeat baseline: 18/18 successes with evaluator v2.
- Completed four negative controls: all rejected. Direct linear/angular velocity, orientation stability, separated timing, process peak memory, exact source snapshots, and package lock are recorded.
- Reset outcomes are not fully deterministic. Do not assume parent reuse; test interleaved repeats before freezing its rule.
- Stage 1 infrastructure is complete. Transition to the full study is NOT approved by the evidence yet: all six development scenes succeed and no candidate repairs exist.
- November 16: remaining development scenes and plausible variation, natural failure discovery, at most five contexts/two proposals, then runtime/precision and go/no-go decision. Keep all this data out of the final audit.
- Report: day1_feasibility_report.md. The earlier review response records the pre-install audit; this update supersedes its runtime-status statements.

## Revision following external review — authoritative execution plan

This section supersedes the larger sample counts and execution assumptions in the original planning notes below. See review_response.md for the inspected project status, literature comparison, and answers to every pilot question. Installation and the November 15 evaluator feasibility milestone are complete; see day1_feasibility_report.md for measured results. No candidate-repair or held-out audit results exist.

**Research questions:** RQ1 measures how often agent-proposed repairs lose earlier successes. RQ2 measures when shared-evidence aggregate and preservation-aware gates disagree. RQ3 measures delivered target gain versus retained old successes, including missed useful updates.

**Stage 0: finish installation.** Require a successful installation exit, package/version checks, headless startup, and stock-scene execution. Preserve all errors. CUDA success alone is insufficient.

**Stage 1: validate the evaluator and resets.** Start with six representative development scenes repeated three times (18 rollouts). Record setup, reset, execution, and evaluation time separately; monitor peak memory. Validate object lift, placement tolerance, release/retreat, finite state, horizon, linear/angular settling velocity, and orientation stability. Do not impose a cube yaw objective unless specified by the task. Add negative controls: no movement, no grasp, held-at-goal, and timeout must not be scored as completed placement. Fix thresholds on development data and record every revision. Start one simulator process; do not assume parallelism is reliable.

**Stage 2: small repair pilot.** Use at most five sampled failure contexts and two proposals per context. Record the exact prompt, accessible information, model/version if available, outputs, invalid proposals, bounded parameter edits, and any human/assistant intervention. The current implementation supports parameter edits, not unrestricted source-code patches; choose and document one scope before collection. With no repeatable model client, label interactive proposals as a feasibility pilot rather than an independently sampled agent benchmark. Evaluate all proposals, not only successful repairs.

Record: valid proposals / all proposals; repair rate; regression frequency; frequency of both gains and losses; gate disagreement; aggregate admissions with independent-audit losses; and useful candidates rejected. Report denominators. All pilot scenes remain development data. No final audit may be inspected at this stage.

**Stage 3: freeze the minimum main study.** Provisional target: 10 contexts × 2 candidates = 20 candidates, one robot, one task, one fixed proposal model/interface. Freeze the population rule, prompts, controller parent versions, randomization ranges, gate thresholds, scene manifests, success evaluator, audit size, stopping rule, and analyses. Changes after this point require a new untouched audit. Increase to 12 contexts only if measured throughput permits it before the freeze, not because initial results look promising.

**Exact gates:** Let T be candidate minus parent target success, O be candidate minus parent old-scene success, and R be losses divided by parent old-scene successes. Frozen always retains the parent. Target-only admits if T>0 on 12 target pairs. Aggregate admits if T>0 and O≥0 on four target pairs plus eight old pairs. Preservation admits on those identical pairs if aggregate admits and observed losses are zero. For the primary aggregate/preservation comparison, both defer if no parent old successes were observed; also report the unrestricted aggregate rule as a secondary comparison so this imposed common eligibility condition is visible. A pair costs two rollouts. Invalid patches and exhausted budgets are separate recorded outcomes and retain the parent. The zero-loss rule is not a safety guarantee.

**Budget ledger:** Each gate logically consumes 24 rollouts per candidate; aggregate/preservation share observations. With 20 candidates, their shared ledger is 480 logical rollouts; target-only adds 480. If parent executions are reused across the two candidates of each context on the identical frozen resets, the distinct validation executions are 10×(12 parent + 24 candidate) = 360 for each sampling scheme, or 720 total. Without valid parent reuse, validation is 960 executions. Freeze reuse only after repeatability checks; retain all underlying observations.

Provisional audit: 40 resets per context (24 old, 16 target). Twenty candidates ×40 plus ten parents ×40 = 1,200 executions when parent observations are legitimately shared. Total main execution estimate: 1,920 with validation reuse, or 2,160 without it, plus pilot, repeated-reset diagnostics, generation, failures, startup, and analysis. Report shared computational savings separately from logical deployment budgets. At 5 seconds per rollout, 1,920 executions take about 2.7 serial hours; at 30 seconds, about 16 hours. These are arithmetic estimates, not measured speeds. Final audit size must be frozen after throughput measurement and a precision assessment.

**Statistics:** Report all four paired outcome cells, unconditional loss and gain, conditional retention/loss, old net change, target gain, admissions, deferrals, and missed useful updates. Compute delivered-policy outcomes using the parent after rejection. Use context-level summaries and exploratory context-cluster intervals; disclose common parent-family dependence and only 10 clusters. Do not treat simulation repeats as extra repairs. Calibrate random thinning on development data, freeze it, and report its actual audit-time admission rate. Define useful updates and any tolerated old-performance loss before auditing. Avoid selecting a preferred threshold from the audit.

**Go/no-go:** Advance beyond installation only after the stock scene runs. Advance beyond feasibility only after measured-state scoring and resets are validated and at least some natural failures can be repaired. Advance to a full gate-comparison paper only if the development pilot establishes that the contrast is informative; gate disagreement need not favor preservation. No numerical prevalence cutoff is imposed after observing results. A lack of disagreement is a reportable finding, not permission to engineer favorable final data. If no scientifically useful robot evidence exists by November 18, switch to a clearly framed position paper or defer submission. Never populate results with hypothetical numbers.

**Schedule:** Nov 15 installation and evaluator feasibility; Nov 16 repair pilot and runtime/precision decision; Nov 17 protocol freeze and main collection if qualified; Nov 18 withheld audit and evidence-based paper-type decision; Nov 19 final formatting, anonymization, reference checks, and intended submission. November 20 AoE is contingency time, not the working target.

**Manuscript revision policy:** Preserve the existing proposal as a versioned initial draft. After the pilot, align its intervention with what actually ran (parameter edits versus source patches), update status and sample sizes, and include only completed evidence. Prioritize one framework figure, one gain–loss plot, and one results table. Keep UR12e/VLA extensions in future work.

---

## Original planning notes (superseded where conflicting)

Prepared November 15, 2026. User resources: a Windows PC with an RTX 4070 Ti SUPER (16 GB VRAM), plus an existing Isaac Sim installation in a separate Ubuntu boot. Windows installation and autonomous experiment execution are authorized. This plan is conditional on a successful simulator pilot.

## Recommendation

Combine an agent-harness contribution with a small robotics evaluation. Study how the harness admits an agent's changes to an existing robot controller. Train no new foundation model. The initial manuscript is `initial_paper.md`.

The core question is whether apparently successful repairs exchange old successes for new ones, and whether recording those directional changes improves admission decisions at the same simulation budget. The strongest potential contribution is a careful empirical finding supported by controlled comparisons and reproducible artifacts. Regression testing itself is not novel.

## Venue and dates

The [Trust4RSI-Agent workshop at AAAI 2027](https://trust4rsi-agent.github.io/AAAI2027/) lists a November 20, 2026 AoE submission deadline, December 2 notification, and a one-day workshop during February 22–23, 2027 in Montréal. It accepts four-page short/position papers, uses double-blind review, and is non-archival. Its topics directly include policy updates, regression suites, rollback, and trustworthy agent evolution. The CFP says references and appendices are “usually” excluded, so the final submission form must be checked before relying on that wording. [Submission portal](https://openreview.net/group?id=AAAI.org/2027/Workshop/Trust4RSI-Agent).

**November 20 is a submission deadline, not an acceptance or publication date.** Target submission on November 19 to meet the user's “before 11/20” request. Acceptance cannot be promised, and a non-archival workshop presentation is different from an archival proceedings publication.

ICLR 2027 is a later fallback, not a confirmed immediate target: its central [workshop call](https://iclr.cc/Conferences/2027/CallForWorkshops) lists workshop acceptance notification on November 29, 2026 and a suggested contribution deadline of February 1, 2027. Individual workshop calls must be checked after selection.

## Why this scope

| Direction | Fit to five days | Main issue |
|---|---|---|
| New VLA/RL learning algorithm | Poor from the present starting point | Training, baselines, and task setup would dominate |
| General-purpose new agent harness | Technically feasible, weakly scoped | Verification, memory, and retry mechanisms already have substantial overlap |
| Admission audit for agent-edited robot skills | Best conditional fit | Requires repeatable baseline execution and a measurable repair tradeoff |

A controller is simply the code that turns the current robot state into the next movement. The initial controller will come from NVIDIA's manipulation example. The agent changes the high-level skill code; the robot then executes that code in simulated scenes.

## Literature to review first

1. [Rethinking Self-Repair in Code-as-Policy Agents](https://arxiv.org/abs/2611.06863): closest accessible starting point for the repair setup. Its controls show why retry success alone is not enough to establish a special benefit from failure feedback.
2. [When Validation Stops Learning](https://arxiv.org/abs/2609.10873): closest overlap for admission gates and lost learning opportunities. The proposed study must distinguish its question and compare against simple baselines.
3. [Learning and Transferring Closed-Loop Robot Software](https://arxiv.org/abs/2609.19906): establishes simulation-guided robot-code optimization and validation selection as existing work.
4. [Rethinking Verification in Agent Harnesses](https://arxiv.org/abs/2610.34577): establishes that independent review and completion gates are already studied.

Do not claim a first-ever verifier, first rollback mechanism, first paired evaluation, or first agent-driven robot-code repair. A workshop-sized contribution can instead quantify an overlooked tradeoff in a specific setting, with unusually clean controls.

## Implementation sequence

1. Install a pinned Windows Isaac Sim release in a dedicated Python environment. Record GPU, driver, OS, package versions, and launch command.
2. Run the stock robot example. Verify measured object movement and success from simulator state.
3. Add deterministic scene manifests and repeated resets. Measure runtime and reset variability before claiming paired comparisons are reliable.
4. Freeze low-level motion generation. Expose one small controller module for agent edits. Make scoring, scene definitions, and validation data read-only to the repair process.
5. Collect a development population with both successes and failures. Do not secretly weaken the baseline to manufacture a research result. Deliberately injected defects, if used, must be a separately labeled diagnostic.
6. Generate and record candidate edits. Freeze the prompt, model configuration, edit scope, and candidate count before final data collection. A manually assisted pilot is not a reproducible autonomous-agent benchmark.
7. Run common-candidate admission comparisons, then the withheld audit. Record all rejected and invalid candidates, not only successful repairs.
8. Analyze paired gains/losses, admission rates, delivered-controller outcomes, and costs. Produce figures directly from raw logs.

## Minimum experiment and compute accounting

Begin with one pick-and-place task and a few declared scene regimes. Add a second task only after the first is stable. Twenty repair contexts with three candidates each is the initial target, subject to measured throughput; it is not a power guarantee.

The central contrast uses exactly the same candidate and the same 24 simulation executions for aggregate and preservation-aware admission. This rules out “your method just ran more checks.” An additional target-only rule reallocates its equal budget to target scenes. The frozen parent exposes the trivial solution of never updating.

The planned withheld audit has 60 resets per context: 40 old and 20 target. With 60 candidates and 20 parent contexts, the audit needs 4,800 rollouts before reset-repeat diagnostics, gate data, or pilot runs. Measure throughput before committing. If one rollout takes 30 seconds serially, these audits alone take about 40 hours; at five seconds, about 6.7 hours. These are arithmetic planning estimates, not measured simulator speeds.

Report language-model input/output tokens, model charges if any, simulator steps, rollout wall time, and GPU time separately. No paid model API or additional cloud compute has been selected or purchased. A repeated, pinned model endpoint is needed for reproducible candidate generation; interactive edits by this assistant can establish feasibility but must be labeled accurately.

## November 15–19 schedule

| Date, Los Angeles | Deliverable | Decision point |
|---|---|---|
| Nov 15 | Windows install, stock scene, measured baseline, initial manuscript | Can the robot execute and reset repeatably? |
| Nov 16 | Small development pilot and fixed evaluator | Do natural failures and consequential repairs exist? |
| Nov 17 | Frozen protocol, candidate collection, main executions | Is throughput sufficient for the full audit? |
| Nov 18 | Withheld evaluation, uncertainty analysis, figures | Do findings survive cost and admission-rate controls? |
| Nov 19 | Four-page paper, reference checks, anonymization, reproducibility package, submission | Submit only claims supported by actual evidence |

This is an aggressive schedule, especially without an existing Windows simulator baseline. If setup or pilot evidence fails, the fallback is a clearly labeled position/exploratory paper with whatever real evidence exists. A negative result is acceptable if measured carefully. Fabricated tables or an unchanged proposal presented as completed research are not.

## What would make the paper convincing

- A repair that passes local validation but loses prior successes, demonstrated from measured robot outcomes rather than a narrative.
- The frequency of that behavior across a defined population, not only an anecdote.
- A comparison using the exact same candidate edits and simulation observations.
- Retained target improvement, so the gate is doing more than rejecting every edit.
- A clear account of failed candidates, reset noise, and task limitations.
- A runnable artifact that regenerates the main table and figure from recorded data.

## Likely reviewer objections

**“This is just regression testing.”** Agree that the primitive is established. The empirical question is the magnitude and budget tradeoff of directional behavior replacement in persistent, agent-edited robot skills.

**“The safer gate just accepts fewer updates.”** Include a frozen baseline, delivered-policy performance, missed opportunities, and an admission-rate control fixed on development data.

**“Your average metric was the wrong objective.”** Report both objectives. Preservation is an explicit deployment preference, not a universal definition of success.

**“The simulator is too narrow.”** Call it one task with several regimes unless another task is actually completed. Avoid physical-robot safety and general VLA claims.

**“The repair feedback is not doing anything special.”** Hold proposal generation fixed in the main comparison. If claiming improved repair generation, add resampling and static-guidance baselines first.

**“The evidence was selected to make the method win.”** Freeze splits and thresholds before final evaluation; disclose screening and include every generated candidate.
