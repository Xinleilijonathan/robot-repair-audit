# Handoff to Claude: robot-repair workshop paper

> **Update, Nov 17 ~05:30 (Claude): EXTENSION 2 COMPLETE. H1 SUPPORTED. New paper drafts await the user's review.**
> - **Run.**
>   - 3,520/3,520 rollouts, 51 batches, no retries or failures.
>   - Gates were committed at 06:54:01.50 UTC, 2 s before the first audit batch.
>   - The audit parent matched the Extension 1 parent on 120/120 labels with identical errors. The validation repeat matched 20/20.
> - **Primary result (P1).** The history suite detected losses in 14/20 lossy edits, against an expected 0.36 for a uniform suite: +0.34 [0.16, 0.51].
> - **Secondary results.**
>   - Realized uniform suite: 7/20, McNemar p = 0.09, not significant.
>   - k = 4: 0.60 vs 0.22.
>   - Concentration: 31/97 losses fell on the 8 history scenes.
>   - All 11 target improvers lost old successes; pooled with Extension 1, 21/21.
>   - The history gate admitted 1 edit (2 losses); the uniform gate admitted 7 (28 losses). The history gate missed 9/10 aggregate-useful edits.
> - **Caveat (post hoc).** Candidate outcomes differed between the suite batch and the audit on 17/384 labels because of order and run context. Reading detection from the audit gives 15/20.
> - **Write-ups.**
>   - Report: `outputs/extension2_report.md`.
>   - Frozen analysis: `results/ext2/ext2_analysis.json`.
>   - Post hoc: `results/exploratory/ext2_*.json`, produced by `explore_ext2_*.py`.
> - **Paper drafts (separate files; `main.tex` and `main_short.tex` are untouched fallbacks).**
>   - `paper/main_ext2.tex`: a 4-page body plus references. It drops the pilot table, the audit gate table and the population figure, replacing them with text, a combined gate table and the Extension 2 figure.
>   - `paper/main_ext2_short.tex`: 4 pages total. It also drops the audit-map figure.
>   - The figure is `fig_ext2.pdf`, from `plot_ext2.py`. The table is `combined_gate_table.tex`, from `paper/make_combined_gate_table.py`.
>   - Two verified references were added: Kim & Porter (ICSE 2002) and Elbaum et al. (TSE 2002). History-based test prioritization is prior art, and the drafts say so.
> - **Waiting on the user.**
>   - Choose a version: the current paper, or the Extension 2 drafts.
>   - If the drafts are chosen, update the OpenReview abstract and TL;DR in `outputs/openreview_form.md`.

> **Update, Nov 16 ~22:00 (Claude): EXTENSION 2 RUNNING overnight (user-approved).**
> - **Question.** A confirmatory test of whether loss histories predict future regressions. Protocol: `outputs/robot_repair_study/extension2_protocol.md`. It was frozen at 21:52 in `extension2_frozen_hashes.json` (42 files) and pushed as commit `1a49f07` before any rollout.
> - **Design.** 24 new random edits (r25–r48). An 8-scene history suite (the scenes Extension 1 edits broke most often) against an 8-scene uniform suite, on the Extension 1 audit panel. 3,520 rollouts, about 6.5 hours.
> - **Queue.** `work/run_extension2.ps1`. Logs: `work/ext2_queue.log` and `work/ext2_*.log`. Results: `outputs/robot_repair_study/results/ext2/`. Ledger: `results/ext2/ext2_batch_ledger.json`.
> - **If it stopped:** rerun `work/run_extension2.ps1` from the project root. It is resumable. Never run two simulators at once.
> - **After completion:**
>   1. Run `analyze_ext2.py`, with the arguments listed in the protocol and shown in its argparse.
>   2. Report P1 against the pre-registered criterion, whatever the outcome.
>   3. Only then decide the paper changes. The current `main.tex` and `main_short.tex` remain the fallback.
> - **Motivation.** The exploratory analyses are in `results/exploratory/`, made by the `explore_*.py` scripts. They are post hoc and labelled as such.

