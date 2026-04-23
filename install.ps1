# codex-sangpye-skill — one-shot installer (Windows PowerShell)
#
# Usage:
#   iwr -useb https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/install.ps1 | iex
#
# What it does:
#   1. Verifies prerequisites (uv, codex >= 0.121.0, codex OAuth login)
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

# codex >= 0.121.0
try { $codexVer = (codex --version 2>$null) -split '\s+' | Select-Object -Index 1 } catch { $codexVer = $null }
if (-not $codexVer) {
    Fail "codex CLI not found. Install: npm install -g @openai/codex  (or https://github.com/openai/codex)"
}
# Parse x.y.z; require (0.y where y>=121) OR >= 1.0
if ($codexVer -match '^0\.(\d+)\.') {
    $minor = [int]$Matches[1]
    if ($minor -lt 121) {
        Fail "codex $codexVer is too old. Upgrade: npm install -g @openai/codex@latest  (need >= 0.121.0)"
    }
}
Ok "codex $codexVer"

# codex login status
try {
    $loginOut = codex login status 2>&1
    if ($LASTEXITCODE -ne 0) { throw "not logged in" }
} catch {
    Fail "codex is not logged in. Run: codex login  (pick ChatGPT/OAuth option)"
}
$loginFirstLine = ($loginOut | Select-Object -First 1).ToString().Trim()
Ok "codex login: $loginFirstLine"

# CODEX_API_KEY check
if ($env:CODEX_API_KEY) {
    Warn "CODEX_API_KEY is set — this will override OAuth and may bill against an API key."
    Warn "Unset it with: Remove-Item Env:CODEX_API_KEY"
}

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
