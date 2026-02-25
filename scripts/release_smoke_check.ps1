param(
    [string]$ReleaseDir = "build\portable"
)

$ErrorActionPreference = "Stop"

function Assert-Exists {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path -Path $Path)) {
        Write-Host "[smoke] MISSING: $Label -> $Path" -ForegroundColor Red
        $script:Failed = $true
    } else {
        Write-Host "[smoke] OK: $Label" -ForegroundColor Green
    }
}

$script:Failed = $false
$resolvedRelease = Resolve-Path -Path $ReleaseDir -ErrorAction SilentlyContinue
if (-not $resolvedRelease) {
    Write-Host "[smoke] Release directory does not exist: $ReleaseDir" -ForegroundColor Red
    exit 1
}

$root = $resolvedRelease.Path
Assert-Exists -Path (Join-Path $root "app") -Label "app directory"
Assert-Exists -Path (Join-Path $root "backend") -Label "backend directory"
Assert-Exists -Path (Join-Path $root "run.bat") -Label "launcher"
Assert-Exists -Path (Join-Path $root "config.template.json") -Label "config template"
Assert-Exists -Path (Join-Path $root "backend\requirements.txt") -Label "backend requirements"
Assert-Exists -Path (Join-Path $root "backend\Integrators\utils\xp3_upk.exe") -Label "helper executable (xp3_upk)"

$frontendExe = Get-ChildItem -Path (Join-Path $root "app") -File -Filter "*.exe" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notin @("elevate.exe", "crashpad_handler.exe") } |
    Select-Object -First 1
if (-not $frontendExe) {
    Write-Host "[smoke] MISSING: frontend executable in app/" -ForegroundColor Red
    $script:Failed = $true
} else {
    Write-Host "[smoke] OK: frontend executable ($($frontendExe.Name))" -ForegroundColor Green
}

if ($script:Failed) {
    Write-Host "[smoke] Release smoke check failed." -ForegroundColor Red
    exit 1
}

Write-Host "[smoke] Release smoke check passed." -ForegroundColor Green
exit 0