> **Page-limit decision (user, Nov 16 ~00:15).**
> - **The question.** The user is emailing the organizers (trust4rsi.agent@gmail.com; primary contact Haolun Wu) to ask whether references count toward the 4-page short-paper limit.
> - **The two versions.**
>   - `paper/main.tex`: a 4-page body, with references on pages 4–5. This is the default.
>   - `paper/main_short.tex` → `main_short.pdf`: 4 pages total including references. Same results, tables and figures; the prose is condensed. This is the fallback, ready now.
> - **The user's instruction:** if the organizers have NOT confirmed by **Nov 18** that references are excluded, submit the 4-page-total version (`main_short`).
> - **Keep in sync.** Any content edit to `main.tex` must also go into `main_short.tex`.
>
> **Submission prep (Nov 16, user-approved fixes).**
> - **Artifact sentence.** The OpenReview form has only a PDF field (at most 50 MB) and no supplementary field. Both versions now say the anonymized artifact "will be released after the review period".
> - **Workshop fit.** Both versions now add one intro sentence framing the acceptance check as the release step of an agent's update layer.
> - **Form entries.** `outputs/openreview_form.md` has the title, keywords, TL;DR, both abstracts and the required confirmations.
> - **Still the user's:** an OpenReview profile for every author, the read-through, and the submission itself.

> **Update, Nov 15 ~23:59 (Claude): EXTENSION 1 COMPLETE and in the paper.**
> - **Run.** 3,800/3,800 rollouts, no retries, no exclusions. Gates were committed before the audit. The parent repeat matched 20/20. All 39 frozen hashes were re-verified.
> - **Results.** Full write-up in `outputs/extension1_report.md`.
>   - All 10 target-improving candidates lost old successes.
>   - No candidate is useful under the zero-loss objective.
>   - A's and B's old net changes flipped to +2 and +3, while their conditional loss rates replicated.
>   - Aggregate vs preservation disagreed only on r14.
>   - All gates delivered B.
> - **Analysis files.** `results/ext1/audit_analysis.json` and `population_analysis.json`.
> - **Paper.** `paper/main.tex` has a new post-hoc section with Figure 2 (`fig_population.pdf`, from `plot_population.py`) and Table 4 (`population_table.tex`, from `paper/make_population_table.py`). The body is 4 pages, and the references end on page 5.
>   - **Open:** whether references count toward the 4-page limit.
> - **Disclosure.** At the user's request, a read-only interim tally of 23/26 candidates was printed at ~22:54. Nothing depended on it; it is disclosed in the report.
> - **Artifact.** Rebuilt with the extension queue scripts and the table script. `.gitignore` no longer excludes ext1.

