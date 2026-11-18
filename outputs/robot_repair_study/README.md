# Robot repair study — artifact

This folder accompanies `../initial_paper.md` (historical pre-experiment draft) and `../research_plan.md`. The submission manuscript is `paper/main_ext2.tex`, with a 4-page-total variant in `paper/main_ext2_short.tex`. `paper/main.tex` and `paper/main_short.tex` are the earlier version, without Extension 2. Results write-ups are `../repair_pilot_report.md` (development pilot), `../audit_report.md` (frozen audit), `../extension1_report.md` (post-hoc candidate-population extension) `../extension2_report.md` (pre-registered loss-history test) and `../extension3_report.md` (pre-registered test on AI-agent-proposed repairs, added to both drafts on Nov 18).

## Extension 3 (pre-registered agent-proposed repairs, Nov 17–18)

Protocol `extension3_protocol.md`, hashes `extension3_frozen_hashes.json` and `ext3_proposal_hashes.json` (written by `scripts/freeze_ext3.py`), materials from `make_ext3_materials.py`, proposals in `proposals/ext3/` (collected by `run_ext3_agents.py`; agent CLIs not included), results in `results/ext3/`. Queue: `scripts/run_extension3.ps1` with `scripts/launch_isaac_ps51_timeout.ps1`. Commands are run from this directory; `R=results/ext3`.

| Output | Command |
|---|---|
| Frozen analysis (P1, S1–S6) | `analyze_ext3.py --audit-manifest ext1_audit_scenes.json --parent $R/audit_parent --ext1-parent results/ext1/audit_parent --index proposals/ext3/index.json --results $R --suites ext3_suites.json --output $R/ext3_analysis.json` |
| Post-hoc: copied edits, leave-own-out and new-edits-only P1 | `explore_ext3_insample.py --analysis $R/ext3_analysis.json --suites ext3_suites.json --output results/exploratory/ext3_insample.json` |
| Post-hoc: copied edits vs their earlier runs | `explore_ext3_copy_replay.py --output results/exploratory/ext3_copy_replay.json` |

## Extension 2 (pre-registered loss-history test, Nov 16–17)

Protocol `extension2_protocol.md`, hashes `extension2_frozen_hashes.json` (written by `scripts/freeze_ext2.py`), materials from `make_ext2_materials.py`, results in `results/ext2/`. Queue: `scripts/run_extension2.ps1` with `scripts/launch_isaac_ps51_timeout.ps1`. Commands are run from this directory; `R=results/ext2`.

| Output | Command |
|---|---|
| Committed gate decisions | written once by the queue (`ext2_gates.py`): `$R/ext2_gate_decisions.json` |
| Frozen analysis (P1, S1–S5) | `analyze_ext2.py --audit-manifest ext1_audit_scenes.json --parent $R/audit_parent --candidates $R/audit_r25 … $R/audit_r48 --gates $R/ext2_gate_decisions.json --suites ext2_suites.json --ext1-parent results/ext1/audit_parent --validation-manifest ext2_validation_scenes.json --validation-parent $R/ext2_validation_parent --validation-parent-repeat $R/ext2_validation_parent_repeat --output $R/ext2_analysis.json` |
| Post-hoc: suite batch vs audit | `explore_ext2_agreement.py --output results/exploratory/ext2_agreement.json` |
| Post-hoc: per-scene loss counts | `explore_ext2_scenes.py --output results/exploratory/ext2_scenes.json` |
| Extension 2 figure | `plot_ext2.py --analysis $R/ext2_analysis.json --scenes results/exploratory/ext2_scenes.json --suites ext2_suites.json --output fig_ext2.pdf` |
| Combined gate table | `make_combined_gate_table.py results/ext1/population_analysis.json $R/ext2_analysis.json OUT_DIR` (`paper/` locally; `scripts/` in the review artifact) |

Every analysis script refuses to overwrite an existing output; write to a new path to re-check.

## Extension 1 (post-hoc candidate population, Nov 15–16)

Protocol `extension1_protocol.md`, hashes `extension1_frozen_hashes.json`, results in `results/ext1/`. Queue: `scripts/run_extension1.ps1` with `scripts/launch_isaac_ps51_timeout.ps1`. Commands are run from this directory; `R=results/ext1`.

| Output | Command |
|---|---|
| Committed gate decisions | written once by the queue: `$R/audit_gate_decisions.json` |
| Per-candidate analysis | `analyze_audit.py --manifest ext1_audit_scenes.json --parent $R/audit_parent --candidates $R/audit_candidate_a $R/audit_candidate_b $R/audit_r01 … $R/audit_r24 --gates $R/audit_gate_decisions.json --validation-manifest ext1_validation_scenes.json --validation-parent $R/audit_validation_parent --validation-parent-repeat $R/audit_validation_parent_repeat --output $R/audit_analysis.json` |
| Population analysis (Q1–Q4) | `analyze_population.py --analysis $R/audit_analysis.json --gates $R/audit_gate_decisions.json --index proposals/ext1/index.json --first-audit results/audit_analysis.json --output $R/population_analysis.json` |
| Figure 2 | `plot_population.py --population $R/population_analysis.json --output fig_population.pdf` |
| Table 4 | `make_population_table.py $R/population_analysis.json $R/audit_analysis.json OUT_DIR` (`paper/` locally; `scripts/` in the review artifact) |

