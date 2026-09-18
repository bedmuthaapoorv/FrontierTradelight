# Double-click launcher for the FrontierTradeLight app (FastAPI backend +
# React frontend) on Windows - the PowerShell counterpart to
# "Start FrontierTradeLight.command" (the Mac version). Starts both
# servers, waits for the frontend to come up, opens it in your default
# browser, and stops both servers together when this window is closed or
# Ctrl+C is pressed.
#
# Launched via the sibling "Start FrontierTradeLight.bat" so double-clicking
# in Explorer works without a PowerShell execution-policy prompt.

$ErrorActionPreference = 'Stop'

# Resolve this script's own directory so it works regardless of where it's
# double-clicked from or copied to.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$BackendPort = 8000
$FrontendPort = 5173
$ViteJs = "frontend\node_modules\vite\bin\vite.js"

Write-Host "FrontierTradeLight"
Write-Host "=================="
Write-Host "Working directory: $ScriptDir"
Write-Host ""

# Prefer a project venv if one's been set up (matches the Mac script's
# Default/.venv convention); otherwise fall back to the "py" launcher,
# which - unlike a bare "python" on PATH - reliably resolves a real
# installed interpreter instead of the Microsoft Store alias stub.
#
# No --reload here (unlike the Mac dev script): with --reload, uvicorn
# forks a separate watcher + worker process pair, so the PID Start-Process
# hands back is just the watcher - Stop-Process on it leaves the actual
# worker (and the port) running behind. This is a double-click launcher for
# using the app, not a dev server, so there's nothing to reload anyway.
$VenvUvicorn = "Default\.venv\Scripts\uvicorn.exe"
$BackendExe = $null
$BackendArgs = @()
if (Test-Path $VenvUvicorn) {
    $BackendExe = (Resolve-Path $VenvUvicorn).Path
    $BackendArgs = @("api.main:app", "--port", "$BackendPort", "--app-dir", "Default")
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    # Resolve py's target interpreter and invoke it directly (not "py.exe"
    # itself) - py.exe spawns the real python.exe as a CHILD process rather
    # than replacing itself, so Stop-Process on py.exe later would leave
    # that child running. Same reasoning as the vite.js-over-vite.cmd choice
    # below.
    $resolvedPython = & py -3 -c "import sys; print(sys.executable)" 2>$null
    if ($resolvedPython -and (Test-Path $resolvedPython)) {
        $BackendExe = $resolvedPython
        $BackendArgs = @("-m", "uvicorn", "api.main:app", "--port", "$BackendPort", "--app-dir", "Default")
    }
}

if (-not $BackendExe) {
    Write-Host "Error: no usable Python found (checked Default\.venv and the 'py' launcher)."
    Write-Host "Set up the backend first, either:"
    Write-Host "  cd Default; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
    Write-Host "or install Python from python.org (which registers the 'py' launcher) and:"
    Write-Host "  py -3 -m pip install -r Default\requirements.txt"
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "frontend\node_modules not found - running npm install..."
    Push-Location frontend
    npm install
    Pop-Location
}
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found - running npm install..."
    npm install
}

$backendProcess = $null
$frontendProcess = $null

function Stop-Servers {
    Write-Host ""
    Write-Host "Shutting down..."
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Stopped. You can close this window."
}

try {
    Write-Host "Starting backend on port $BackendPort..."
    $backendProcess = Start-Process -FilePath $BackendExe -ArgumentList $BackendArgs `
        -WorkingDirectory $ScriptDir -PassThru -WindowStyle Hidden

    Write-Host "Starting frontend on port $FrontendPort..."
    # Invoke vite's JS entry directly via node.exe (not the vite.cmd shim) so
    # the process we get back IS the server, not a wrapper around it -
    # mirrors the Mac script's `exec vite` trick, so Stop-Process actually
    # reaches it instead of leaving an orphaned node.exe behind.
    $frontendProcess = Start-Process -FilePath "node" `
        -ArgumentList (Resolve-Path $ViteJs), "--port", "$FrontendPort" `
        -WorkingDirectory (Join-Path $ScriptDir "frontend") -PassThru -WindowStyle Hidden

    Write-Host "Waiting for frontend to come up..."
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            Invoke-WebRequest -Uri "http://localhost:$FrontendPort" -UseBasicParsing -TimeoutSec 1 | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        Write-Host "Warning: frontend did not respond within 60s - opening it anyway."
    }

    Start-Process "http://localhost:$FrontendPort"

    Write-Host ""
    Write-Host "Backend:  http://localhost:$BackendPort/docs"
    Write-Host "Frontend: http://localhost:$FrontendPort"
    Write-Host ""
    Write-Host "Close this window or press Ctrl+C to stop both servers."

    Wait-Process -Id $backendProcess.Id, $frontendProcess.Id -ErrorAction SilentlyContinue
} finally {
    Stop-Servers
}
