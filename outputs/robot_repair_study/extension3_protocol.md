# Extension 3: agent-proposed repairs, with and without a loss history (frozen protocol)

**Frozen:** November 17, 2026, before any agent was asked for a proposal and before any Extension 3 rollout. SHA-256 values of the files in §7 are in `extension3_frozen_hashes.json`, committed and pushed before the agents are called. The proposals are hashed in a second record, `ext3_proposal_hashes.json`, committed and pushed before the first rollout.

**Status:** a confirmatory test, designed by Claude (Opus 5.5) at the user's request on Nov 17. It answers two limits stated in the paper: the earlier edits came from a random generator and two interactive repairs, not from agents; and the loss-history suite had only been tested on random edits.

## 1. Questions and hypotheses

- **H1 (primary).** Among distinct agent edits with at least one audit loss, the 8-scene history suite built from the 50 earlier candidates (§3) detects a loss more often than an 8-scene uniform suite is expected to.
  - **Detection** is read from the audit: at least one of the edit's lost old successes is in the suite. Extension 2 showed that a separately run suite batch can differ from the audit on near-threshold labels (17/384) because of run order; reading the audit removes that source.
  - **Uniform expectation:** 1 − C(n − m, 8) / C(n, 8), with n the parent's old successes (73) and m the edit's losses.
  - **Test:** mean paired difference over edits, bootstrap 95% CI (10,000 resamples, seed 20261132).
  - **Criterion:** H1 is supported if and only if the CI's lower bound is above 0. If fewer than 5 distinct edits have losses, H1 is not tested and is reported as inconclusive.
- **Secondary questions** (reported whatever the outcome):
  - **S1.** How many agent edits improve the target, how many of those lose old successes (Wilson 95%), and whether any improves the target with zero losses.
  - **S2.** Memory vs blind prompts (proposals as units): mean old losses, mean target change, target improvers, loss-free improvers, aggregate-useful edits; two-sided permutation test on mean old losses (10,000 permutations, seed 20261134). With about 10 proposals per condition this is descriptive.
  - **S3.** Per-agent and per-proposal outcomes.
  - **S4.** Agent edits against the 50 earlier edits: share of target improvers with losses, mean conditional loss.
  - **S5.** The frozen Extension 2 history suite and the k = 4 suites on agent edits; the share of agent losses that fall on the history suite against 8/73.
  - **S6.** Replay: the Extension 3 audit parent against the Extension 1 audit parent (120 labels).

## 2. Agents, prompts and proposals

**Agents** (`ext3_agents.json`). Five agents from three vendors, each called through its own command-line tool:

| Agent | Tool (version) | Model requested |
|---|---|---|
| claude-opus | Claude Code 2.1.327 | `opus` (Claude Opus 5.5) |
| claude-sonnet | Claude Code 2.1.327 | `sonnet` (Claude Sonnet 5.5) |
| claude-haiku | Claude Code 2.1.327 | `haiku` (Claude Haiku 5.5) |
| gpt | Codex CLI 0.170.0 | `gpt-6-astra`, reasoning effort high |
| gemini | Gemini CLI 0.68.0 | the CLI's default model |

The models each tool reports are recorded. The protocol designer is itself a Claude model; claude-opus is the same model, but each proposal comes from a fresh session that has none of this conversation.

**Conditions.** `ext3_prompts/blind.md` and `ext3_prompts/memory.md`, written by `make_ext3_materials.py`:
- **Both prompts contain:** the system and task; the six-parameter interface with current values, bounds and meanings; the full source of the installed `PickPlaceController` (`pick_place.py`, hash in `ext3_suites.json`); the development target failure (radius 0.80 m, angle −60°, LIFT timeout with 0.0203 m error against a 0.015 m tolerance); the development success counts; the scoring rule; and the goal: fix the failure without breaking scenes the controller already solves.
  - This is the information the two interactive repairs A and B were based on.
- **Memory adds:** the record of the 50 earlier edits on the audit panel (parameters, target scenes gained and lost, old successes broken and old failures fixed), the 10 most-often-broken old scenes (radius, angle, count), and two computed facts: none of the 21 target-improving edits avoided losses, and 191 of 260 losses were placement errors of 3.0–4.7 cm.
- **Neither prompt contains:** the audit scene list, any Extension 3 result, the paper, or the history-suite membership as such. Memory agents see the coordinates of the 10 most-broken scenes.

**Samples.** Two proposals per agent per condition: 20 proposals in all.

**Isolation** (`run_ext3_agents.py`):
- Each proposal is one fresh, non-interactive session, started in a new empty directory outside the project, with the frozen prompt on stdin.
- **Claude:** no tools at all (`--tools ""`), safe mode, no MCP servers, no session persistence.
- **Codex:** ephemeral session, user config and rules ignored, read-only sandbox; shell, unified exec, apps, plugins, browser, computer use, image generation and memories disabled.
- **Gemini:** read-only plan mode, workspace trusted for the session only.
- Every transcript is saved. The working directory must still be empty afterwards.

