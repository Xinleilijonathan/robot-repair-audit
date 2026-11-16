# Day 1: Windows simulator and evaluator feasibility

November 15, 2026. This is development evidence, not a repair benchmark or a held-out paper result.

## Outcome

Isaac Sim 6.2.0.0 is installed and running on Windows. The final evaluator completed **18/18 successful placements** across six scenes with three resets each. **All four negative controls were rejected.** Six paired-audit unit tests passed; their synthetic fixtures are separate from robot data. Today's installation/evaluator milestone is complete. The next research milestone remains conditional: natural failures and informative repairs have not yet been established.

The robot is NVIDIA's stock Franka pick-and-place example. Physics runs on CPU at 60 Hz; this is not a learned robot policy, GPU-parallel training, or VLA experiment. The GPU is an RTX 4070 Ti SUPER with 16 GB VRAM. Python 3.12, PyTorch 2.11.0+cu128, and CUDA availability were checked; pip check found no broken requirements.

## Measured baseline

| Development scene | Successes / repeats | Final goal error range (mm) |
|---|---:|---:|
| nominal | 3/3 | 25.12–25.12 |
| pick_far | 3/3 | 14.39–22.69 |
| pick_far_left | 3/3 | 13.82–14.01 |
| pick_left | 3/3 | 12.71–16.16 |
| pick_near | 3/3 | 14.11–15.11 |
| pick_right | 3/3 | 19.12–19.12 |

Successful repeats do not prove identical resets. Some final positions vary, including repeated scenes with unchanged initial specifications. Do not assume determinism or automatically reuse a single parent outcome. Tomorrow's pilot must include interleaved parent/candidate repeats; frozen reuse rules must account for this variability. These 18 repetitions are six scene configurations, not 18 independent repairs.

## Evaluator and controls

Version 2 requires observed lift above 0.0758 m, all 30 settling frames within 0.03 m of the target, grasp-frame distance above 0.08 m, linear speed below 0.02 m/s, angular speed below 0.1 rad/s, orientation drift below 0.05 rad, and completion before the configured horizon. It uses simulator object measurements separately from controller status. There is no task yaw objective. Grasp separation is a release/retreat proxy, not a contact-force or hardware-safety certificate. The horizon rule conservatively rejects an episode reaching its exact maximum step count.

| Control | Observed outcome | Scorer result |
|---|---|---|
| No motion | No lift; cube remains away from goal | Rejected |
| No grasp | Controller held in grasp phase; no lift | Rejected |
| Held at goal | Cube is near the goal but grasp remains close | Rejected |
| One-step timeout | Episode exhausts its one-step budget | Rejected |

The first three controls also exhaust their 900-step horizon. Their recorded component checks demonstrate relevant failures, but these are not isolated causal tests of every scoring predicate. No crash occurred in these completed runs; automatic batch recovery and crash accounting still need implementation before main collection.

## Throughput and memory

Warm-cache startup: 9.422 s; scene setup: 1.687 s. Median reset: 0.156 s; execution: 6.250 s; evaluation: 0.297 s. Median execution plus evaluation: 6.547 s. Peak process working set: 5.02 GiB (OS process high-water mark, not total machine RAM or peak VRAM). Startup excludes imports after SimulationApp construction; timings are component measurements, not a complete end-to-end budget.

At the measured successful-baseline throughput, 1,920 executions plus median reset costs imply approximately 3.57 serial hours before generation, long failures, diagnostics, I/O, and startup. This is an extrapolation, not a measured main-study duration. The 1,800-step default permits much longer failures. Do not assume parallel execution or freeze the final budget from this extrapolation alone.

## Version history and reproducibility

- `results/stock`: initial three stock runs, before stronger settling checks; not pooled with the final set.
- `results/feasibility`: first 18-run development set; orientation drift and linear velocity checked, angular velocity not directly logged. All passed. Its reconstructed source snapshot was verified against the run's original SHA-256 metadata.
- `results/negative_controls`: three development controls with that earlier evaluator; all rejected.
- `results/feasibility_v2`: authoritative 18-run baseline with direct angular-velocity measurements and timing/memory instrumentation.
- `results/negative_controls_v2` and `results/timeout_v2`: four controls using version 2.

Each final run directory contains metadata, the exact runner snapshot and SHA-256, rollout records, and object trajectories. `environment-lock.txt` records installed package versions. Logs and local launch configuration are preserved in `reproduction/`. Paths in the launch script are machine-specific and must be edited on another machine. Online assets may be fetched by Isaac Sim; the archive is not an offline asset bundle.

Initial startup required relocating the Warp compilation cache into the writable workspace. Earlier failed/stopped attempts remain in work logs; they are setup diagnostics, not missing benchmark episodes. A Documents/Kit/shared warning persisted without preventing the completed runs. No model-generated repair candidates have been evaluated.

## Research decision and next work

The baseline is usable but currently too easy to identify repair opportunities. All successes provide no compensating old-scene gains, so aggregate and zero-loss gates cannot differ on this observed parent panel. This is a limitation of today's evidence, not evidence that either gate works better.

On November 16, evaluate the remaining pre-existing development scenes and a documented, physically plausible variation rule. Preserve all outcomes, including failures. Establish reproducible natural failure contexts without weakening the parent or choosing final audit scenes to manufacture gate disagreement. Then run at most five contexts with two bounded parameter proposals each. Log proposal provenance and label interactive proposals as exploratory unless a repeatable model interface is established. Main collection remains conditional on informative pilot results.

The strongest defensible paper remains an empirical study of losses hidden by aggregate repair success. [When Validation Stops Learning](https://arxiv.org/abs/2609.10873) already studies update-admission budgets and missed learning opportunities. [Rethinking Self-Repair in Code-as-Policy Agents](https://arxiv.org/abs/2611.06863) motivates controls against attributing retry gains to feedback alone. Our evidence must distinguish directional behavior changes and delivered-policy outcomes, not claim invention of regression checking.

The [Trust4RSI-Agent call](https://trust4rsi-agent.github.io/AAAI2027/) remains the target; November 19 is the intended submission date ahead of its November 20 AoE deadline. This is a non-archival workshop submission, not a promise of acceptance or publication by November 20. The initial manuscript remains a proposal pending repair results.