## Reproducing the reported numbers (Nov 15 update)

Use the Isaac Python interpreter for every command. None of these re-runs the simulator; they recompute everything from the recorded rollouts.

| Output | Script | Input |
|---|---|---|
| Development pilot comparison | `compare_pilot.py`, `pilot_diagnostics.py`, `scene_table.py` | `results/radial_*`, `results/boundary_parent` |
| Committed gate decisions | `audit_gates.py`, run once by the queue; output `results/audit_gate_decisions.json` | validation folders |
| Audit analysis | `analyze_audit.py`; output `results/audit_analysis.json` | — |
| Figure 1 | `plot_audit_map.py` | — |
| Paper tables | `make_tables.py` (`paper/` locally; `scripts/` in the review artifact) | analysis and gate JSON |

**Protocol and provenance:**
- The frozen protocol is `audit_protocol.md`.
- Hashes are in `audit_frozen_hashes.json`. The infrastructure-only amendment is `audit_amendment_1.md`, with its hashes in `audit_frozen_hashes_amendment1.json`.
- The scene manifests were generated by `make_audit_manifest.py` (seed 20261115).
- **Queues:**
  - `scripts/run_repair_batches.ps1` ran the pilot.
  - `scripts/run_audit_batches.ps1` ran the audit.
  - Under Windows PowerShell 5.1, launch with `scripts/launch_isaac_ps51.ps1`.

## Evidence labels

- `test_audit.py` contains **synthetic software-test fixtures**, never robot results.
- `run_stock_scene.py` runs a **stock-controller pilot** to establish simulator functionality and reset repeatability.
- The proposed final study requires frozen candidate repairs, disjoint scene splits, and withheld evaluation. A successful stock-controller pilot does not establish the paper's repair hypothesis.

## Current Windows environment

The dedicated interpreter is:

```text
C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe
```

Verified installation: Isaac Sim 6.2.0.0, Python 3.12, CUDA-enabled PyTorch 2.11.0. Actual simulator runs, rather than CUDA availability alone, establish runtime compatibility. See `../day1_feasibility_report.md` for the final development evidence and limitations, and `environment-lock.txt` for package versions.

NVIDIA references:

- [Python installation](https://docs.isaacsim.omniverse.nvidia.com/6.2.0/installation/install_python.html)
- [Franka example](https://docs.isaacsim.omniverse.nvidia.com/6.2.0/examples/manipulation_franka_pick_place.html)
- [Manipulator API tutorial](https://docs.isaacsim.omniverse.nvidia.com/6.2.0/core_api_tutorials/tutorial_core_adding_manipulator.html)

## Audit test

From this directory:

```powershell
& 'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe' -m unittest -v test_audit.py
```

The tests verify compensating gains and losses, admission of useful preserving changes, undefined retention when the parent has no successes, the gain-minus-loss identity, isolation of audit data from validation data, and input validation.

## CSV audit schema

```text
context_id,candidate_id,split,regime,scene_id,parent,candidate
```

`parent` and `candidate` must be binary outcomes observed on the same scene/reset. Use `split=audit` for withheld data. Keep validation data labeled separately. `audit.py` refuses duplicate paired observations and empty audit populations.

```powershell
python audit.py observations.csv --output paired_summary.json
```

Do not interpret conditional loss as a probability estimate when no parent successes were observed. The script returns `null` in that case.

## Baseline pilot

`run_stock_scene.py` uses the installed NVIDIA task and records object trajectories, goal errors, lift evidence, and gripper separation. It separately records the stock controller's completion/failure status. CPU physics follows NVIDIA's stock tutorial; CUDA availability and a rendered RTX scene do not imply GPU-parallel physics training.

Actual run metadata and trajectories are preserved under `results/`. Each final run has an exact source snapshot whose SHA-256 matches its metadata. Simulator startup may download assets and compile shaders. The local launcher and configuration are archived under `reproduction/`.

The version 2 scoring rule is an explicit pilot choice: the cube must rise above 7.58 cm, remain within 3 cm of the target for the final 30 simulation frames, remain more than 8 cm from the measured grasp frame, have linear speed below 0.02 m/s and angular speed below 0.1 rad/s, and orientation drift below 0.05 rad. It must finish before the horizon. This is not a hardware safety definition. Final baseline and negative controls use directories with the `_v2` suffix; earlier runs are development history and must not be pooled as independent evidence.