**Exclusion rules** (fixed now):
- A proposal is re-requested once, in a fresh session, if the tool errors or times out (15 min), uses an information-access tool (file read or write, shell command, MCP tool, web search), or returns no valid edit.
- After a second failure it is excluded and reported, not replaced.
- An agent that cannot authenticate at collection time contributes no proposals; this is reported.

**Valid edit:** a JSON object whose `overrides` name 1–6 of the six parameters, each numeric and within the runner's bounds after rounding to 3 decimals. Values are rounded to 3 decimals, as for the random edits.

**Duplicates and no-ops:**
- An exact duplicate of an earlier proposal (index order: agents as listed, then blind before memory, then sample) is recorded but not run.
- An edit equal to the stock values is a no-op: it is not run and is analysed as identical to the parent, by exact replay.
- An edit that equals one of the 50 earlier edits is run anyway; its agreement with the earlier audit is reported as a replay check.

## 3. Regression panel and suites

**Panel.** The Extension 1 audit panel (`ext1_audit_scenes.json`: 30 target and 90 old scenes; the parent solves 10 target and 73 old scenes), in its original order. It is reused by design: a loss history is defined over fixed scenes.

**History suite** (`ext3_suites.json`).
- **Pool:** the 73 old parent successes, ranked by how many of the 50 earlier candidates lost them. The 50 are Extension 1's A, B and r01–r24, and Extension 2's r25–r48, each scored against its own audit parent.
- **Ties:** broken by a seeded random order (seed 20261131).
- **Members**, with loss counts out of 50: ao020 (19), ao083 (15), ao052 (12), ao017 (12), ao002 (11), ao022 (10), ao064 (9), ao034 (9).
- **k = 4 secondary suite:** the first 4 of these.
- **Secondary suite:** the frozen Extension 2 suite, which overlaps on 5 scenes.

## 4. Audit

The parent and every distinct agent edit run the full 120-scene panel, one rollout per scene, in the same order. Usefulness is defined as before:
- **aggregate:** target net > 0 and old net ≥ 0;
- **zero-loss:** target net > 0 and no losses;
- **secondary:** conditional loss ≤ 5%.

## 5. Execution (`work/run_extension3.ps1`)

**Order:**
1. The audit parent.
2. Every distinct edit, in index order.

That is at most 21 × 120 = 2,520 rollouts, about 5 hours serial.

**Failure handling:** the same timeout launcher as before, 150 minutes per batch. A failed batch is renamed `failed<n>_<name>` and rerun whole, once. An edit whose audit fails twice is excluded and reported. The queue is resumable and never overwrites. An idle-sleep request is held while it runs.

**Dry runs.** These were run before freezing, on clearly labelled stand-in data in a scratch directory:
- **Queue:** run with a fake launcher that writes empty rollout files and never starts the simulator. It also checked resuming.
- **Analysis:** run with Extension 2 audit folders relabelled as fake agent edits. Those numbers are meaningless because the edits are in-sample.
- **Bug fixed:** the queue's batch messages were switched to host output so that a failed batch stops the queue.
- **Agent tools:** a smoke test with a trivial prompt checked that the tools start without information-access tools.

**Ordering guarantee.** No result triggers any change. The proposals are collected once, hashed, committed and pushed before the first rollout.

## 6. Analysis (`analyze_ext3.py`)

- **Unit:** the distinct edit for H1, S1, S4 and S5; the proposal for S2 and S3.
- **Losses:** relative to the Extension 3 audit parent.
- **Reporting:** all outputs are reported whatever their direction. Intervals describe these agents and prompts on one panel, robot, task and context.

## 7. Frozen files

- **Protocol and materials:** this protocol; `make_ext3_materials.py`; `ext3_suites.json`; `ext3_prompts/blind.md`; `ext3_prompts/memory.md`; `ext3_agents.json`.
- **Collection and analysis:** `run_ext3_agents.py`; `analyze_ext3.py`; `analyze_ext2.py`, whose helpers it imports.
- **Queue and simulator:** `work/run_extension3.ps1`; `work/launch_isaac_ps51_timeout.ps1`; `run_stock_scene.py`.
- **Inputs:** `ext1_audit_scenes.json`; the installed controller source `pick_place.py`.

## 8. What was known before freezing

Everything in the paper and in the Extension 1 and 2 reports:
- all 21 earlier target improvers lost old successes;
- the Extension 2 history suite detected losses in 14 of 20 lossy random edits, against 36% expected;
- the Extension 2 run-context sensitivity.

No agent had been asked for a proposal. Apart from the smoke test's trivial prompt, no command-line agent had been called.
