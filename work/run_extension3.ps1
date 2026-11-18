param(
    [string]$ResultsDir = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\outputs\robot_repair_study\results\ext3',
    [string]$Launcher = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\work\launch_isaac_ps51_timeout.ps1',
    [string]$LogDir = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\work',
    [string]$IndexPath = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\outputs\robot_repair_study\proposals\ext3\index.json',
    [string]$ProposalDir = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t\outputs\robot_repair_study\proposals\ext3'
)
# Extension 3 queue (extension3_protocol.md §5). Same failure handling as Extensions 1-2: resumable;
# completed batches are skipped; incomplete ones are renamed failed<n>_<name> (data preserved) and
# rerun whole; one retry per batch. Audit parent, then every distinct agent edit (index order).
$ErrorActionPreference = 'Stop'
$studyRoot = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t'
$artifact = Join-Path $studyRoot 'outputs\robot_repair_study'
$results = $ResultsDir
$launcher = $Launcher
$runner = Join-Path $artifact 'run_stock_scene.py'
$aManifest = Join-Path $artifact 'ext1_audit_scenes.json'
$ledgerPath = Join-Path $results 'ext3_batch_ledger.json'
New-Item -ItemType Directory -Force -Path $results | Out-Null
# PS 5.1 emits a JSON array as ONE object; pipe through ForEach-Object to enumerate before counting.
$aExpected = @((Get-Content $aManifest -Raw | ConvertFrom-Json) | ForEach-Object { $_ }).Count
if ($aExpected -ne 120) { throw "Unexpected audit manifest size: $aExpected" }

# Keep the machine from idle-sleeping while this process runs (no system setting is changed).
Add-Type -Namespace Ext3 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Ext3.Power]::SetThreadExecutionState([uint32]2147483649)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

$index = Get-Content $IndexPath -Raw | ConvertFrom-Json
$candidates = @()
foreach ($c in @($index.candidates | ForEach-Object { $_ })) {
    if ($c.run -eq $true) {
        $cfg = Join-Path $ProposalDir ($c.id + '.json')
        if (-not (Test-Path -LiteralPath $cfg)) { throw "Missing proposal config $cfg" }
        $candidates += @{ Id = $c.id; Config = $cfg }
    }
}
Write-Output "EXT3_QUEUE candidates=$($candidates.Count)"

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
        $log = Join-Path $LogDir ('ext3_' + $name + '.log')
        if (Test-Path -LiteralPath $log) { Rename-Item -LiteralPath $log -NewName ('ext3_' + $name + '.attempt' + (Get-Date -Format 'HHmmss') + '.log') }
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

if (-not (Invoke-Batch 'audit_parent' $null $aManifest $aExpected 150)) { throw 'Parent audit failed twice; stopping.' }
foreach ($c in $candidates) { [void](Invoke-Batch ('audit_' + $c.Id) $c.Config $aManifest $aExpected 150) }
[void][Ext3.Power]::SetThreadExecutionState([uint32]2147483648)  # release: ES_CONTINUOUS only
Write-Output 'EXT3_QUEUE_DONE'
