$ErrorActionPreference = "Stop"

. "$PSScriptRoot\repair-path.ps1" -Quiet

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$ToolsDir = Join-Path $Root ".tools"
$DockerDir = Join-Path $ToolsDir "docker"
$CliPluginsDir = Join-Path $DockerDir "cli-plugins"
$TempDir = Join-Path $ToolsDir "downloads"

New-Item -ItemType Directory -Force $DockerDir, $CliPluginsDir, $TempDir | Out-Null

function Get-LatestDockerCliUrl {
    $indexUrl = "https://download.docker.com/win/static/stable/x86_64/"
    $content = (Invoke-WebRequest -UseBasicParsing -Uri $indexUrl).Content
    $versions = [regex]::Matches($content, 'docker-(\d+\.\d+\.\d+)\.zip') |
        ForEach-Object {
            [pscustomobject]@{
                Version = [version]$_.Groups[1].Value
                File = $_.Groups[0].Value
            }
        } |
        Sort-Object Version -Descending

    if (-not $versions) {
        throw "Could not find Docker CLI versions from $indexUrl"
    }

    return "$indexUrl$($versions[0].File)"
}

function Get-LatestComposeUrl {
    $apiUrl = "https://api.github.com/repos/docker/compose/releases/latest"
    $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "codex-local-installer" }
    $asset = $release.assets |
        Where-Object { $_.name -eq "docker-compose-windows-x86_64.exe" } |
        Select-Object -First 1

    if (-not $asset) {
        throw "Could not find docker-compose-windows-x86_64.exe in latest Compose release"
    }

    return $asset.browser_download_url
}

$dockerCliUrl = Get-LatestDockerCliUrl
$dockerZip = Join-Path $TempDir "docker-cli.zip"
Write-Host "Downloading Docker CLI:" $dockerCliUrl
Invoke-WebRequest -UseBasicParsing -Uri $dockerCliUrl -OutFile $dockerZip

$extractDir = Join-Path $TempDir "docker-cli"
if (Test-Path $extractDir) {
    Remove-Item -Recurse -Force $extractDir
}
Expand-Archive -Path $dockerZip -DestinationPath $extractDir -Force

$dockerSourceDir = Join-Path $extractDir "docker"
Copy-Item -Path (Join-Path $dockerSourceDir "docker.exe") -Destination $DockerDir -Force

$composeUrl = Get-LatestComposeUrl
$composeDestination = Join-Path $CliPluginsDir "docker-compose.exe"
Write-Host "Downloading Docker Compose plugin:" $composeUrl
Invoke-WebRequest -UseBasicParsing -Uri $composeUrl -OutFile $composeDestination

$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($currentUserPath -split ";") -notcontains $DockerDir) {
    $newUserPath = if ([string]::IsNullOrWhiteSpace($currentUserPath)) {
        $DockerDir
    } else {
        "$currentUserPath;$DockerDir"
    }
    [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
}

$env:Path = "$DockerDir;$env:Path"
docker --version
docker compose version
docker compose -f (Join-Path $Root "docker-compose.yml") config | Out-Null
Write-Host "Docker CLI and Compose plugin are ready for docker compose config."
