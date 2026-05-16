param(
    [switch]$Quiet
)

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")

$candidatePaths = @(
    (Join-Path $Root ".tools\node"),
    (Join-Path $Root ".tools\docker"),
    "C:\Program Files\Git\cmd",
    "C:\Program Files\Docker\Docker\resources\bin",
    "C:\ProgramData\DockerDesktop\version-bin",
    [Environment]::GetEnvironmentVariable("Path", "Machine"),
    [Environment]::GetEnvironmentVariable("Path", "User")
)

$seen = New-Object "System.Collections.Generic.HashSet[string]" ([StringComparer]::OrdinalIgnoreCase)
$cleanParts = New-Object "System.Collections.Generic.List[string]"

foreach ($entryGroup in $candidatePaths) {
    if ([string]::IsNullOrWhiteSpace($entryGroup)) {
        continue
    }

    foreach ($entry in ($entryGroup -split ";")) {
        $trimmed = $entry.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }
        if ($seen.Add($trimmed)) {
            $cleanParts.Add($trimmed)
        }
    }
}

$cleanPath = $cleanParts -join ";"
$dockerConfig = Join-Path $Root ".docker"
New-Item -ItemType Directory -Force $dockerConfig | Out-Null

# The Codex shell can contain both PATH and Path. Start-Process on Windows may fail
# when the process environment has duplicate case-insensitive keys, so remove the
# uppercase variant first and then set a single canonical Path entry.
[Environment]::SetEnvironmentVariable("PATH", $null, "Process")
[Environment]::SetEnvironmentVariable("Path", $cleanPath, "Process")
$env:Path = $cleanPath
$env:DOCKER_CONFIG = $dockerConfig

if (-not $Quiet) {
    Write-Host "Process Path repaired. Entries:" $cleanParts.Count
    Write-Host "DOCKER_CONFIG:" $env:DOCKER_CONFIG
}
