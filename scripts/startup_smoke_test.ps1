param(
    [string]$RunDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$FullInstall
)

$ErrorActionPreference = "Stop"

$launcher = Join-Path $RunDir "run.bat"
if (-not (Test-Path $launcher)) {
    throw "Launcher not found: $launcher"
}

Write-Host "[startup-smoke] Running first startup smoke..." -ForegroundColor Cyan
$firstArgs = if ($FullInstall) { "--smoke --max-runtime-seconds 900" } else { "--smoke --skip-install --max-runtime-seconds 180" }
$firstOutput = & cmd /c """$launcher"" $firstArgs" 2>&1
$firstCode = $LASTEXITCODE
if ($firstCode -ne 0) {
    Write-Host ($firstOutput | Out-String)
    throw "First smoke run failed with exit code $firstCode"
}

Write-Host "[startup-smoke] Running second startup smoke..." -ForegroundColor Cyan
$secondOutput = & cmd /c """$launcher"" $firstArgs" 2>&1
$secondCode = $LASTEXITCODE
if ($secondCode -ne 0) {
    Write-Host ($secondOutput | Out-String)
    throw "Second smoke run failed with exit code $secondCode"
}

$secondText = ($secondOutput | Out-String)
if ($FullInstall) {
    if ($secondText -notmatch "Dependencies are up to date\. Skipping pip install\.") {
        Write-Host $secondText
        throw "Second smoke run did not detect dependency cache skip."
    }
}

if ($FullInstall) {
    Write-Host "[startup-smoke] PASS: first run + cached second run completed." -ForegroundColor Green
} else {
    Write-Host "[startup-smoke] PASS: quick smoke completed without dependency install." -ForegroundColor Green
}
