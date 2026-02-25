param(
    [string]$RootPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

function Read-EnvFile {
    param([string]$Path)
    $result = @{}
    if (-not (Test-Path $Path)) { return $result }

    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        $result[$parts[0].Trim()] = $parts[1]
    }
    return $result
}

function Write-EnvFile {
    param(
        [string]$Path,
        [hashtable]$Entries
    )
    $lines = @()
    foreach ($key in ($Entries.Keys | Sort-Object)) {
        $value = $Entries[$key]
        if ([string]::IsNullOrWhiteSpace([string]$value)) {
            continue
        }
        $lines += "$key=$value"
    }
    Set-Content -Path $Path -Value $lines -Encoding UTF8
}

function Merge-Hashtable {
    param(
        [hashtable]$Base,
        [hashtable]$Override
    )
    foreach ($key in $Override.Keys) {
        $Base[$key] = $Override[$key]
    }
    return $Base
}

function Get-EndpointEnvName {
    param(
        [string]$EndpointName,
        [string]$TokenField
    )
    if ($TokenField -and $TokenField.StartsWith("ENV:")) {
        return $TokenField.Substring(4)
    }
    $sanitized = (($EndpointName.ToUpper() -replace "[^A-Z0-9]", "_") -replace "_+", "_").Trim("_")
    if (-not $sanitized) { $sanitized = "SORA_ENDPOINT" }
    return "${sanitized}_API_KEY"
}

$root = (Resolve-Path $RootPath).Path
$translatorsPath = Join-Path $root "translators.json"
$configUserPath = Join-Path $root "config.user.json"
$envPath = Join-Path $root ".env"

if (-not (Test-Path $translatorsPath)) {
    throw "translators.json not found in $root"
}

$translators = Get-Content -Path $translatorsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$endpoints = @($translators.endpoints)
if ($endpoints.Count -eq 0) {
    throw "No endpoints configured in translators.json"
}

Write-Host ""
Write-Host "SoraTranslator first-run setup" -ForegroundColor Cyan
Write-Host "--------------------------------"
Write-Host ""
Write-Host "Select endpoint:"
for ($i = 0; $i -lt $endpoints.Count; $i++) {
    Write-Host ("  [{0}] {1}" -f ($i + 1), $endpoints[$i].name)
}

$endpointIndex = $null
while ($null -eq $endpointIndex) {
    $raw = Read-Host "Enter number"
    if ($raw -as [int]) {
        $candidate = [int]$raw
        if ($candidate -ge 1 -and $candidate -le $endpoints.Count) {
            $endpointIndex = $candidate - 1
        }
    }
    if ($null -eq $endpointIndex) {
        Write-Host "Invalid selection. Try again." -ForegroundColor Yellow
    }
}

$selectedEndpoint = $endpoints[$endpointIndex]
$models = @($selectedEndpoint.models)
if ($models.Count -eq 0) {
    throw "Endpoint '$($selectedEndpoint.name)' has no models."
}

Write-Host ""
Write-Host ("Selected endpoint: {0}" -f $selectedEndpoint.name) -ForegroundColor Green
Write-Host "Select model:"
for ($i = 0; $i -lt $models.Count; $i++) {
    Write-Host ("  [{0}] {1}" -f ($i + 1), $models[$i])
}

$modelIndex = $null
while ($null -eq $modelIndex) {
    $raw = Read-Host "Enter number"
    if ($raw -as [int]) {
        $candidate = [int]$raw
        if ($candidate -ge 1 -and $candidate -le $models.Count) {
            $modelIndex = $candidate - 1
        }
    }
    if ($null -eq $modelIndex) {
        Write-Host "Invalid selection. Try again." -ForegroundColor Yellow
    }
}
$selectedModel = $models[$modelIndex]

$apiKey = ""
while ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = Read-Host "Enter API key for $($selectedEndpoint.name)"
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Host "API key cannot be empty." -ForegroundColor Yellow
    }
}

$proxy = Read-Host "Optional proxy URL (press Enter to skip)"

$envName = Get-EndpointEnvName -EndpointName $selectedEndpoint.name -TokenField ([string]$selectedEndpoint.token)
$envEntries = Read-EnvFile -Path $envPath
$envEntries[$envName] = $apiKey.Trim()
if ([string]::IsNullOrWhiteSpace($proxy)) {
    $envEntries.Remove("SORA_PROXY") | Out-Null
} else {
    $envEntries["SORA_PROXY"] = $proxy.Trim()
}
Write-EnvFile -Path $envPath -Entries $envEntries

$currentUserConfig = @{}
if (Test-Path $configUserPath) {
    $existingObj = Get-Content -Path $configUserPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($p in $existingObj.PSObject.Properties) {
        $currentUserConfig[$p.Name] = $p.Value
    }
}

$tokenRef = "ENV:$envName"
$updates = @{
    endpoint_name = $selectedEndpoint.name
    model_name    = $selectedModel
    endpoint      = $selectedEndpoint.endpoint
    token         = $tokenRef
    proxy         = if ([string]::IsNullOrWhiteSpace($proxy)) { $null } else { $proxy.Trim() }
}
if ($selectedEndpoint.name -eq "OpenAI") {
    $updates["openai_api_key"] = "ENV:OPENAI_API_KEY"
}

$merged = Merge-Hashtable -Base $currentUserConfig -Override $updates
$merged | ConvertTo-Json -Depth 10 | Set-Content -Path $configUserPath -Encoding UTF8

Write-Host ""
Write-Host "Saved:" -ForegroundColor Green
Write-Host ("  - {0}" -f $envPath)
Write-Host ("  - {0}" -f $configUserPath)
Write-Host ("Endpoint: {0}" -f $selectedEndpoint.name)
Write-Host ("Model: {0}" -f $selectedModel)
Write-Host ""
Write-Host "Run run.bat to start SoraTranslator."
