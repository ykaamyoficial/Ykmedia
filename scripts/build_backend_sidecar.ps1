param(
    [string]$TargetTriple = "x86_64-pc-windows-msvc",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$entryPoint = Join-Path $projectRoot "app\backend_entry.py"
$binariesDirectory = Join-Path $projectRoot "src-tauri\binaries"
$stagingDirectory = Join-Path $projectRoot "build\backend-sidecar"
$distDirectory = Join-Path $projectRoot "dist\backend-sidecar"
$outputName = "ykmedia-backend"
$sidecarPath = Join-Path $binariesDirectory "$outputName-$TargetTriple.exe"

New-Item -ItemType Directory -Force -Path $binariesDirectory | Out-Null

Push-Location $projectRoot
try {
    # PyInstaller escreve seus logs em stderr. Rodamos com ErrorActionPreference
    # local em "Continue" para que essas linhas nao sejam promovidas a erro
    # terminal (o que quebrava o build quando este script era chamado por outro).
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --noconsole `
        --name $outputName `
        --paths $projectRoot `
        --add-data "docker;docker" `
        --collect-all uvicorn `
        --collect-all fastapi `
        --workpath $stagingDirectory `
        --distpath $distDirectory `
        $entryPoint
    $pyInstallerExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference

    if ($pyInstallerExitCode -ne 0) {
        throw "PyInstaller falhou (codigo $pyInstallerExitCode)."
    }

    $builtSidecarPath = Join-Path $distDirectory "$outputName.exe"
    $copyCompleted = $false
    for ($attempt = 1; $attempt -le 10; $attempt++) {
        try {
            Copy-Item -LiteralPath $builtSidecarPath -Destination $sidecarPath -Force
            $copyCompleted = $true
            break
        }
        catch [System.IO.IOException] {
            if ($attempt -eq 10) {
                throw
            }
            Start-Sleep -Seconds 1
        }
    }

    if (-not $copyCompleted) {
        throw "Nao foi possivel atualizar o backend sidecar."
    }
    Write-Host "Backend sidecar gerado em: $sidecarPath"
}
finally {
    Pop-Location
}
