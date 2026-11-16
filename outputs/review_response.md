# Response to research review and project audit

**Later November 15 status:** Windows installation and evaluator feasibility are now complete. See day1_feasibility_report.md and the completion update in research_plan.md. The component table below is preserved as the earlier pre-install audit, not the current runtime status.

November 15, 2026. This response reflects inspected files and executed checks, not intended functionality. The attached review is substantially correct, but several distinctions below are necessary.

## 1. Actual project status

| Component | Evidence and status |
|---|---|
| Hardware | Windows 11, 20 logical CPU processors, approximately 31.7 GiB RAM, RTX 4070 Ti SUPER with 16,376 MiB VRAM; driver 610.88. CPU model and physical-core count were not established. |
| CUDA | PyTorch 2.11.0+cu128 imported successfully and reported CUDA available on the GPU. |
| Isaac Sim | Version 6.2.0.0 installation is still running. The extension cache was observed at approximately 12.3 GB and 117,220 files. Installation completion and simulator startup are NOT verified. |
| Environment | Dedicated Python 3.12 environment exists under Documents/Codex/isaac-sim-env. Ubuntu is a separate boot and cannot run concurrently through this Windows session. |
| Baseline runner | run_stock_scene.py exists and compiles. It has NOT executed in Isaac Sim. |
| Scene manifest | Twelve exploratory scene specifications exist. Reachability and reset reproducibility remain unverified. They are pilot scenes, not a frozen benchmark. |
| Editable controller | The runner implements a bounded JSON parameter interface for six high-level controller parameters. It uses internal fields seen in upstream source; compatibility with the installed package remains untested. It does NOT yet implement a general code-patching agent. |
| Scoring | Lift, placement error over 30 frames, and measured grasp-frame separation are implemented in the runner. Velocity, orientation stability, crash accounting, and robust horizon semantics require completion and simulator validation. |
| Admission analysis | audit.py implements paired metrics and two admission rules. Six diagnostic unit tests pass, including compensating gains/losses and withholding validation records from audit summaries. |
| Candidate generation | No reproducible model client, frozen generation prompts, or independently sampled candidate population exists. Interactive parameter proposals must be labeled as such. |
| Data | No robot rollout results, repair results, empirical figures, or confidence intervals exist. Synthetic unit-test fixtures are not experimental evidence. |
| Draft | Initial manuscript and review PDF exist. They explicitly label results as not run. They are proposals, not completed empirical papers. |

