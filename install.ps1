# codex-sangpye-skill — one-shot installer (Windows PowerShell)
#
# Usage:
#   iwr -useb https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/install.ps1 | iex
#
# What it does:
#   1. Verifies prerequisites (uv, and ChatGPT OAuth tokens in ~/.codex/auth.json)
#   2. Installs the `sangpye` CLI globally via `uv tool install`
#   3. Drops SKILL.md into %USERPROFILE%\.claude\skills\codex-sangpye\ for Claude Code skill discovery
#   4. Runs a smoke check
#
# Safe to re-run — idempotent.

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/NewTurn2017/codex-sangpye-skill"
$SkillDirClaude = Join-Path $HOME ".claude\skills\codex-sangpye"

function Ok([string]$msg)    { Write-Host "  " -NoNewline; Write-Host "OK " -NoNewline -ForegroundColor Green; Write-Host $msg }
function Warn([string]$msg)  { Write-Host "  " -NoNewline; Write-Host "!  " -NoNewline -ForegroundColor Yellow; Write-Host $msg }
function Fail([string]$msg)  { Write-Host "  " -NoNewline; Write-Host "x  " -NoNewline -ForegroundColor Red; Write-Host $msg; exit 1 }
function Step([string]$msg)  { Write-Host ""; Write-Host "==> " -NoNewline -ForegroundColor Cyan; Write-Host $msg }

Step "1/4  Prerequisite check"

# uv
try { $uvVer = (uv --version 2>$null) -split '\s+' | Select-Object -Index 1 } catch { $uvVer = $null }
if (-not $uvVer) {
    Fail "uv not found. Install: winget install --id=astral-sh.uv  (or see https://github.com/astral-sh/uv)"
}
Ok "uv $uvVer"

# ChatGPT OAuth tokens (sangpye reads them directly — no codex binary needed at runtime)
$AuthFile = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "auth.json" } else { Join-Path $HOME ".codex\auth.json" }
if (-not (Test-Path $AuthFile)) {
    Fail "$AuthFile not found. Run: codex login  (pick the ChatGPT/OAuth option)"
}
try {
    $authObj = Get-Content -Raw -Path $AuthFile | ConvertFrom-Json
    if (-not $authObj.tokens.access_token -or -not $authObj.tokens.account_id) {
        Fail "$AuthFile has no ChatGPT OAuth tokens (auth_mode=$($authObj.auth_mode)). Run: codex logout; codex login (choose ChatGPT)"
    }
} catch {
    Fail "Could not parse $AuthFile : $_"
}
Ok "ChatGPT OAuth tokens present in $AuthFile"

Step "2/4  Install sangpye CLI (uv tool install)"
# Try --reinstall first (to upgrade an existing install), fall back to plain install
& uv tool install --reinstall "git+$RepoUrl" 2>$null
if ($LASTEXITCODE -ne 0) {
    & uv tool install "git+$RepoUrl"
    if ($LASTEXITCODE -ne 0) { Fail "uv tool install failed" }
}
$sangpyeVer = (sangpye --version) -split '\s+' | Select-Object -Index 1
Ok "sangpye $sangpyeVer"

Step "3/4  Drop SKILL.md for Claude Code skill discovery"
New-Item -ItemType Directory -Force -Path $SkillDirClaude | Out-Null
Invoke-WebRequest -UseBasicParsing `
    -Uri "https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/SKILL.md" `
    -OutFile (Join-Path $SkillDirClaude "SKILL.md")
Ok "Claude Code: $(Join-Path $SkillDirClaude 'SKILL.md')"

Step "4/4  Smoke check"
$help = sangpye --help 2>&1
if ($help -match "sangpye") { Ok "sangpye CLI responds to --help" }

Write-Host ""
Write-Host "codex-sangpye-skill is ready." -ForegroundColor Green
Write-Host ""
Write-Host "Try it (one image + a Korean brief):"
Write-Host "  sangpye --image C:\path\to\product.jpg --prompt '무선 이어폰, ANC, 30시간 배터리' --output .\out"
Write-Host ""
Write-Host "From inside Claude Code, just ask in Korean:"
Write-Host "  `"이 상품으로 상세페이지 만들어줘: C:\path\to\product.jpg`""
Write-Host "The agent will dispatch the codex-sangpye skill automatically."
