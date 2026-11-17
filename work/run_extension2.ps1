param(
    [string]$ResultsDir = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\outputs\robot_repair_study\results\ext2',
    [string]$Launcher = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\work\launch_isaac_ps51_timeout.ps1',
    [string]$LogDir = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\work'
)
# Extension 2 queue (extension2_protocol.md §7). Same structure and failure handling as Extension 1:
# resumable; completed batches are skipped; incomplete ones are renamed failed<n>_<name> (data
# preserved) and rerun whole; one retry per batch. Suite batches -> commit gates -> audits -> repeat.
$ErrorActionPreference = 'Stop'
$studyRoot = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t'
$artifact = Join-Path $studyRoot 'outputs\robot_repair_study'
$results = $ResultsDir
$python = 'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe'
$launcher = $Launcher
$runner = Join-Path $artifact 'run_stock_scene.py'
$vManifest = Join-Path $artifact 'ext2_validation_scenes.json'
$aManifest = Join-Path $artifact 'ext1_audit_scenes.json'
$suites = Join-Path $artifact 'ext2_suites.json'
$ledgerPath = Join-Path $results 'ext2_batch_ledger.json'
$gatePath = Join-Path $results 'ext2_gate_decisions.json'
New-Item -ItemType Directory -Force -Path $results | Out-Null
# PS 5.1 emits a JSON array as ONE object; pipe through ForEach-Object to enumerate before counting.
$vExpected = @((Get-Content $vManifest -Raw | ConvertFrom-Json) | ForEach-Object { $_ }).Count
$aExpected = @((Get-Content $aManifest -Raw | ConvertFrom-Json) | ForEach-Object { $_ }).Count
if ($vExpected -ne 20 -or $aExpected -ne 120) { throw "Unexpected manifest sizes: suite=$vExpected audit=$aExpected" }

# Keep the machine from idle-sleeping while this process runs (no system setting is changed).
Add-Type -Namespace Ext2 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Ext2.Power]::SetThreadExecutionState([uint32]2147483649)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

$index = Get-Content (Join-Path $artifact 'proposals\ext2\index.json') -Raw | ConvertFrom-Json
$candidates = @()
foreach ($c in $index.candidates) { $candidates += @{ Id = $c.id; Config = (Join-Path $artifact ('proposals\ext2\' + $c.id + '.json')) } }

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
        $log = Join-Path $LogDir ('ext2_' + $name + '.log')
        if (Test-Path -LiteralPath $log) { Rename-Item -LiteralPath $log -NewName ('ext2_' + $name + '.attempt' + (Get-Date -Format 'HHmmss') + '.log') }
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

# 1. Suite (validation) batches
if (-not (Invoke-Batch 'ext2_validation_parent' $null $vManifest $vExpected 40)) { throw 'Parent suite batch failed twice; stopping.' }
$validated = @()
foreach ($c in $candidates) { if (Invoke-Batch ('ext2_validation_' + $c.Id) $c.Config $vManifest $vExpected 40) { $validated += $c } }

# 2. Commit gate decisions (once; before any audit batch)
if (-not (Test-Path -LiteralPath $gatePath)) {
    $ErrorActionPreference = 'Continue'
    $folders = @($validated | ForEach-Object { Join-Path $results ('ext2_validation_' + $_.Id) })
    & $python -I (Join-Path $artifact 'ext2_gates.py') --manifest $vManifest --suites $suites --parent (Join-Path $results 'ext2_validation_parent') --candidates $folders --output $gatePath *> (Join-Path $LogDir 'ext2_gates.log')
    $gateExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    [void]$ledger.Add([pscustomobject]@{ batch = 'gate_decisions'; ended_utc = [DateTime]::UtcNow.ToString('o'); exit_code = $gateExit; candidates = $validated.Count })
    Save-Ledger
    if ($gateExit -ne 0 -or -not (Test-Path -LiteralPath $gatePath)) { throw 'Gate commit failed; stopping before audit.' }
    Write-Output "GATES_COMMITTED candidates=$($validated.Count)"
} else { Write-Output 'SKIP_COMPLETE gate_decisions' }
$gated = (Get-Content $gatePath -Raw | ConvertFrom-Json).candidates.PSObject.Properties.Name

# 3. Audit on the Extension 1 panel (same 120 scenes, same order)
if (-not (Invoke-Batch 'audit_parent' $null $aManifest $aExpected 150)) { throw 'Parent audit failed twice; stopping.' }
foreach ($c in $candidates) { if ($gated -contains $c.Id) { [void](Invoke-Batch ('audit_' + $c.Id) $c.Config $aManifest $aExpected 150) } }

# 4. Parent repeat check
[void](Invoke-Batch 'ext2_validation_parent_repeat' $null $vManifest $vExpected 40)
[void][Ext2.Power]::SetThreadExecutionState([uint32]2147483648)  # release: ES_CONTINUOUS only
Write-Output 'EXT2_QUEUE_DONE'