The existing hardware is suitable to attempt a small scene, but successful CUDA access does not prove Isaac Sim compatibility. NVIDIA lists 32 GB RAM, 16 GB VRAM, and an RTX 4080 GPU reference in its [requirements](https://docs.isaacsim.omniverse.nvidia.com/6.2.0/installation/requirements.html). The actual launch and throughput measurements decide feasibility.

## 2. Novelty assessment

The four references were checked against their primary arXiv records and full-text HTML during this task.

| Prior work | Established contribution relevant here | Defensible distinction for this study |
|---|---|---|
| [Ma and Wu](https://arxiv.org/abs/2609.10873) | Update-admission auditing, paired comparisons, rejection of useful updates, and budget limitations in continual embodied learning; analytical and synthetic diagnostics | Directional scene-level changes in agent-proposed edits to an actual manipulation controller. Paired testing and opportunity-cost reporting are not new. |
| [Aphale and Singh](https://arxiv.org/abs/2611.06863) | Simulated robot program retry comparisons with resampling, feedback, and static-guidance controls | Persistence across a distribution after a repair, and admission conditional on the same proposed edits. Do not claim feedback-specific repair benefits without their controls. |
| [Kuroki et al.](https://arxiv.org/abs/2609.19906) | Simulation-guided closed-loop robot-code optimization, validation selection, and transfer | Quantify cases hidden by aggregate selection; code-based policy adaptation itself is existing work. |
| [Zhang et al.](https://arxiv.org/abs/2610.34577) | A comparison of instructions, reminders, completion gates, and independent review in agent harnesses | Robot-controller behavioral transitions and admission objectives, not invention of verification or independent review. |

Recommended positioning: **an exploratory empirical audit of directional behavior changes in persistent, agent-edited robot skills under shared validation evidence.** This remains a candidate contribution, not a verified novel finding or an exhaustive literature review.

Remove or avoid claims of a novel verification algorithm, regression-free updates, population safety, improved VLA learning, or general robot-learning superiority. The user's UR12e/VLA research is motivation and future work only.

## 3. Corrections and qualifications to the review

**Gate equivalence:** Correct and central. For the zero-loss gate, disagreement requires a positive observed old-scene loss L, at least as much compensating gain G, and positive target gain. Merely having mixed parent successes/failures is necessary but not sufficient. If every parent old-scene outcome is successful, G=0 and the gates agree. A failure-free parent panel does not imply the controller is failure-free outside that panel.

**Zero observed losses:** Correct. The calculation 0.9^8≈0.43 applies when 10% is the *unconditional* loss-event probability across eight independent old-distribution draws. If 10% refers to loss conditional on parent success, the relevant sample size is the number of parent-success observations, often fewer than eight. Neither interpretation supplies a certificate from this small panel.

**Uncertainty:** Context-cluster bootstrap is useful for correlated candidates, but 10 contexts give fragile intervals. All contexts may also share one controller family and scene generator. Report raw counts and context-level estimates; intervals do not establish generality across tasks, controllers, or models. Repeated simulator runs measure reset noise, not independent repairs.

**Admission matching:** A random-thinning probability selected on development data only approximately matches the held-out admission rate. Call it development-calibrated thinning and report actual rates. Do not claim exact matching or tune its probability on final audit outcomes.

**Orientation:** A cube-placement task need not require a specific yaw unless the task specification says so. Measure orientation/velocity stability to reject a rolling or falling cube; do not silently add a target-orientation requirement that changes the task. This is a proposed evaluator revision, to be frozen before final testing.

**Scope reduction:** Agree with 10 contexts × 2 candidates as an engineering target, not a sample-size justification. Select audit size using runtime and desired precision before inspecting audit outcomes. A small, underpowered result must be called exploratory.

**Publication:** November 20 is the submission deadline, not an acceptance date. The [workshop CFP](https://trust4rsi-agent.github.io/AAAI2027/) lists December 2 notification and describes the workshop as non-archival. The user's earlier request to submit before November 20 is preserved: November 19 remains our internal submission target.

## 4. Answers to the seven pilot questions

1. **Does the baseline have successes and failures?** Unknown; no simulator executions yet.
2. **Can the agent produce executable patches?** Not established. A syntactically valid parameter interface exists, but no patch has executed in the simulator.
3. **Do patches repair failures?** Unknown.
4. **Do they introduce regressions?** Unknown.
5. **Do gains and losses compensate?** Unknown; arithmetic and unit tests illustrate the possibility only.
6. **Do gates disagree?** Yes on synthetic software fixtures; unknown on robot outcomes.
7. **Is the pipeline reproducible?** Not yet. Audit functions pass tests, but resets, model generation, evaluator behavior, and simulator execution require verification.

These are the right pilot questions. None should be answered from the paper's motivation alone.

## 5. Submission decision

An empirical short paper is realistic only if installation, baseline execution, and reset/scoring checks succeed promptly, followed by a genuinely recorded candidate population and an untouched audit. We have not yet met that threshold. A position paper remains possible, but must contribute a clear argument and relate it honestly to prior work; a proposed benchmark alone does not guarantee acceptance.

If gates seldom disagree, retain the prevalence finding and narrow RQ2 rather than selecting favorable patches. If repairs seldom change behavior, report that limitation and reconsider the testbed using development data only. If repeatability is poor, do not interpret success-to-failure pairs as repair-induced losses until the noise is quantified.

The revised task plan is in research_plan.md. No large rollout campaign is authorized by this plan before the pilot and protocol freeze conditions are met. The original manuscript remains a pre-experiment draft until these implementation gaps are reconciled.
