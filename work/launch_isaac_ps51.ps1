param(
    [Parameter(Mandatory=$true)][string]$Script,
    [string[]]$ScriptArguments = @(),
    [Parameter(Mandatory=$true)][string]$LogPath
)
# Windows PowerShell 5.1 variant of launch_isaac.ps1 (audit amendment 1).
# Identical interpreter, environment and arguments; the interpreter is started with
# Start-Process so that harmless native stderr warnings (e.g. the carb ujitso version
# notice) are written to "$LogPath.err" instead of becoming terminating PowerShell errors.
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
$null = $process.Handle  # cache the handle so ExitCode is available after exit
$process.WaitForExit()
exit $process.ExitCode
