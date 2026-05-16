param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

. "$PSScriptRoot\repair-path.ps1" -Quiet

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogDir = Join-Path $Root ".logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

if (-not $FrontendOnly) {
    Start-Process `
        -FilePath (Join-Path $Root "scripts\dev-backend.cmd") `
        -WorkingDirectory $Root `
        -WindowStyle Hidden
}

if (-not $BackendOnly) {
    Start-Process `
        -FilePath (Join-Path $Root "scripts\dev-frontend.cmd") `
        -WorkingDirectory $Root `
        -WindowStyle Hidden
}

Start-Sleep -Seconds 3

Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Docs:     http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:3000"
