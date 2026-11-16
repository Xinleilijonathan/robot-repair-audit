$ErrorActionPreference = 'Stop'
$studyRoot = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t'
$artifact = Join-Path $studyRoot 'outputs\robot_repair_study'
$jobs = @(
    @{ Name = 'radial_candidate_a'; Config = 'candidate_a.json' },
    @{ Name = 'radial_candidate_b'; Config = 'candidate_b.json' },
    @{ Name = 'radial_parent_repeat'; Config = $null }
)
$ledger = @()
foreach ($job in $jobs) {
    $destination = Join-Path $artifact ('results\' + $job.Name)
    if (Test-Path -LiteralPath $destination) { throw "Refusing to overwrite existing experiment folder: $destination" }
    $arguments = @('--output', $destination, '--repeats', '3', '--scene-manifest', (Join-Path $artifact 'combined_development_scenes.json'))
    if ($job.Config) { $arguments += @('--controller-config', (Join-Path $artifact ('proposals\' + $job.Config))) }
    $started = [DateTime]::UtcNow.ToString('o')
    $logPath = Join-Path $studyRoot ('work\' + $job.Name + '.log')
    & (Join-Path $studyRoot 'work\launch_isaac.ps1') -Script (Join-Path $artifact 'run_stock_scene.py') -ScriptArguments $arguments *> $logPath
    $exitStatus = $LASTEXITCODE
    $completed = @(Get-ChildItem -LiteralPath $destination -Filter 'rollout_*.json' -ErrorAction SilentlyContinue).Count
    $ledger += @{ batch = $job.Name; started_utc = $started; ended_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $exitStatus; completed_rollouts = $completed; expected_rollouts = 75 }
    ConvertTo-Json -InputObject $ledger -Depth 5 | Set-Content (Join-Path $artifact 'results\repair_batch_ledger.json')
    Write-Output ("BATCH_COMPLETE " + $job.Name + " exit=" + $exitStatus + " rollouts=" + $completed)
    if ($exitStatus -ne 0 -or $completed -ne 75) { throw 'Partial batch preserved; stopping for inspection.' }
}
