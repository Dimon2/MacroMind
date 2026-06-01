# Cursor beforeShellExecution: prefer project .venv over global Python.
# Reads JSON from stdin; writes JSON to stdout. Exit 0 = success, 2 = deny.

$ErrorActionPreference = "Stop"
$raw = [Console]::In.ReadToEnd()
if (-not $raw) {
    Write-Output '{"permission":"allow"}'
    exit 0
}

try {
    $payload = $raw | ConvertFrom-Json
} catch {
    Write-Output '{"permission":"allow"}'
    exit 0
}

$command = [string]$payload.command
if ([string]::IsNullOrWhiteSpace($command)) {
    Write-Output '{"permission":"allow"}'
    exit 0
}

# Already using project venv
if ($command -match '(?i)\.venv[\\/]scripts[\\/]python') {
    Write-Output '{"permission":"allow"}'
    exit 0
}

# Creating or managing venv is fine
if ($command -match '(?i)python\s+-m\s+venv\b') {
    Write-Output '{"permission":"allow"}'
    exit 0
}

$venvPython = '.\.venv\Scripts\python.exe'
$needsVenv = $false
$reason = ''

if ($command -match '(?i)(^|[;&|]\s*)(pip3?)\s+install\b') {
    $needsVenv = $true
    $reason = 'pip install'
    $suggest = "$venvPython -m pip install ..."
}
elseif ($command -match '(?i)(^|[;&|]\s*)python\s+-m\s+pip\s+install\b') {
    $needsVenv = $true
    $reason = 'python -m pip install'
    $suggest = "$venvPython -m pip install ..."
}
elseif ($command -match '(?i)(^|[;&|]\s*)py\s+-m\s+pip\s+install\b') {
    $needsVenv = $true
    $reason = 'py -m pip install'
    $suggest = "$venvPython -m pip install ..."
}
elseif ($command -match '(?i)main\.py|ai_market_terminal|pytest\b') {
    if ($command -match '(?i)(^|[;&|]\s*)python\b') {
        $needsVenv = $true
        $reason = 'python project CLI'
        $suggest = "$venvPython main.py ...  (set PYTHONPATH=src for this repo)"
    }
}

if (-not $needsVenv) {
    Write-Output '{"permission":"allow"}'
    exit 0
}

$userMsg = "Use the project virtualenv instead of global Python ($reason). Example: $suggest"
$agentMsg = "Hook blocked global Python/pip. Use .\.venv\Scripts\python.exe and PYTHONPATH=src per .cursor/rules/python-venv.mdc."

$response = @{
    permission    = 'ask'
    user_message  = $userMsg
    agent_message = $agentMsg
} | ConvertTo-Json -Compress

Write-Output $response
exit 0