> **Git (Nov 15 ~17:10).**
> - **Repo.** The project is a git repo pushed to the **private** GitHub repo `Xinleilijonathan/robot-repair-audit`, with initial commit `b1afbd4`. Commits use the GitHub no-reply address, set in the local repo config only. `.gitignore` excludes caches, toolchains, `artifact/` and the in-progress `results/ext1/` and `work/ext1_*`.
> - **Tools.** Git is at `C:\Program Files\Git\cmd\git.exe`. gh is at `%LOCALAPPDATA%\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe`.
> - **Pushing.** No global credential helper is configured, so push with `git -c credential.helper= -c "credential.helper=!'<gh path with forward slashes>' auth git-credential" push`.
> - **After extension 1 completes:** remove the two `ext1` lines from `.gitignore`, then commit and push.
> - **Visibility.** Do not make the repo public or link it from the submission during double-blind review.
>
> **Update, Nov 15 ~16:50 (Claude): EXTENSION 1 RUNNING (overnight).**
> - **Setup.** The protocol is `outputs/robot_repair_study/extension1_protocol.md`. Its materials (39 files) were frozen at 16:47 in `extension1_frozen_hashes.json`. It tests 24 seeded random edits plus A and B on a fresh scene draw: 3,800 rollouts, about 7–9 hours.
> - **Queue.** `work/run_extension1.ps1`, launched about 16:48. It logs to `work/ext1_queue.log`, writes results under `outputs/robot_repair_study/results/ext1/`, and keeps a ledger at `results/ext1/ext1_batch_ledger.json`.
> - **If it stopped** (app quit, reboot): rerun `work/run_extension1.ps1` from the project root. It is resumable: it skips completed batches, preserves partial ones as `failed<n>_*` and reruns them whole. Never start it twice concurrently.
> - **After completion:**
>   - run `analyze_audit.py` on `results/ext1`, with all 26 candidate audit folders in queue order (A, B, r01–r24);
>   - then run `analyze_population.py` with `--first-audit results/audit_analysis.json`;
>   - add the results to the paper as a clearly labelled post-hoc extension.
>
> **Update, Nov 15 ~16:30 (Claude): audit COMPLETE.**
> - **Results.** See `outputs/audit_report.md`. The gate decisions and analysis are in `outputs/robot_repair_study/results/audit_gate_decisions.json` and `audit_analysis.json`.
> - **Paper.** `paper/main.tex` is fully filled in, with no pending markers. It compiles to `paper/main.pdf`: 3-page body plus 1 page of references. Tables are generated by `paper/make_tables.py`; the figure is `paper/fig_audit_map.pdf`.
> - **Artifact.** `artifact/robot_repair_artifact.zip` is built by `work/package_artifact.py`, which refuses to package if identifying strings remain.
> - **Not done, and needs the user:** final read-through, organizer confirmation of the page rules, author and OpenReview details, artifact hosting, and submission.
>
> **Earlier update, Nov 15 ~15:15 (Claude):**
> - **Pilot queue finished.** All three batches completed cleanly. The pilot is analyzed in `outputs/repair_pilot_report.md`.
> - **Correction.** The radial grid was **44/45**, not 45/45 as stated below: `r75_a+60` repeat 1 missed at 0.0308 m.
> - **Frozen audit running.** The protocol is in `outputs/robot_repair_study/audit_protocol.md`; hashes are in `audit_frozen_hashes.json` and `audit_frozen_hashes_amendment1.json`. The amendment is an infrastructure fix for PowerShell 5.1 stderr handling.
> - **Queue.** `work/run_audit_batches.ps1` was launched about 15:08. It runs validation (3×20), commits gate decisions to `results/audit_gate_decisions.json`, then the audit (3×160), then a parent repeat (20).
> - **Progress.** Check `results/audit_batch_ledger.json` and the `results/audit_*` folders. Do not start a second simulator, and do not overwrite.
> - **After completion.** Run `analyze_audit.py` and `plot_audit_map.py` (commands in the protocol and scripts), fill the `\PENDING` markers in `paper/main.tex`, then run `work/package_artifact.py`.
> - **LaTeX.** MiKTeX 25.12 was installed per-user on Nov 15, with the user's approval, at `%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64`. Package auto-install is enabled.
>   - **Compile:** in `paper/`, run `pdflatex main`, `bibtex main`, then `pdflatex main` twice.
>   - **Render pages for inspection:** `mgs.exe -q -dNOPAUSE -dBATCH -sDEVICE=png16m -r110 -o page%d.png main.pdf`. Ghostscript ships with MiKTeX; no poppler or PyMuPDF is installed.
>   - **Status:** the draft compiles cleanly with the official AAAI-27 style: 3 pages, with the audit results still pending.

Checkpoint: November 15, 2026, approximately 13:05 America/Los_Angeles. Read this file first, then inspect live files: the experiment queue may have advanced since this checkpoint.

## User objective and authorization

Help produce the strongest defensible AI-agent/robotics workshop submission before November 20. The user authorized installing Isaac Sim on Windows, setting up scenes, and autonomously running experiments. They have simulator/GPU access and want execution, not just suggestions. Do not promise acceptance or publication by the deadline. The latest request is to prepare this handoff for Claude, especially if Codex usage is exhausted.

Workspace: `C:\Users\Jonat\Documents\Codex\2026-11-15\t`

No paper has been submitted. No model API or OpenReview account has been configured in this project. Do not send emails or submit a manuscript without the user's explicit final instruction and accurate author information. Continue reversible local experiments and manuscript preparation autonomously.

## FIRST: check the running batch; do not duplicate it

An existing PowerShell queue is running `work\run_repair_batches.ps1`. It sequentially executes:

1. `radial_candidate_a`: lower lift height to 0.20 m, 25 scenes x 3 resets = 75 rollouts.
2. `radial_candidate_b`: motion convergence tolerance 0.025 m, same 75 rollouts.
3. `radial_parent_repeat`: unchanged parent, same 75 rollouts.

