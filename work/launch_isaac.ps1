param(
    [Parameter(Mandatory=$true)][string]$Script,
    [string[]]$ScriptArguments = @()
)
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
& $isaacPython $Script @ScriptArguments --portable-root (Join-Path $studyRoot 'work\isaac_runtime')
exit $LASTEXITCODE
