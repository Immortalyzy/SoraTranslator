param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$script:logPath = Join-Path $root "log.txt"
$script:legacyLogPath = Join-Path $root "launcher.log.txt"
$script:stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

function Write-LauncherLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message

    foreach ($logFile in @($script:logPath, $script:legacyLogPath) | Select-Object -Unique) {
        Add-Content -Path $logFile -Value $line -Encoding UTF8
    }

    Write-Host $line
}

function Parse-IntegerValue {
    param(
        [string]$RawValue,
        [string]$FlagName
    )

    $parsed = 0
    if (-not [int]::TryParse($RawValue, [ref]$parsed)) {
        throw "$FlagName requires an integer value. Received '$RawValue'."
    }

    return $parsed
}

function Get-RemainingSeconds {
    param([int]$BudgetSeconds)

    $remaining = $BudgetSeconds - [int]$script:stopwatch.Elapsed.TotalSeconds
    if ($remaining -lt 0) { return 0 }
    return $remaining
}

function Stop-ProcessTree {
    param([int]$ProcessId)

    if ($ProcessId -le 0) {
        return
    }

    try {
        & taskkill /PID $ProcessId /T /F 1>$null 2>$null
    } catch {
        # Cleanup is best-effort; callers also guard process state before invoking it.
    }
}

function Wait-ProcessWithTimeout {
    param(
        [System.Diagnostics.Process]$Process,
        [int]$TimeoutSeconds,
        [string]$Name
    )

    if ($TimeoutSeconds -le 0) {
        throw "$Name exceeded runtime budget before start."
    }

    if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-ProcessTree -ProcessId $Process.Id
        throw "$Name exceeded hard timeout (${TimeoutSeconds}s)."
    }

    return $Process.ExitCode
}

function Find-PythonLauncher {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & py -3 -c "import sys" 1>$null 2>$null
            if ($LASTEXITCODE -eq 0) {
                return @{ Exe = "py"; Args = @("-3") }
            }
        } catch {
            # A broken py launcher should not prevent falling back to python.exe.
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        try {
            & python -c "import sys" 1>$null 2>$null
            if ($LASTEXITCODE -eq 0) {
                return @{ Exe = "python"; Args = @() }
            }
        } catch {
            # Keep probing candidates before reporting that Python is unavailable.
        }
    }

    return $null
}

function Find-ReleaseFrontendExecutable {
    param([string]$RootPath)

    $appDir = Join-Path $RootPath "app"
    if (-not (Test-Path $appDir)) {
        return $null
    }

    if ($env:SORA_FRONTEND_EXE) {
        $explicitExe = Join-Path $appDir $env:SORA_FRONTEND_EXE
        if (Test-Path $explicitExe) {
            return $explicitExe
        }
    }

    $defaultExe = Join-Path $appDir "SoraTranslator.exe"
    if (Test-Path $defaultExe) {
        return $defaultExe
    }

    $candidates = Get-ChildItem -Path $appDir -File -Filter "*.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notin @("elevate.exe", "crashpad_handler.exe") }
    if (-not $candidates) {
        return $null
    }

    $preferred = $candidates | Where-Object { $_.Name -match "(?i)sora" } | Select-Object -First 1
    if ($preferred) {
        return $preferred.FullName
    }

    return ($candidates | Select-Object -First 1).FullName
}

function Read-Stamp {
    param([string]$Path)

    $result = @{}
    if (-not (Test-Path $Path)) { return $result }

    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        if (-not $line.Contains("=")) { continue }
        $parts = $line.Split("=", 2)
        $result[$parts[0]] = $parts[1]
    }

    return $result
}

function Get-Sha256Hex {
    param([string]$Path)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($Path)
        try {
            $hashBytes = $sha.ComputeHash($stream)
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha.Dispose()
    }

    return (($hashBytes | ForEach-Object { $_.ToString("x2") }) -join "")
}

function Test-PipInstallOutcome {
    param(
        [int]$ExitCode,
        [string]$StdOutPath,
        [string]$StdErrPath
    )

    if ($ExitCode -eq 0) {
        return $true
    }

    $stdoutText = ""
    $stderrText = ""
    if (Test-Path $StdOutPath) { $stdoutText = Get-Content -Path $StdOutPath -Raw -Encoding UTF8 }
    if (Test-Path $StdErrPath) { $stderrText = Get-Content -Path $StdErrPath -Raw -Encoding UTF8 }
    $combined = "$stdoutText`n$stderrText"

    $hasSuccessMarker = ($combined -match "(?im)^Successfully installed ") -or ($combined -match "(?im)^Requirement already satisfied:")
    $hasHardError = $combined -match "(?im)^ERROR:"

    if ($hasSuccessMarker -and -not $hasHardError) {
        return $true
    }

    return $false
}

