<#
Start entire VoiceAI stack (Docker services + FastAPI API + optional Agent)

Usage (PowerShell):
  powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -WithAgent

Parameters:
  -NoDocker        Skip starting Docker services (Redis)
  -WithAgent       Also start the dialog agent (agent/run_agent.py)
  -Host            Host to bind FastAPI (default 127.0.0.1)
  -Port            Port to bind FastAPI (default 8000)
  -RAGProvider     Override RAG provider for this run: local|openai|gemini
  -OpenAIKey       OPENAI_API_KEY for this run (optional)
  -GeminiKey       GEMINI_API_KEY for this run (optional)

Notes:
  - Requires Docker if you want Redis queue (via docker-compose.yml)
  - .env in repo root is used by the app (Supabase URL/Key, etc.)
  - This script opens separate PowerShell windows for the API and Agent
#>

param(
  [switch]$NoDocker,
  [switch]$WithAgent,
  [string]$ApiHost = "127.0.0.1",
  [int]$ApiPort = 8000,
  [ValidateSet("local","openai","gemini")]
  [string]$RAGProvider,
  [string]$OpenAIKey,
  [string]$GeminiKey
)

function Write-Header($text) {
  Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Test-Command($name) {
  $null = (Get-Command $name -ErrorAction SilentlyContinue)
  return $?
}

function Get-DockerComposeCmd() {
  if (Test-Command "docker") {
    # Prefer 'docker compose'
    try {
      # Check if docker compose subcommand exists
      (& docker compose version) 2>$null | Out-Null
      if ($LASTEXITCODE -eq 0) { return "docker compose" }
    } catch { }
  }
  if (Test-Command "docker-compose") { return "docker-compose" }
  return $null
}

Write-Host "🚀 VOICEAI — START ALL" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# 1) Ensure venv and install dependencies
Write-Header "Environment setup"
if (-Not (Test-Path ".venv")) {
  Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Yellow
  python -m venv .venv
}

Write-Host "Activating .venv..." -ForegroundColor Yellow
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip | Out-Null

Write-Host "Installing requirements..." -ForegroundColor Yellow
python -m pip install -r requirements.txt | Out-Null

# 2) Start Docker services (Redis) unless skipped
if (-Not $NoDocker) {
  Write-Header "Docker services"
  $dc = Get-DockerComposeCmd
  if ($null -eq $dc) {
    Write-Host "⚠️  Docker or Docker Compose not found. Skipping Docker services." -ForegroundColor Yellow
  } else {
    Write-Host "Starting Docker services via: $dc up -d" -ForegroundColor Yellow
    & $dc up -d
  }
}

# 3) Build extra env vars for spawned processes
$extraEnv = @{}
if ($RAGProvider) { $extraEnv["RAG_PROVIDER"] = $RAGProvider }
if ($OpenAIKey) { $extraEnv["OPENAI_API_KEY"] = $OpenAIKey }
if ($GeminiKey) { $extraEnv["GEMINI_API_KEY"] = $GeminiKey }

function Start-Window($title, $command, $envMap) {
  $envPrefix = ""
  if ($envMap.Count -gt 0) {
    $assignments = $envMap.GetEnumerator() | ForEach-Object { "`$env:${($_.Key)}='${($_.Value)}';" }
    $envPrefix = ($assignments -join " ") + " "
  }
  $full = "$envPrefix$command"
  Start-Process powershell -ArgumentList @("-NoExit","-Command", $full) -WindowStyle Normal
}

# 4) Start FastAPI server in a new window
Write-Header "Starting FastAPI API"
$apiCmd = "python -X utf8 -m uvicorn app.main:app --reload --host $ApiHost --port $ApiPort"
Start-Window -title "VoiceAI API" -command $apiCmd -envMap $extraEnv

# 5) Optionally start the Agent
if ($WithAgent) {
  Write-Header "Starting Agent"
  $agentCmd = "python agent/run_agent.py"
  Start-Window -title "VoiceAI Agent" -command $agentCmd -envMap $extraEnv
}

# 6) Final info
Write-Header "All set"
Write-Host ("API docs: http://{0}:{1}/docs" -f $ApiHost, $ApiPort) -ForegroundColor Green
Write-Host ("RL monitor status: http://{0}:{1}/api/rl-monitor/status" -f $ApiHost, $ApiPort) -ForegroundColor Green
Write-Host ("RAG search: http://{0}:{1}/api/rag/search?q=bao%20hiem" -f $ApiHost, $ApiPort) -ForegroundColor Green
Write-Host "" 
Write-Host "To stop: close the API/Agent windows and run 'docker compose down' if used." -ForegroundColor Yellow
