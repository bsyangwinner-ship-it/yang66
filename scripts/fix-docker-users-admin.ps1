$ErrorActionPreference = "Continue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogPath = Join-Path $Root ".logs\fix-docker-users-admin.log"
New-Item -ItemType Directory -Force (Split-Path $LogPath) | Out-Null

Start-Transcript -Path $LogPath -Force

$users = @(
    "YANG66\胡杨",
    "YANG66\codexsandboxoffline",
    "胡杨",
    "codexsandboxoffline"
)

foreach ($user in $users) {
    Write-Host "Adding $user to docker-users..."
    net localgroup docker-users "$user" /add
}

Write-Host "Current docker-users members:"
net localgroup docker-users

Write-Host "Restarting Docker Desktop processes..."
Get-Process |
    Where-Object { $_.ProcessName -match "Docker|com\.docker|docker-sandbox" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 3

Write-Host "Starting Docker Desktop service..."
Start-Service com.docker.service

Write-Host "Starting Docker Desktop..."
Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe"

Write-Host "Done. Log off/on or restart Windows if the current shell still cannot access Docker."

Stop-Transcript
Read-Host "Press Enter to close"
