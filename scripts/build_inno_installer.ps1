param(
    [switch]$SkipSidecar,
    [switch]$SkipTauri
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$innoScript = Join-Path $projectRoot "installer\YkMedia.iss"
$outputDir = Join-Path $projectRoot "installer\output"

$isccCandidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 7\ISCC.exe",
    "C:\Program Files\Inno Setup 7\ISCC.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 7\ISCC.exe")
)
$isccPath = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $isccPath) {
    throw "Inno Setup 6/7 nao foi encontrado. Instale-o antes de gerar o instalador."
}

Push-Location $projectRoot
try {
    # 1. Backend sidecar. Chamado com "&" na mesma sessao (nao via "powershell
    #    -File"), senao o stderr do PyInstaller vira erro terminal.
    if (-not $SkipSidecar) {
        & (Join-Path $PSScriptRoot "build_backend_sidecar.ps1")
    }

    # 2. Aplicativo Tauri (frontend + shell Rust em release).
    if (-not $SkipTauri) {
        $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
        if (Test-Path $cargoBin) {
            $env:Path = "$cargoBin;" + $env:Path
        }

        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & npm.cmd run tauri:build --prefix frontend
        $tauriExitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference

        if ($tauriExitCode -ne 0) {
            throw "Falha ao gerar o aplicativo Tauri (codigo $tauriExitCode)."
        }
    }

    # 3. Instalador Inno Setup.
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $isccPath $innoScript
    $isccExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference

    if ($isccExitCode -ne 0) {
        throw "Falha ao gerar o instalador Inno Setup (codigo $isccExitCode)."
    }

    $installer = Get-ChildItem $outputDir -Filter *.exe |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    Write-Host ""
    Write-Host "Instalador gerado: $($installer.FullName)"
}
finally {
    Pop-Location
}
