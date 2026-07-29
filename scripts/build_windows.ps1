param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$iconPath = Join-Path $projectRoot "app\desktop\assets\ykmedia.ico"
$entryPoint = Join-Path $projectRoot "app\desktop\__main__.py"
$assetData = "app\desktop\assets;app\desktop\assets"
$dockerData = "docker;docker"

if (-not (Test-Path $iconPath)) {
    throw "Icone nao encontrado em: $iconPath"
}

Push-Location $projectRoot
try {
    $mode = if ($OneFile) { "--onefile" } else { "--onedir" }
    python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        $mode `
        --name YkMedia `
        --icon $iconPath `
        --add-data $assetData `
        --add-data $dockerData `
        $entryPoint
}
finally {
    Pop-Location
}
