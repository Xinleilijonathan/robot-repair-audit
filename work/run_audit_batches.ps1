$ErrorActionPreference = 'Stop'
$studyRoot = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t'
$artifact = Join-Path $studyRoot 'outputs\robot_repair_study'
$results = Join-Path $artifact 'results'
$python = 'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe'
$validationManifest = Join-Path $artifact 'audit_validation_scenes.json'
$auditManifest = Join-Path $artifact 'audit_scenes.json'
$ledgerPath = Join-Path $results 'audit_batch_ledger.json'
$gatePath = Join-Path $results 'audit_gate_decisions.json'

$steps = @(
    @{ Name = 'audit_validation_parent';        Config = $null;              Manifest = $validationManifest; Expected = 20 },
    @{ Name = 'audit_validation_candidate_a';   Config = 'candidate_a.json'; Manifest = $validationManifest; Expected = 20 },
    @{ Name = 'audit_validation_candidate_b';   Config = 'candidate_b.json'; Manifest = $validationManifest; Expected = 20 },
    @{ Name = '__gates__' },
    @{ Name = 'audit_parent';                   Config = $null;              Manifest = $auditManifest;      Expected = 160 },
    @{ Name = 'audit_candidate_a';              Config = 'candidate_a.json'; Manifest = $auditManifest;      Expected = 160 },
    @{ Name = 'audit_candidate_b';              Config = 'candidate_b.json'; Manifest = $auditManifest;      Expected = 160 },
    @{ Name = 'audit_validation_parent_repeat'; Config = $null;              Manifest = $validationManifest; Expected = 20 }
)
foreach ($s in $steps) {
    if ($s.Name -ne '__gates__' -and (Test-Path -LiteralPath (Join-Path $results $s.Name))) { throw "Refusing to overwrite existing folder: $($s.Name)" }
}
if (Test-Path -LiteralPath $gatePath) { throw 'Gate decisions already exist; refusing to rerun queue.' }

$ledger = @()
foreach ($s in $steps) {
    $started = [DateTime]::UtcNow.ToString('o')
    if ($s.Name -eq '__gates__') {
        $gateLog = Join-Path $studyRoot 'work\audit_gates.log'
        $ErrorActionPreference = 'Continue'  # amendment 1: native stderr must not abort (PS 5.1)
        & $python -I (Join-Path $artifact 'audit_gates.py') --manifest $validationManifest `
            --parent (Join-Path $results 'audit_validation_parent') `
            --candidates (Join-Path $results 'audit_validation_candidate_a') (Join-Path $results 'audit_validation_candidate_b') `
            --output $gatePath *> $gateLog
        $exitStatus = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
        $ledger += @{ batch = 'gate_decisions'; started_utc = $started; ended_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $exitStatus }
        ConvertTo-Json -InputObject $ledger -Depth 5 | Set-Content -Encoding utf8 $ledgerPath
        Write-Output ("GATES_COMMITTED exit=" + $exitStatus)
        if ($exitStatus -ne 0 -or -not (Test-Path -LiteralPath $gatePath)) { throw 'Gate commit failed; stopping before audit.' }
        continue
    }
    $destination = Join-Path $results $s.Name
    $arguments = @('--output', $destination, '--repeats', '1', '--scene-manifest', $s.Manifest)
    if ($s.Config) { $arguments += @('--controller-config', (Join-Path $artifact ('proposals\' + $s.Config))) }
    $logPath = Join-Path $studyRoot ('work\' + $s.Name + '.log')
    # amendment 1: PS 5.1-safe launcher; stdout -> $logPath, stderr -> "$logPath.err"
    & (Join-Path $studyRoot 'work\launch_isaac_ps51.ps1') -Script (Join-Path $artifact 'run_stock_scene.py') -ScriptArguments $arguments -LogPath $logPath
    $exitStatus = $LASTEXITCODE
    $completed = @(Get-ChildItem -LiteralPath $destination -Filter 'rollout_*.json' -ErrorAction SilentlyContinue).Count
    $ledger += @{ batch = $s.Name; started_utc = $started; ended_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $exitStatus; completed_rollouts = $completed; expected_rollouts = $s.Expected }
    ConvertTo-Json -InputObject $ledger -Depth 5 | Set-Content -Encoding utf8 $ledgerPath
    Write-Output ("BATCH_COMPLETE " + $s.Name + " exit=" + $exitStatus + " rollouts=" + $completed + "/" + $s.Expected)
    if ($exitStatus -ne 0 -or $completed -ne $s.Expected) { throw 'Partial batch preserved; stopping for inspection.' }
}
Write-Output 'AUDIT_QUEUE_DONE'
