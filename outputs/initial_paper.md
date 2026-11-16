# Repair Without Regression? Budget-Matched Auditing of Agent-Edited Robot Skills

**Initial manuscript for author review — November 15, 2026**  
**Status:** Research proposal and pre-experiment draft. No experimental results are claimed. The methods below are the intended protocol; implementation and pilot findings may require documented revisions before evaluation is frozen.  
**Intended submission:** A four-page short paper to Trust4RSI-Agent at AAAI 2027. This editable manuscript is not yet formatted to the venue's page limit.

## Abstract

An agent can repair a robot skill on a newly encountered failure while changing behavior on scenes the skill previously solved. Average success may conceal this replacement: newly successful scenes can offset lost successes. We propose an empirical audit of this phenomenon in persistent robot-skill code, using an existing manipulation controller in NVIDIA Isaac Sim. A coding agent receives a failure trace and proposes a controller revision. Different admission rules then evaluate the same candidate revisions under matched simulation budgets. The central comparison holds both candidates and observed simulation outcomes fixed, changing only whether admission considers average success or also counts success-to-failure transitions. A separate, withheld scene set measures retained capabilities, new-case improvement, and rejected improvement opportunities. The proposed contribution is a reproducible study of the gain–retention tradeoff in agent-driven robot repair, together with a lightweight harness that makes that tradeoff explicit. The study does not claim a new regression-testing principle, a learned robot foundation model, or a statistical safety certificate.

## 1. Introduction

Robot agents increasingly improve behavior by editing executable policies in response to simulation feedback. The artifact that changes may be a state machine, a grasp offset, a timeout, or a recovery branch. Unlike a fresh program generated for a single episode, a persistent skill is reused across subsequent scenes. A locally useful repair can therefore have consequences beyond the failure that motivated it.

Consider a pick-and-place controller that misses a grasp on a shifted object. A coding agent changes the approach offset and successfully reruns that scene. The change might also move the gripper away from previously successful grasp configurations. Even evaluation on multiple scenes can miss the practical consequence if gains on some scenes compensate for losses on others. Whether this tradeoff is acceptable depends on the deployment objective; preserving earlier capabilities and maximizing average success are different objectives.

This paper asks: **under a fixed simulation budget, how much previously successful behavior is lost when an agent repairs a persistent robot skill, and does explicitly auditing those transitions improve the gain–retention tradeoff?**

Our proposed study makes three contributions. First, it measures both newly solved and newly broken scenes for each controller revision. Second, it compares admission rules on identical proposed revisions and identical evaluation evidence, isolating the effect of the decision rule. Third, it evaluates the controller actually retained after admission or rejection, accounting for both harmful updates and missed improvements. These are intended empirical contributions; their strength depends on the experiments.

## 2. Relation to existing work

Agent-harness verification already includes completion gates and independent review. Zhang et al. compare verification designs across coding and artifact tasks [1]. Our question concerns the behavioral consequences of persistent robot-policy edits and the objective used to admit them.

Aphale and Singh examine robot program self-repair and show why resampling and static guidance are essential controls when attributing improvements to failure feedback [2]. We therefore avoid treating successful retries as evidence that a new reasoning mechanism has been learned. The primary experiment keeps the candidate-generation process fixed across admission rules.

Kuroki et al. optimize closed-loop robot software with simulation feedback and select implementations using validation performance [3]. We study what aggregate validation can hide about retained behaviors, rather than claiming that code-based robot improvement is new.

Ma and Wu study update admission for continual embodied agents, including paired evaluation and the opportunity cost of rejecting useful updates [4]. This is the closest conceptual overlap. Our proposed distinction is an empirical audit of **directional scene-level behavior changes in agent-edited manipulation code**, compared with aggregate validation on exactly the same observations. Paired evaluation and rollback are existing techniques. If experiments cannot establish a meaningful distinction from this prior work, the manuscript should be narrowed to a replication or exploratory position paper.

## 3. Problem and measurements

