$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Project root: $ProjectRoot"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv not found in PATH. Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
}

Push-Location $ProjectRoot
try {
    uv sync --group build
    uv run pyinstaller --noconfirm --clean --onefile --name twist main.py
}
finally {
    Pop-Location
}

$DistExe = Join-Path $ProjectRoot "dist\twist.exe"
if (!(Test-Path $DistExe)) {
    throw "Build failed: $DistExe not found"
}

Write-Host "Build success: $DistExe"
