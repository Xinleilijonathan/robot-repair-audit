# Extension 1 queue (extension1_protocol.md §6). Resumable: completed batches are skipped,
# incomplete ones are renamed failed<n>_<name> (data preserved) and rerun whole; one retry.
$ErrorActionPreference = 'Stop'
$studyRoot = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t'
$artifact = Join-Path $studyRoot 'outputs\robot_repair_study'
$results = Join-Path $artifact 'results\ext1'
$python = 'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe'
$launcher = Join-Path $studyRoot 'work\launch_isaac_ps51_timeout.ps1'
$runner = Join-Path $artifact 'run_stock_scene.py'
$vManifest = Join-Path $artifact 'ext1_validation_scenes.json'
$aManifest = Join-Path $artifact 'ext1_audit_scenes.json'
$ledgerPath = Join-Path $results 'ext1_batch_ledger.json'
$gatePath = Join-Path $results 'audit_gate_decisions.json'
New-Item -ItemType Directory -Force -Path $results | Out-Null

# Keep the machine from idle-sleeping while this process runs (no system setting is changed).
Add-Type -Namespace Ext1 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Ext1.Power]::SetThreadExecutionState([uint32]2147483649)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

$index = Get-Content (Join-Path $artifact 'proposals\ext1\index.json') -Raw | ConvertFrom-Json
$candidates = @()
foreach ($c in $index.candidates) {
    $config = if ($c.origin -eq 'assistant') { Join-Path $artifact ('proposals\' + $c.id + '.json') } else { Join-Path $artifact ('proposals\ext1\' + $c.id + '.json') }
    $candidates += @{ Id = $c.id; Config = $config }
}

$ledger = New-Object System.Collections.ArrayList
if (Test-Path -LiteralPath $ledgerPath) { (Get-Content $ledgerPath -Raw | ConvertFrom-Json) | ForEach-Object { [void]$ledger.Add($_) } }
function Save-Ledger { ConvertTo-Json -InputObject @($ledger) -Depth 5 | Set-Content -Encoding utf8 $ledgerPath }
function Count-Rollouts($folder) { @(Get-ChildItem -LiteralPath $folder -Filter 'rollout_*.json' -ErrorAction SilentlyContinue).Count }

function Invoke-Batch($name, $config, $manifest, $expected, $timeout) {
    $folder = Join-Path $results $name
    $done = @($ledger | Where-Object { $_.batch -eq $name -and $_.exit_code -eq 0 -and $_.completed_rollouts -eq $expected })
    if ((Test-Path -LiteralPath $folder) -and (Count-Rollouts $folder) -eq $expected -and $done.Count -gt 0) {
        Write-Host "SKIP_COMPLETE $name"; return $true
    }
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        if (Test-Path -LiteralPath $folder) {
            $n = 1; while (Test-Path -LiteralPath (Join-Path $results ("failed{0}_{1}" -f $n, $name))) { $n++ }
            Rename-Item -LiteralPath $folder -NewName ("failed{0}_{1}" -f $n, $name)
            Write-Host ("PRESERVED_PARTIAL failed{0}_{1}" -f $n, $name)
        }
        $arguments = @('--output', $folder, '--repeats', '1', '--scene-manifest', $manifest)
        if ($config) { $arguments += @('--controller-config', $config) }
        $log = Join-Path $studyRoot ('work\ext1_' + $name + '.log')
        if (Test-Path -LiteralPath $log) { Rename-Item -LiteralPath $log -NewName ('ext1_' + $name + '.attempt' + (Get-Date -Format 'HHmmss') + '.log') }
        $started = [DateTime]::UtcNow.ToString('o')
        $null = & $launcher -Script $runner -ScriptArguments $arguments -LogPath $log -TimeoutMinutes $timeout
        $exitStatus = $LASTEXITCODE
        $count = Count-Rollouts $folder
        [void]$ledger.Add([pscustomobject]@{ batch = $name; attempt = $attempt; started_utc = $started; ended_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $exitStatus; completed_rollouts = $count; expected_rollouts = $expected })
        Save-Ledger
        Write-Host ("BATCH {0} attempt={1} exit={2} rollouts={3}/{4}" -f $name, $attempt, $exitStatus, $count, $expected)
        if ($exitStatus -eq 0 -and $count -eq $expected) { return $true }
    }
    Write-Host "BATCH_FAILED_TWICE $name"
    return $false
}

# 1. Validation
if (-not (Invoke-Batch 'audit_validation_parent' $null $vManifest 20 40)) { throw 'Parent validation failed twice; stopping.' }
$validated = @()
foreach ($c in $candidates) { if (Invoke-Batch ('audit_validation_' + $c.Id) $c.Config $vManifest 20 40) { $validated += $c } }

# 2. Commit gate decisions (once; before any audit batch)
if (-not (Test-Path -LiteralPath $gatePath)) {
    $ErrorActionPreference = 'Continue'
    $folders = @($validated | ForEach-Object { Join-Path $results ('audit_validation_' + $_.Id) })
    & $python -I (Join-Path $artifact 'audit_gates.py') --manifest $vManifest --parent (Join-Path $results 'audit_validation_parent') --candidates $folders --output $gatePath *> (Join-Path $studyRoot 'work\ext1_gates.log')
    $gateExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    [void]$ledger.Add([pscustomobject]@{ batch = 'gate_decisions'; ended_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $gateExit; candidates = $validated.Count })
    Save-Ledger
    if ($gateExit -ne 0 -or -not (Test-Path -LiteralPath $gatePath)) { throw 'Gate commit failed; stopping before audit.' }
    Write-Output "GATES_COMMITTED candidates=$($validated.Count)"
} else { Write-Output 'SKIP_COMPLETE gate_decisions' }
$gated = (Get-Content $gatePath -Raw | ConvertFrom-Json).candidates.PSObject.Properties.Name

# 3. Audit
if (-not (Invoke-Batch 'audit_parent' $null $aManifest 120 150)) { throw 'Parent audit failed twice; stopping.' }
foreach ($c in $candidates) { if ($gated -contains $c.Id) { [void](Invoke-Batch ('audit_' + $c.Id) $c.Config $aManifest 120 150) } }

# 4. Parent repeat check
[void](Invoke-Batch 'audit_validation_parent_repeat' $null $vManifest 20 40)
[void][Ext1.Power]::SetThreadExecutionState([uint32]2147483648)  # release: ES_CONTINUOUS only
Write-Output 'EXT1_QUEUE_DONE'
