# Audit amendment 1: infrastructure only

November 15, 2026, ~15:10 America/Los_Angeles. This was made before any audit or validation rollout existed.

## What happened

The first queue launch, at 15:05, failed during Isaac Sim startup and produced zero rollouts. No scene outcome was observed.

The cause was a shell behaviour, not the simulator. This session runs Windows PowerShell 5.1, not PowerShell 7. In 5.1, when a native program's stderr is redirected under `$ErrorActionPreference = 'Stop'`, every stderr line becomes a terminating `NativeCommandError`. Isaac's routine warning "Possible version incompatibility … carb::ujitso::IFactory" therefore aborted `launch_isaac.ps1` at line 15. The earlier Codex batches did not hit this, presumably because they ran under a different PowerShell host.

The evidence is preserved:

- `results/failed_launch1_audit_validation_parent/` (empty folder)
- `work/failed_launch1_audit_validation_parent.log`
- `work/failed_launch1_audit_queue.log`
- `work/failed_launch1_queue_stderr.txt`

## Change

- **New launcher.** Added `work/launch_isaac_ps51.ps1`. It uses the same interpreter, environment variables and arguments as `launch_isaac.ps1`, but starts Python with `Start-Process`, so stdout goes to the batch log and stderr to `<log>.err`.
- **Queue.** `work/run_audit_batches.ps1` now calls this launcher. It also wraps the gate-script call in a local `$ErrorActionPreference = 'Continue'`.
- **Smoke test.** The launcher ran one stock-scene rollout into the session scratchpad, not into the results tree: exit 0, one rollout recorded.

**Unchanged:** the protocol, manifests, gate rules, analysis script, runner, proposals and evaluator. Their hashes in `audit_frozen_hashes.json` still match. New hashes for the two changed or added infrastructure files are in `audit_frozen_hashes_amendment1.json`.

## Deviation from protocol §7

§7 says a failed batch is rerun into a `_restart1` folder. That rule exists to keep partially observed ordered sequences separate. Here no rollout was produced. The empty folder was renamed to `failed_launch1_…` and the queue relaunched under its original folder names, so the frozen gate and analysis commands apply unchanged. Any failure *after* rollouts exist will follow §7 literally.