At the last inspection A had **25/75 completed, all 25 successful**. B and repeated parent had not started. This is a partial observation, NOT the pilot result. The target scene is late in the ordered panel and had not yet been evaluated under A. The original target parent failed three times.

Codex tool session ID is 18095 (this is NOT a Windows PID and may be unusable outside this chat). The queue records `outputs\robot_repair_study\results\repair_batch_ledger.json` after each completed batch. Absence of that file while the first batch runs is expected. Logs are `work\radial_candidate_a.log`, `work\radial_candidate_b.log`, and `work\radial_parent_repeat.log`.

Use these PowerShell checks from the workspace:

```powershell
foreach ($batchName in @('radial_candidate_a','radial_candidate_b','radial_parent_repeat')) {
    $batchFolder = Join-Path 'outputs\robot_repair_study\results' $batchName
    if (Test-Path $batchFolder) {
        $rows = @(Get-ChildItem $batchFolder -Filter 'rollout_*.json' | ForEach-Object { Get-Content $_.FullName -Raw | ConvertFrom-Json })
        '{0}: {1}/75 completed; {2} successes' -f $batchName,$rows.Count,@($rows | Where-Object object_state_success).Count
    }
}
Get-Content work\radial_candidate_a.log -Tail 3
Get-Content outputs\robot_repair_study\results\repair_batch_ledger.json -ErrorAction SilentlyContinue
```

Check again after a short interval to establish whether counts/logs are advancing. CIM process inspection was denied in this sandbox, so no OS PID was verified. Do not assume the queue survived a chat/app transition. Do not start a second simulator concurrently. Do not overwrite any partial run. If the process has stopped, preserve partial data and logs and launch only unfinished batches into new directories, documenting the restart. The queue intentionally refuses to overwrite an existing output directory.

## Current research scope

Working title: **Repair Without Regression? Budget-Matched Auditing of Agent-Edited Robot Skills.** This remains an initial proposal, not a completed main study.

Question: when an agent changes a persistent robot controller to repair a failure, does aggregate success conceal losses on earlier successful scenes? Compare aggregate and preservation-aware admission using identical candidate evidence, and account for useful updates rejected.

Do NOT claim a novel regression-testing principle, general autonomous robot-learning algorithm, improved VLA training, or safety guarantee. No neural policy has been trained. Current interventions are bounded parameter edits to NVIDIA's scripted Franka controller. Candidate generation is interactive Codex assistance; no frozen, independently sampled model client exists. A careful case study is possible; the proposed broad empirical study is not yet qualified by evidence.

Theoretical sanity check: old net improvement = gains minus losses. If every parent old-scene result succeeds, no old gains are possible, and aggregate nondegradation already excludes losses. A meaningful contrast requires target improvement AND old losses compensated by old gains. Do not manipulate parent quality, thresholds, or held-out scenes to engineer that pattern.

## What is complete

- Windows Isaac Sim 6.2.0.0, Python 3.12, PyTorch 2.11.0+cu128 installed and verified.
- GPU: RTX 4070 Ti SUPER, 16 GB VRAM; approximately 32 GB system RAM. The stock task uses CPU physics at 60 Hz. GPU availability is not GPU-parallel physics training.
- Stock Franka headless execution works. Six audit unit tests pass; they use synthetic fixtures, not robot data.
- Evaluator v2 uses simulator object measurements separately from controller status: lift above 0.0758 m; final 30 frames within 0.03 m of goal; grasp-frame separation >0.08 m; linear speed <0.02 m/s; angular speed <0.1 rad/s; orientation drift <0.05 rad; finish strictly before the horizon.
- Four negative controls rejected: no motion, no grasp, held at goal, one-step timeout. Several controls violate multiple predicates, so do not call them isolated tests of every predicate.
- Original twelve development scenes: 36/36 successful placements (six in feasibility_v2, six in remaining_development, three resets each).
- Additional radial grid: radii 0.35, 0.55, 0.75 m x angles -60,-30,0,30,60 degrees: 45/45 successful placements.
- Boundary grid: radii 0.80 and 0.85 m at the same angles, three resets each: 30 completed runs; the observed boundary traces fail in LIFT at 0.80 m and APPROACH_PICK at 0.85 m. Read summary.json for definitive counts; do not rely solely on this prose.
- First failure target selected by documented manifest-order rule: `r80_a-60`. Three parent failures: LIFT timed out at 5 seconds with approximately 0.0203 m position error (parent convergence tolerance 0.015 m). Object lifted, not placed.
- Two proposal JSONs and rationale saved BEFORE candidate execution. A changes lift height from 0.30 to 0.20. B changes position tolerance from 0.015 to 0.025; separately stored grasp tolerance remains unchanged. Neither changes the evaluator.

