$ErrorActionPreference = "Stop"

function Test-CommandExists {
  param([string]$CommandName)

  return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

$pkgManager = if (Test-CommandExists "pnpm") { "pnpm" } else { "npm" }

if (-not (Test-CommandExists "uv")) {
  Write-Error "Missing required command: uv"
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start each service in its own PowerShell window so logs remain visible.
if (Test-CommandExists "livekit-server") {
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot'; livekit-server --dev"
} else {
  Write-Warning "livekit-server was not found. Skipping local LiveKit startup and using your configured LIVEKIT_URL instead."
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot\backend'; uv run python src/agent.py dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot\frontend'; $pkgManager run dev"

Write-Host "Started backend and frontend in separate PowerShell windows."
