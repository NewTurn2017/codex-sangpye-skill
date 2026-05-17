#!/usr/bin/env bash
# codex-sangpye-skill — one-shot installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/install.sh | bash
#
# What it does:
#   1. Verifies prerequisites (uv, and ChatGPT OAuth tokens in ~/.codex/auth.json)
#   2. Installs the `sangpye` CLI globally via `uv tool install`
#   3. Drops SKILL.md into ~/.claude/skills/codex-sangpye/ for Claude Code skill discovery
#   4. Runs a smoke check
#
# Safe to re-run — idempotent.

set -euo pipefail

REPO_URL="https://github.com/NewTurn2017/codex-sangpye-skill"
SKILL_DIR_CLAUDE="$HOME/.claude/skills/codex-sangpye"
SKILL_DIR_HERMES="$HOME/.hermes/skills/creative/codex-sangpye"

color() { printf "\033[%sm%s\033[0m" "$1" "$2"; }
ok() { echo "  $(color 32 "✓") $1"; }
warn() { echo "  $(color 33 "!") $1"; }
fail() { echo "  $(color 31 "✗") $1" >&2; exit 1; }
step() { echo; echo "$(color 36 "==>") $1"; }

step "1/4  Prerequisite check"

# uv
if ! command -v uv >/dev/null 2>&1; then
  fail "uv not found. Install: brew install uv  (or see https://github.com/astral-sh/uv)"
fi
ok "uv $(uv --version | awk '{print $2}')"

# ChatGPT OAuth tokens (sangpye reads them directly — no codex binary needed at runtime)
AUTH_FILE="${CODEX_HOME:-$HOME/.codex}/auth.json"
if [ ! -f "$AUTH_FILE" ]; then
  fail "$AUTH_FILE not found. Run: codex login  (pick the ChatGPT/OAuth option)"
fi
if ! python3 -c "
import json, sys
d = json.load(open('$AUTH_FILE'))
t = d.get('tokens') or {}
if not t.get('access_token') or not t.get('account_id'):
    sys.exit('auth.json has no ChatGPT OAuth tokens (auth_mode={!r}). Run: codex logout && codex login (choose ChatGPT).'.format(d.get('auth_mode')))
" 2>/dev/null; then
  fail "$AUTH_FILE has no ChatGPT OAuth tokens. Run: codex logout && codex login  (choose ChatGPT)"
fi
ok "ChatGPT OAuth tokens present in $AUTH_FILE"

step "2/4  Install sangpye CLI (uv tool install)"
uv tool install --reinstall "git+$REPO_URL" >/dev/null 2>&1 || uv tool install "git+$REPO_URL"
ok "sangpye $(sangpye --version | awk '{print $2}')"

step "3/4  Drop SKILL.md for Claude Code skill discovery"
mkdir -p "$SKILL_DIR_CLAUDE"
curl -fsSL "https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/SKILL.md" \
  -o "$SKILL_DIR_CLAUDE/SKILL.md"
ok "Claude Code: $SKILL_DIR_CLAUDE/SKILL.md"

if [ -d "$HOME/.hermes/skills" ]; then
  mkdir -p "$SKILL_DIR_HERMES"
  cp "$SKILL_DIR_CLAUDE/SKILL.md" "$SKILL_DIR_HERMES/SKILL.md"
  ok "Hermes: $SKILL_DIR_HERMES/SKILL.md"
fi

step "4/4  Smoke check"
sangpye --help | head -1 | grep -q "sangpye" && ok "sangpye CLI responds to --help"

echo
echo "$(color 32 "🎉 codex-sangpye-skill is ready.")"
echo
echo "Try it (one image + a Korean brief):"
echo "  sangpye --image /path/to/product.jpg --prompt \"무선 이어폰, ANC, 30시간 배터리\" --output ./out"
echo
echo "From inside Claude Code, just ask in Korean:"
echo "  \"이 상품으로 상세페이지 만들어줘: /path/to/product.jpg\""
echo "The agent will dispatch the codex-sangpye skill automatically."