All these scenes and results are DEVELOPMENT data, not final audit data. Failure discovery was adaptive in documented stages. Do not treat the searched boundary failure frequency as a population estimate.

## Important files

All paths below are relative to the workspace:

- `outputs\research_plan.md`: authoritative staged plan, plus clearly superseded historical notes.
- `outputs\review_response.md`: answers to the user's pasted research review; original status table is preserved as a historical pre-install audit, with a later update at the top.
- `outputs\day1_feasibility_report.md`: verified installation/evaluator results and limitations.
- `outputs\literature_update.md`: additional close work and submission requirements.
- `outputs\initial_paper.md` and `.pdf`: initial pre-experiment manuscript. Preserve it as history; write a new evidence-based revision. PDF is NOT venue-formatted.
- `outputs\robot_repair_study\run_stock_scene.py`: simulator runner.
- `outputs\robot_repair_study\audit.py`, `test_audit.py`: paired admission metrics, six tests.
- `outputs\robot_repair_study\pilot_protocol.md`, `radial_development_rule.md`, `boundary_development_rule.md`: development protocol and amendments.
- `outputs\robot_repair_study\proposals\proposal_record.md`, `candidate_a.json`, `candidate_b.json`, `frozen_hashes.json`: intervention provenance.
- `outputs\robot_repair_study\combined_development_scenes.json`: all 25 radial/boundary scenes, ordered, three repetitions per scene in active batches.
- `outputs\robot_repair_study\results\`: raw metadata, source snapshots, trajectories, rollout JSONs, summaries. Preserve everything.
- `outputs\robot_repair_study\summarize_runs.py`: validates runner hash and summarizes any completed run folder.
- `outputs\robot_repair_study\compare_pilot.py`: complete-panel comparison; requires identical scene manifests, paired labels, and evaluator definitions. Produces all four paired cells, target/old metrics, diagnostic full-panel gate decisions.
- `outputs\robot_repair_study\plot_pilot.py`: descriptive success heatmap, assumes exactly three repeats per scene. It was created but has NOT yet been run/visually checked.
- `outputs\robot_repair_study\environment-lock.txt`: pip freeze.
- `work\launch_isaac.ps1`: working machine-specific launch wrapper.
- `work\run_repair_batches.ps1`: active sequential queue, exits on incomplete batch, no overwrite.

The original pasted review is at `C:\Users\Jonat\.codex\attachments\6400a71d-8b40-4152-9300-2c2aae698598\Pasted text.txt` if needed.

## Runtime details and known pitfalls

Interpreter: `C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe`.

Use launch_isaac.ps1, not a bare Python invocation. It sets EULA acceptance, local Omni configuration, portable root, and writable Warp/CUDA caches. Earlier launches stalled without network access; network permission was granted for the current Codex turn and may need renewal in another agent/session. Explain that permission is for Isaac's required assets. Earlier Warp compilation failed with its default cache; the local cache resolves it. A Documents/Kit/shared warning does not prevent these runs. Do not attempt unnecessary writes outside the project to silence it.

Current successful baseline execution plus evaluation is about 6.5 seconds/rollout, with slower/faster cases. Startup and reset add overhead. One 75-rollout batch can take several minutes. Keep the user informed at meaningful progress points. All simulation is serial; no parallelism has been validated.

Reset outcomes are not bit-identical in every scene. A fresh parent panel is part of this pilot. Paired repeat labels do not guarantee identical hidden simulator state. Compare repeated-parent outcome changes before attributing gains/losses solely to edits. Do not turn 75 rollouts into 75 independent repair samples: there is one selected target and two proposals.

## Next execution steps

1. Monitor/complete the existing three-batch queue, preserving failures. Require 75 records and a zero process exit for each complete batch.
2. Run summaries on each final folder. Verify source hashes and proposal hashes. Inspect target, old losses, old gains, and failure reasons.
3. Compare the two candidates to the complete repeated parent:

```powershell
& 'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe' outputs\robot_repair_study\compare_pilot.py --parent outputs\robot_repair_study\results\radial_parent_repeat --comparisons outputs\robot_repair_study\results\radial_candidate_a outputs\robot_repair_study\results\radial_candidate_b --target r80_a-60 --output outputs\robot_repair_study\results\pilot_comparison.json
& 'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe' outputs\robot_repair_study\plot_pilot.py outputs\robot_repair_study\results\pilot_comparison.json outputs\pilot_success_heatmap.png
```

4. Separately compare initial radial/boundary parent outcomes with the repeated-parent panel by (scene_id, repeat_within_scene). The discovery parent comes from TWO original run folders; do not fabricate a combined run's metadata or source hash. Report any parent-parent transitions as reset/order diagnostics.
5. Write `outputs\repair_pilot_report.md`, including every proposal and denominator, elapsed costs, component failures, reset diagnostics, and an explicit go/no-go decision. Full-panel gates are NOT the planned matched 24-rollout validation experiment. No final audit currently exists.
6. Revise the manuscript around measured evidence. If informative repairs and compensated regressions occur, decide and freeze a small independent audit before collecting it. If not, transparently narrow to a pilot/position paper or defer. Do not launch thousands of main-study episodes merely because a simulator works.
7. Prepare a properly formatted, anonymized manuscript and artifact for user review before submission.

## Venue and formatting

Target: https://trust4rsi-agent.github.io/AAAI2027/

Verified November 15: deadline November 20, 2026 AoE; intended submission November 19; short/position papers four pages; double-blind; non-archival. References/appendices wording says "usually" excluded, so verify the actual submission instructions before relying on extra pages. Submission does not imply acceptance/publication by November 20.

Official author kit downloaded from https://aaai.org/authorkit27/ to `work\aaai27-author-kit\AuthorKit27`. It includes aaai2027.sty/bst and the anonymous template.

IMPORTANT: portable Tectonic 0.17.0 was downloaded to `work\tectonic`, but its smoke compile FAILED. The official style explicitly requires pdfTeX and rejects XeTeX. Do NOT bypass or edit the official style to make Tectonic work. Use a real pdfLaTeX distribution (or the user's Overleaf), or provide checked source while clearly stating compilation is pending. Failure log: `work\tex-smoke.log`. No new submission PDF exists.

For a review-only PDF, bundled ReportLab/Poppler are available under the Codex primary runtime, but that does not reproduce the official template. If making a final PDF, render and inspect every page. The PDF skill was read and its artifact-operation marker was already executed once earlier in this conversation for the initial draft.

## Literature and honest claims

Primary records checked:

- https://arxiv.org/abs/2609.10873 — Ma/Wu, update-admission budget and missed-opportunity auditing.
- https://arxiv.org/abs/2611.06863 — Aphale/Singh, robot code-policy retry controls.
- https://arxiv.org/abs/2609.19906 — Kuroki et al., simulation-guided closed-loop robot software.
- https://arxiv.org/abs/2610.34577 — Zhang et al., agent-harness verification designs.
- https://arxiv.org/abs/2606.19980 — ENPIRE, physical robot self-improvement harness.
- https://arxiv.org/abs/2607.24604 — Gao et al., retention versus repair and evidence tied to exact code states.
- https://arxiv.org/abs/2607.28871 — Xu/Wu, adequacy of validation evidence in repair agents.

These overlap substantially with broad novelty claims. The strongest potential contribution here is tightly controlled robot evidence about directional gains/losses, not invention of a verifier. Nothing so far establishes general agent competence, physical safety, or superiority of a gate.

## Handoff boundaries

Claude needs local filesystem and shell access to execute this project. A browser-only Claude chat can review uploaded files but cannot run the existing Windows simulator. No data was sent to Claude by Codex. No external account usage balance is visible; do not claim a known remaining token/account quota. If access is unavailable, ask the user to open this folder in their coding environment rather than inventing experiment results.
