param(
    [Parameter(Mandatory=$true)][string]$Script,
    [string[]]$ScriptArguments = @(),
    [Parameter(Mandatory=$true)][string]$LogPath,
    [Parameter(Mandatory=$true)][int]$TimeoutMinutes
)
# Extension 1 launcher: identical to launch_isaac_ps51.ps1 (audit amendment 1) plus a
# wall-clock timeout. On timeout the process tree is killed and exit code 124 is returned.
$ErrorActionPreference = 'Stop'
$studyRoot = 'C:\Users\Jonat\Documents\Codex\2026-11-15\t'
$isaacPython = 'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Scripts\python.exe'
$env:OMNI_KIT_ACCEPT_EULA = 'YES'
$env:OMNI_CONFIG_PATH = Join-Path $studyRoot 'work\omni_config'
$env:CUDA_CACHE_PATH = Join-Path $studyRoot 'work\isaac_runtime\cuda_cache'
$env:MPLCONFIGDIR = Join-Path $studyRoot 'work\isaac_runtime\matplotlib'
$env:PYTHONUNBUFFERED = '1'
$env:WARP_CACHE_PATH = Join-Path $studyRoot 'work\isaac_runtime\warp'
New-Item -ItemType Directory -Force -Path $env:CUDA_CACHE_PATH | Out-Null
$all = @($Script) + $ScriptArguments + @('--portable-root', (Join-Path $studyRoot 'work\isaac_runtime'))
$argString = ($all | ForEach-Object { '"' + $_ + '"' }) -join ' '
$process = Start-Process -FilePath $isaacPython -ArgumentList $argString -NoNewWindow -PassThru `
    -RedirectStandardOutput $LogPath -RedirectStandardError ($LogPath + '.err')
$null = $process.Handle
if (-not $process.WaitForExit($TimeoutMinutes * 60 * 1000)) {
    Add-Content -Path ($LogPath + '.err') -Value ("LAUNCHER_TIMEOUT after $TimeoutMinutes minutes; killing process tree " + $process.Id)
    & taskkill.exe /PID $process.Id /T /F | Out-Null
    $process.WaitForExit(60000) | Out-Null
    exit 124
}
exit $process.ExitCode