function Get-RequirementEntryCount {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return 0
    }

    return @(
        Get-Content -Path $Path -Encoding UTF8 |
        Where-Object {
            $trimmed = $_.Trim()
            $trimmed -and -not $trimmed.StartsWith("#")
        }
    ).Count
}

function Get-PipInstallProgressSnapshot {
    param(
        [string]$StdOutPath,
        [int]$RequirementCount
    )

    $snapshot = @{
        Percent = 5
        Status  = "Preparing dependency install..."
    }

    if (-not (Test-Path $StdOutPath)) {
        return $snapshot
    }

    try {
        $content = Get-Content -Path $StdOutPath -Raw -Encoding UTF8
    } catch {
        return $snapshot
    }

    if ([string]::IsNullOrWhiteSpace($content)) {
        return $snapshot
    }

    $collectingCount = [regex]::Matches($content, "(?m)^Collecting ").Count
    $installingStarted = $content -match "(?m)^Installing collected packages:"
    $successfullyInstalled = $content -match "(?m)^Successfully installed "

    if ($successfullyInstalled) {
        $snapshot.Percent = 98
        $snapshot.Status = "Finalizing dependency install..."
        return $snapshot
    }

    if ($installingStarted) {
        $snapshot.Percent = 90
        $snapshot.Status = "Installing downloaded packages..."
        return $snapshot
    }

    if ($RequirementCount -gt 0 -and $collectingCount -gt 0) {
        $resolvedCount = [Math]::Min($collectingCount, $RequirementCount)
        $snapshot.Percent = [Math]::Min(85, (10 + [int](($resolvedCount / $RequirementCount) * 75)))
        $snapshot.Status = "Resolving dependencies ($resolvedCount/$RequirementCount)..."
        return $snapshot
    }

    if ($collectingCount -gt 0) {
        $snapshot.Percent = 25
        $snapshot.Status = "Resolving dependencies..."
    }

    return $snapshot
}

