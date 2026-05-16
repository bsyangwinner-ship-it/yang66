param(
    [switch]$SkipWslSetup
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\repair-path.ps1" -Quiet

function Add-UserPathEntry {
    param([string]$PathEntry)

    if (-not (Test-Path $PathEntry)) {
        return
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $entries = @()
    if (-not [string]::IsNullOrWhiteSpace($userPath)) {
        $entries = $userPath -split ";" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    }

    if ($entries -notcontains $PathEntry) {
        $newUserPath = (@($entries) + $PathEntry) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    }

    if (($env:Path -split ";") -notcontains $PathEntry) {
        $env:Path = "$PathEntry;$env:Path"
    }
}

function Find-DockerCliPath {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin",
        "$env:LOCALAPPDATA\Programs\Docker\Docker\resources\bin",
        "C:\Program Files\Docker\Docker\resources\bin",
        "C:\ProgramData\DockerDesktop\version-bin"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate "docker.exe")) {
            return $candidate
        }
    }

    return $null
}

function Find-DockerDesktopExe {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe",
        "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

$existingDocker = Get-Command docker -ErrorAction SilentlyContinue
if ($existingDocker) {
    Write-Host "Docker CLI already available:" $existingDocker.Source
    docker --version
    docker compose version
    exit 0
}

if (-not $SkipWslSetup) {
    $wslStatus = cmd /c "wsl --status 2>&1"
    $wslExitCode = $LASTEXITCODE
    if ($wslExitCode -ne 0) {
        Write-Host "WSL is not ready. Attempting WSL setup without a Linux distribution..."
        cmd /c "wsl --install --no-distribution"
        $wslInstallExitCode = $LASTEXITCODE
        if ($wslInstallExitCode -ne 0) {
            Write-Host "wsl --install did not complete. Enabling required Windows features..."
            cmd /c "dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart"
            cmd /c "dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart"
            Write-Host "WSL feature setup requested. A Windows restart may be required before Docker can run."
        }
    } else {
        Write-Host "WSL status:"
        Write-Host $wslStatus
    }
}

$installer = Join-Path $env:TEMP "DockerDesktopInstaller.exe"
$downloadUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

Write-Host "Downloading Docker Desktop installer..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $installer

Write-Host "Installing Docker Desktop in per-user mode..."
Start-Process `
    -FilePath $installer `
    -Wait `
    -ArgumentList "install", "--user", "--quiet", "--accept-license"

$dockerCliPath = Find-DockerCliPath
if ($dockerCliPath) {
    Add-UserPathEntry $dockerCliPath
}

$dockerDesktopExe = Find-DockerDesktopExe
if ($dockerDesktopExe) {
    Write-Host "Starting Docker Desktop..."
    Start-Process -FilePath $dockerDesktopExe -WindowStyle Hidden
}

Write-Host "Waiting for Docker engine..."
for ($i = 0; $i -lt 60; $i++) {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker) {
        docker version *> $null
        if ($LASTEXITCODE -eq 0) {
            docker --version
            docker compose version
            Write-Host "Docker Desktop is ready."
            exit 0
        }
    }
    Start-Sleep -Seconds 5
}

Write-Host "Docker Desktop installed, but the engine is not ready yet."
Write-Host "If Windows features were enabled, restart Windows, then open Docker Desktop once."
exit 1
