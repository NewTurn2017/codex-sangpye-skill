#!/usr/bin/env bash
# codex-sangpye-skill — one-shot installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/install.sh | bash
#
# What it does:
#   1. Verifies prerequisites (uv, codex >= 0.121.0, codex OAuth login)
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

# codex >= 0.121.0
if ! command -v codex >/dev/null 2>&1; then
  fail "codex CLI not found. Install from https://github.com/openai/codex (npm install -g @openai/codex)"
fi
CODEX_VER=$(codex --version 2>/dev/null | awk '{print $2}' | head -1)
if [ -z "$CODEX_VER" ]; then
  fail "could not parse codex version"
fi
# Basic version gate — require major 0 with minor >= 121, or anything >= 1.0
if [[ "$CODEX_VER" =~ ^0\.([0-9]+)\. ]]; then
  MINOR="${BASH_REMATCH[1]}"
  if [ "$MINOR" -lt 121 ]; then
    fail "codex $CODEX_VER is too old. Upgrade: npm install -g @openai/codex@latest  (need >= 0.121.0)"
  fi
fi
ok "codex $CODEX_VER"

# codex login status (OAuth/ChatGPT required)
if ! codex login status >/dev/null 2>&1; then
  fail "codex is not logged in. Run: codex login  (pick ChatGPT/OAuth option)"
fi
LOGIN_STATUS=$(codex login status 2>&1 | head -1)
ok "codex login: $LOGIN_STATUS"

# CODEX_API_KEY should be unset (it overrides OAuth)
if [ -n "${CODEX_API_KEY:-}" ]; then
  warn "CODEX_API_KEY is set in your environment — this will override OAuth and may bill against an API key."
  warn "Unset it with: unset CODEX_API_KEY"
fi

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
