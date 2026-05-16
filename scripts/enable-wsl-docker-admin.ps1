$ErrorActionPreference = "Continue"

$LogPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")) ".logs\enable-wsl-docker-admin.log"
New-Item -ItemType Directory -Force (Split-Path $LogPath) | Out-Null

Start-Transcript -Path $LogPath -Force

Write-Host "Enabling Windows Subsystem for Linux..."
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

Write-Host "Enabling Virtual Machine Platform..."
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

Write-Host "Installing WSL core without a Linux distribution..."
wsl --install --no-distribution

Write-Host "Trying to start Docker Desktop service..."
Start-Service com.docker.service

Write-Host "Starting Docker Desktop..."
Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe"

Write-Host "Done. If DISM reports restart required, restart Windows before running docker info."

Stop-Transcript
Read-Host "Press Enter to close"