Let a controller version be \(p\), a proposed revision be \(p'\), and a fully specified scene/reset be \(x\). Define \(S(p,x)\in\{0,1\}\) using an evaluator controlled by the experiment runner. The coding agent cannot edit the evaluator, simulator parameters, reset manifests, or acceptance rule.

We distinguish an old operating distribution \(D_o\) from a repair-target distribution \(D_n\). Both are defined before evaluation. On paired old-scene executions, define

\[
L=\Pr_{x\sim D_o}[S(p,x)=1,S(p',x)=0],\qquad
G=\Pr_{x\sim D_o}[S(p,x)=0,S(p',x)=1].
\]

The average performance difference is

\[
J_o(p')-J_o(p)=G-L.
\]

Thus zero average change does not imply that previous successes were preserved. For illustration, a controller may succeed on eight of ten scenes both before and after a repair, while losing one earlier success and gaining one different success. This is an arithmetic example, not an experimental observation.

We report the unconditional loss rate \(L\), conditional lost-success fraction \(R=L/J_o(p)\) when the denominator is nonzero, old-distribution net change, and target-distribution gain. A regression means a measured success-to-failure transition; it does not automatically imply lower average utility or a physical safety violation. Repeated executions estimate the extent to which simulator variability explains apparent transitions.

## 4. Harness and admission rules

The harness implements five operations: restore a scene, execute a versioned controller, record measurements, evaluate a proposed revision, and retain either the candidate or its parent. Candidate files and evaluation records are content hashed. Each record identifies the code version, simulator configuration, reset, outcome, and runtime.

The initial implementation uses a built-in Franka pick-and-place example [5]. Low-level motion generation is kept fixed. The agent can edit a small high-level controller module governing approach offsets, phase transitions, grasp/release timing, and bounded recovery. This limits setup and attribution costs while allowing consequential behavioral changes. Access to simulator state is explicitly privileged and is identical across conditions.

For each repair context, the agent receives the parent controller, task requirements, and a failed training execution. It generates a fixed number of independently sampled candidate edits. All candidates—including invalid programs and unsuccessful repairs—remain in the recorded population. Candidates are frozen before admission data are exposed.

We compare four rules:

1. **Frozen parent:** reject every revision. This establishes the retention ceiling and the cost of refusing to adapt.
2. **Target-only validation:** admit a revision only if it improves measured performance on fresh target scenes. Spend its full evaluation budget on that distribution.
3. **Aggregate validation:** use paired target and old-scene observations; require positive measured target gain and nonnegative measured old-distribution change.
4. **Preservation-aware validation:** use exactly the same observations as aggregate validation, additionally limiting measured losses of previous successes.

For the primary comparison, the proposed budget is 24 simulator rollouts per candidate: four paired target resets and eight paired old resets. A pair requires one parent and one candidate execution. Both aggregate and preservation-aware validation consume these same 24 rollouts. The target-only rule uses twelve target pairs. Reusing observations computationally does not erase their logical cost in a deployed admission rule.

The initial preservation threshold is zero observed old-scene losses. This is a conservative engineering baseline, not a guarantee. A threshold sweep is secondary and specified before final evaluation. Insufficient evidence, including an old-scene panel with no parent successes, produces deferral to the parent. The primary study compares the two rules on the common evaluable population and also reports population-wide deferrals.

After each decision, the delivered controller is \(p'\) if admitted and \(p\) otherwise. A stricter gate can appear favorable simply by rejecting more candidates. We therefore report admission rates and compare against an aggregate gate randomly thinned at a rate fixed using development data. Frozen-parent performance and rejected useful candidates remain visible.

## 5. Experimental protocol

### 5.1 Environment and scope

The minimum study uses one manipulation task with separately defined operating regimes, such as object location, object size, and placement target. These are **regimes of one task**, not three independent robot benchmarks. Parameters must remain physically feasible. The nominal controller must show both successes and repairable failures; an all-success or all-failure baseline cannot support this study.

Training failures, admission scenes, and final audit scenes use disjoint manifests. Scene-generation code, success tolerances, horizon, and randomization ranges are frozen after the pilot. Success is checked from measured object and gripper state after a settling interval, not from a controller's own completion flag. The evaluator rejects invalid or non-finite state and logs crashes and timeouts. Additional collision or force metrics are included only if the sensors and thresholds have been validated.

### 5.2 Sampling and comparison

The initial target is 20 sampled repair contexts and three candidate edits per context, yielding 60 candidates from one fixed model configuration. This is a small workshop study, not a broad assessment of all agent models. The population is explicitly conditional on the sampled parent-controller failures.

Each frozen candidate and its parent are audited on 60 previously withheld resets: 40 old-distribution scenes and 20 target scenes. Assuming each parent audit is reused only across its three candidates, this entails 3,600 candidate and 1,200 parent audit rollouts, plus admission and development executions. Repeated-reset checks add cost. These are planning counts, not completed runs. Throughput measurements will determine whether the deadline permits this size.

The primary experiment uses common candidate pools, so it estimates admission quality conditional on the proposal distribution. It does not establish superiority of a closed-loop learning system. A secondary sequential-repair experiment is included only if time permits; its results are reported separately because admission decisions alter future candidates.

### 5.3 Outcomes and analysis

Primary outcomes are the retained controller's target gain and conditional old-success loss, with admission rate and net old-distribution performance reported alongside them. We also measure how often aggregate validation admits a candidate that passes its local checks but loses previous successes in the withheld audit.

Uncertainty is estimated by resampling repair contexts, keeping all candidates and paired scene outcomes from a context together. Report per-regime results and raw denominators. Scene repetitions are not treated as independent model-generated repairs. With one parent-controller family and one task, confidence intervals describe that experimental population; they do not establish generality across robotics.

To assess missed opportunity, define an audit-useful candidate before analysis as one with positive measured target gain and old-distribution net change no worse than a declared tolerance. Report how often each gate rejects such candidates. This label is finite-audit evidence, not population truth. A second, retention-constrained definition makes the alternative objective explicit.

## 6. Results to be completed

**No experiments have yet established the hypotheses in this draft.** The final manuscript should replace this section with measured results and confidence intervals.

| Admission rule | Admitted / total | Delivered target gain | Lost old successes | Net old success change | Rollouts used |
|---|---:|---:|---:|---:|---:|
| Frozen parent | Not run | Not run | Not run | Not run | Not run |
| Target-only | Not run | Not run | Not run | Not run | Not run |
| Aggregate | Not run | Not run | Not run | Not run | Not run |
| Preservation-aware | Not run | Not run | Not run | Not run | Not run |

The most informative figure plots delivered target gain against lost old successes, with uncertainty and admission rate. A second plot shows per-candidate gains and losses, making compensating changes visible.

The proposed mechanism is supported only if it reduces withheld losses while retaining meaningful target gains relative to budget-matched and admission-rate controls. If its apparent advantage comes entirely from refusing useful updates, that is a negative finding. If baseline repairs rarely cause regressions, the original failure premise is unsupported in the tested setting and should be reported as such.

## 7. Limitations

Simulation results do not establish physical-robot safety or sim-to-real transfer. Scripted controller edits are a form of software-policy adaptation, not evidence of improved VLA training. Small admission panels can miss rare regressions. Even under independent sampling, observing zero losses in eight draws is compatible with substantial underlying risk: a 10% event has about a 43% chance of being missed. Adaptive reuse of validation scenes creates an additional overfitting risk, so the audit set remains inaccessible until candidates and rules are frozen.

Preserving individual successes may reject a repair that improves average task performance. That tradeoff is part of the research question. No gate can be declared universally superior without specifying the intended deployment objective.

## References

[1] Zhengxin Zhang et al. *Rethinking Verification in Agent Harnesses.* 2026. [Paper](https://arxiv.org/abs/2610.34577).

[2] Siddharth Aphale and Ayushman Singh. *Rethinking Self-Repair in Code-as-Policy Agents: What Drives Retry Success?* 2026. [Paper](https://arxiv.org/abs/2611.06863).

[3] So Kuroki, Kento Kawaharazuka, and Yujin Tang. *Learning and Transferring Closed-Loop Robot Software.* 2026. [Paper](https://arxiv.org/abs/2609.19906).

[4] Qinzhen Ma and Ruihai Wu. *When Validation Stops Learning: Auditing Update Admission for Continual Embodied Agents.* 2026. [Paper](https://arxiv.org/abs/2609.10873).

[5] NVIDIA. *Franka Pick and Place Example*, Isaac Sim documentation, version 6.2.0. [Documentation](https://docs.isaacsim.omniverse.nvidia.com/6.2.0/examples/manipulation_franka_pick_place.html). The experimental software version must be replaced with the version actually installed and tested.