function Wait-ProcessWithProgress {
    param(
        [System.Diagnostics.Process]$Process,
        [int]$TimeoutSeconds,
        [string]$Name,
        [string]$Activity,
        [scriptblock]$ProgressSnapshotProvider,
        [int]$ProgressId = 1
    )

    if ($TimeoutSeconds -le 0) {
        throw "$Name exceeded runtime budget before start."
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    try {
        while (-not $Process.HasExited) {
            $remaining = [int][Math]::Ceiling(($deadline - (Get-Date)).TotalSeconds)
            if ($remaining -le 0) {
                Stop-ProcessTree -ProcessId $Process.Id
                throw "$Name exceeded hard timeout (${TimeoutSeconds}s)."
            }

            $snapshot = & $ProgressSnapshotProvider
            $status = "{0} ({1}s left)" -f $snapshot.Status, $remaining
            Write-Progress -Id $ProgressId -Activity $Activity -Status $status -PercentComplete $snapshot.Percent

            $waitMs = [Math]::Min(1000, $remaining * 1000)
            $null = $Process.WaitForExit($waitMs)
        }

        $Process.WaitForExit()
        Write-Progress -Id $ProgressId -Activity $Activity -Completed
        return [int]$Process.ExitCode
    } finally {
        if (-not $Process.HasExited) {
            Write-Progress -Id $ProgressId -Activity $Activity -Completed
        }
    }
}

function Reserve-TcpPort {
    param([int]$Port)

    $listener = $null
    try {
        if ($Port -gt 0) {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        } else {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
        }
        $listener.Start()
        return ($listener.LocalEndpoint).Port
    } finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

Set-Content -Path $script:logPath -Value "" -Encoding UTF8
if ($script:legacyLogPath -ne $script:logPath) {
    Set-Content -Path $script:legacyLogPath -Value "" -Encoding UTF8
}

$mode = "auto"
$smokeMode = $false
$skipInstall = $false
$projectNameArg = ""
$backendPortArg = $null
$startupTimeoutSeconds = 0
$startupTimeoutExplicit = $false
$maxRuntimeSeconds = 0
$maxRuntimeExplicit = $false

for ($i = 0; $i -lt $CliArgs.Count; $i++) {
    $arg = $CliArgs[$i]
    switch ($arg) {
        "--dev" { $mode = "dev"; continue }
        "--release" { $mode = "release"; continue }
        "--smoke" { $smokeMode = $true; continue }
        "--skip-install" { $skipInstall = $true; continue }
        "--max-runtime-seconds" {
            if ($i + 1 -ge $CliArgs.Count) {
                throw "--max-runtime-seconds requires a value"
            }
            $i++
            $maxRuntimeSeconds = Parse-IntegerValue -RawValue $CliArgs[$i] -FlagName "--max-runtime-seconds"
            $maxRuntimeExplicit = $true
            continue
        }
        "--startup-timeout-seconds" {
            if ($i + 1 -ge $CliArgs.Count) {
                throw "--startup-timeout-seconds requires a value"
            }
            $i++
            $startupTimeoutSeconds = Parse-IntegerValue -RawValue $CliArgs[$i] -FlagName "--startup-timeout-seconds"
            $startupTimeoutExplicit = $true
            continue
        }
        "--backend-port" {
            if ($i + 1 -ge $CliArgs.Count) {
                throw "--backend-port requires a value"
            }
            $i++
            $backendPortArg = Parse-IntegerValue -RawValue $CliArgs[$i] -FlagName "--backend-port"
            continue
        }
        "--" { continue }
        default {
            if (-not $projectNameArg) {
                $projectNameArg = $arg
            }
        }
    }
}

$backendProcess = $null
$frontendProcess = $null
$backendPort = $null
$exitCode = 0

try {
    $releaseExe = Find-ReleaseFrontendExecutable -RootPath $root
    if ($mode -eq "auto") {
        $mode = if ($releaseExe) { "release" } else { "dev" }
    }

    if ($smokeMode) {
        $skipInstall = $true
    }

    if (-not $startupTimeoutExplicit) {
        $startupTimeoutSeconds = if ($smokeMode) { 300 } elseif ($mode -eq "release") { 1200 } else { 900 }
    }

    if ($startupTimeoutSeconds -lt 30) {
        throw "startup timeout must be at least 30 seconds"
    }

    if (-not $maxRuntimeExplicit) {
        if ($smokeMode) {
            $maxRuntimeSeconds = 300
        } elseif ($mode -eq "release") {
            $maxRuntimeSeconds = 0
        } else {
            $maxRuntimeSeconds = 0
        }
    }

    if ($maxRuntimeSeconds -lt 0) {
        throw "max runtime must be zero or a positive integer"
    }
    if ($maxRuntimeSeconds -gt 0 -and $maxRuntimeSeconds -lt 30) {
        throw "max runtime must be at least 30 seconds"
    }
    if ($backendPortArg -ne $null -and ($backendPortArg -lt 0 -or $backendPortArg -gt 65535)) {
        throw "backend port must be between 0 and 65535"
    }

    $runtimeSummary = if ($maxRuntimeSeconds -eq 0) { "unlimited" } else { "${maxRuntimeSeconds}s" }
    $portSummary = if ($backendPortArg -ne $null) { "$backendPortArg" } elseif ($mode -eq "release") { "5000 (release default)" } else { "dynamic" }
    Write-LauncherLog "Mode=$mode Smoke=$smokeMode SkipInstall=$skipInstall StartupTimeout=${startupTimeoutSeconds}s RuntimeLimit=$runtimeSummary BackendPort=$portSummary"
    Write-LauncherLog "Primary log file: $($script:logPath)"

    $pythonLauncher = Find-PythonLauncher
    if (-not $pythonLauncher) {
        throw "Python 3 not found. Install Python 3.8+ and ensure py/python is in PATH."
    }

    Write-LauncherLog ("Using Python launcher: {0} {1}" -f $pythonLauncher.Exe, ($pythonLauncher.Args -join " "))

    $backendDir = Join-Path $root "backend"
    $venvDir = Join-Path $backendDir ".venv"
    $venvPy = Join-Path $venvDir "Scripts\python.exe"
    $reqFile = Join-Path $backendDir "requirements.txt"
    $stampFile = Join-Path $venvDir "install.stamp"
    $backendOut = Join-Path $backendDir "backend.log"
    $backendErr = Join-Path $backendDir "backend.err.log"

    if (-not (Test-Path $reqFile)) {
        throw "Missing backend requirements file: $reqFile"
    }

    if (-not (Test-Path $venvPy)) {
        Write-LauncherLog "Creating backend virtual environment..."
        $createProc = Start-Process -FilePath $pythonLauncher.Exe -ArgumentList ($pythonLauncher.Args + @("-m", "venv", $venvDir)) -WorkingDirectory $root -PassThru -WindowStyle Hidden
        $remaining = Get-RemainingSeconds -BudgetSeconds $startupTimeoutSeconds
        $createCode = Wait-ProcessWithTimeout -Process $createProc -TimeoutSeconds $remaining -Name "venv creation"
        if ($createCode -ne 0) {
            throw "Failed to create backend virtual environment."
        }
    }

    $reqHash = Get-Sha256Hex -Path $reqFile
    $pyVersion = (& $venvPy -c "import platform; print(platform.python_version())").Trim()
    Write-LauncherLog "Requirements hash=$reqHash"
    Write-LauncherLog "Python version=$pyVersion"

    $stamp = Read-Stamp -Path $stampFile
    $needInstall = -not ($stamp["REQ_HASH"] -eq $reqHash -and $stamp["PY_VERSION"] -eq $pyVersion)

    if ($needInstall) {
        if ($skipInstall) {
            Write-LauncherLog "Skipping dependency installation (--skip-install)."
            & $venvPy -c "import flask" *> $null
            if ($LASTEXITCODE -ne 0) {
                throw "Flask is missing in .venv while --skip-install is active. Re-run without --skip-install."
            }
        } else {
            Write-LauncherLog "Installing backend dependencies..."
            $pipOut = Join-Path $backendDir "pip.install.out.log"
            $pipErr = Join-Path $backendDir "pip.install.err.log"
            $requirementCount = Get-RequirementEntryCount -Path $reqFile
            $pipProc = Start-Process -FilePath $venvPy -ArgumentList @("-m", "pip", "install", "--disable-pip-version-check", "-r", $reqFile) -WorkingDirectory $backendDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $pipOut -RedirectStandardError $pipErr
            $remaining = Get-RemainingSeconds -BudgetSeconds $startupTimeoutSeconds
            $pipCode = Wait-ProcessWithProgress -Process $pipProc -TimeoutSeconds $remaining -Name "pip install" -Activity "Installing Python dependencies" -ProgressSnapshotProvider {
                Get-PipInstallProgressSnapshot -StdOutPath $pipOut -RequirementCount $requirementCount
            } -ProgressId 17
            if (-not (Test-PipInstallOutcome -ExitCode $pipCode -StdOutPath $pipOut -StdErrPath $pipErr)) {
                throw "Dependency installation failed. See $pipOut and $pipErr"
            }
            if ($pipCode -ne 0) {
                Write-LauncherLog "pip exited with code $pipCode but logs indicate install success; continuing." "WARN"
            }
            Set-Content -Path $stampFile -Value @("REQ_HASH=$reqHash", "PY_VERSION=$pyVersion") -Encoding UTF8
        }
    } else {
        Write-LauncherLog "Dependencies are up to date. Skipping pip install."
    }

    $desiredPort = if ($backendPortArg -ne $null) { $backendPortArg } elseif ($mode -eq "release") { 5000 } else { 0 }
    try {
        $backendPort = Reserve-TcpPort -Port $desiredPort
    } catch {
        if ($desiredPort -eq 5000) {
            throw "Backend port 5000 is unavailable. Close the process using port 5000 or run with --backend-port <port>."
        }
        throw
    }

    $apiBase = "http://127.0.0.1:$backendPort"
    $env:SORA_BACKEND_PORT = "$backendPort"
    $env:SORA_API_BASE = $apiBase
    if ($projectNameArg) {
        $env:PROJECT_NAME = $projectNameArg
    } else {
        Remove-Item Env:PROJECT_NAME -ErrorAction SilentlyContinue
    }

    Write-LauncherLog "Starting backend on $apiBase"
    $backendProcess = Start-Process -FilePath $venvPy -ArgumentList @("-m", "flask", "--app", "app", "run", "--host", "127.0.0.1", "--port", "$backendPort") -WorkingDirectory $backendDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr
    Write-LauncherLog "Backend PID=$($backendProcess.Id)"

    $ready = $false
    while (-not $ready) {
        if ($backendProcess.HasExited) {
            throw "Backend process exited unexpectedly. See $backendOut and $backendErr"
        }

        $remaining = Get-RemainingSeconds -BudgetSeconds $startupTimeoutSeconds
        if ($remaining -le 0) {
            throw "Startup timeout reached before backend became ready."
        }

        try {
            $health = Invoke-RestMethod -Uri "$apiBase/health" -TimeoutSec 2
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        } catch {
            # retry
        }

        Start-Sleep -Seconds 1
    }

    Write-LauncherLog "Backend is ready."

    if ($smokeMode) {
        Write-LauncherLog "Smoke mode successful."
        exit 0
    }

    if ($mode -eq "release") {
        $releaseExe = Find-ReleaseFrontendExecutable -RootPath $root
        if (-not $releaseExe -or -not (Test-Path $releaseExe)) {
            throw "Release frontend executable not found in app/. Expected SoraTranslator.exe or another app executable."
        }

        Write-LauncherLog "Launching release frontend: $([System.IO.Path]::GetFileName($releaseExe))"
        $frontendProcess = Start-Process -FilePath $releaseExe -WorkingDirectory (Split-Path $releaseExe -Parent) -PassThru
        if ($maxRuntimeSeconds -eq 0) {
            Write-LauncherLog "Release runtime is unlimited by default; waiting for frontend exit."
            $frontendProcess.WaitForExit()
            $exitCode = $frontendProcess.ExitCode
        } else {
            $remaining = Get-RemainingSeconds -BudgetSeconds $maxRuntimeSeconds
            $frontendCode = Wait-ProcessWithTimeout -Process $frontendProcess -TimeoutSeconds $remaining -Name "release frontend"
            $exitCode = $frontendCode
        }
    } else {
        $frontendDir = Join-Path $root "frontend"
        if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
            throw "frontend/package.json not found."
        }

        $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
        if (-not $npm) {
            $npm = Get-Command npm -ErrorAction SilentlyContinue
        }
        if (-not $npm) {
            throw "npm not found in PATH."
        }

        if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
            if ($skipInstall) {
                throw "frontend/node_modules missing while --skip-install is active."
            }

            Write-LauncherLog "Installing frontend dependencies..."
            $npmInstall = Start-Process -FilePath $npm.Source -ArgumentList @("install") -WorkingDirectory $frontendDir -PassThru -NoNewWindow
            $remaining = Get-RemainingSeconds -BudgetSeconds $startupTimeoutSeconds
            $npmInstallCode = Wait-ProcessWithTimeout -Process $npmInstall -TimeoutSeconds $remaining -Name "npm install"
            if ($npmInstallCode -ne 0) {
                throw "npm install failed."
            }
        }

        $devArgs = @("run", "electron:serve")
        if ($projectNameArg) {
            $devArgs += $projectNameArg
        }

        Write-LauncherLog "Launching dev frontend (electron:serve)..."
        $frontendProcess = Start-Process -FilePath $npm.Source -ArgumentList $devArgs -WorkingDirectory $frontendDir -PassThru -NoNewWindow
        if ($maxRuntimeSeconds -eq 0) {
            Write-LauncherLog "Dev runtime is unlimited by default; waiting for frontend exit."
            $frontendProcess.WaitForExit()
            $exitCode = $frontendProcess.ExitCode
        } else {
            $remaining = Get-RemainingSeconds -BudgetSeconds $maxRuntimeSeconds
            $frontendCode = Wait-ProcessWithTimeout -Process $frontendProcess -TimeoutSeconds $remaining -Name "dev frontend"
            $exitCode = $frontendCode
        }
    }

    Write-LauncherLog "Frontend exited with code $exitCode"
    exit $exitCode
} catch {
    Write-LauncherLog $_.Exception.Message "ERROR"
    exit 1
} finally {
    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Stop-ProcessTree -ProcessId $frontendProcess.Id
        Write-LauncherLog "Frontend process stopped."
    }

    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-ProcessTree -ProcessId $backendProcess.Id
        Write-LauncherLog "Backend process stopped."
    }

    if ($backendPort) {
        $netstat = netstat -ano | Select-String ":$backendPort"
        foreach ($line in $netstat) {
            $parts = ($line -split "\s+") | Where-Object { $_ }
            if ($parts.Count -gt 0) {
                $procId = $parts[-1]
                if ($procId -as [int]) {
                    Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
}
