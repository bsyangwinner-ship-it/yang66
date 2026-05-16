. "$PSScriptRoot\repair-path.ps1" -Quiet

$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "docker:" $docker.Source
    docker --version
    docker compose version
} else {
    Write-Host "docker: NOT FOUND"
}

$pathLines = cmd /c set path
$pathKeyCount = ($pathLines | Select-String -Pattern "^(PATH|Path)=").Count
Write-Host "Path key count in child cmd:" $pathKeyCount

if ($pathKeyCount -eq 1) {
    Write-Host "Path/PATH duplicate check: OK"
} else {
    Write-Host "Path/PATH duplicate check: FAILED"
    exit 1
}
