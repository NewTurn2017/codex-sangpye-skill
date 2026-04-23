---
name: codex-sangpye
description: Generate a 13-section Korean e-commerce 상세페이지(상폐) image set (1080x7500 combined image + 13 individual section PNGs) from 1-14 product photos plus a Korean brief, using the Codex CLI's `codex responses` entrypoint under the active Codex OAuth session (no separate OpenAI API key required).
version: 0.1.0
author: genie
license: MIT
metadata:
  hermes:
    tags: [codex, image-generation, oauth, ecommerce, korean, sangpye, detail-page]
    related_skills: [codex-image-generation]
---

## When to use

When the user wants a Korean e-commerce product detail page ("상세페이지" / "상폐") asset set — 13 emotional-journey sections (Hero → Pain → Problem → Story → Solution → How → Proof → Authority → Benefits → Risk → Compare → Filter → CTA) plus a single 1080×7500 combined PNG — generated from 1–14 product photos and a Korean brief.

Prefer this skill over invoking image generation by hand, because:
- It runs the full analysis (gpt-5.4) + 5-bundle parallel image generation (orchestrator + image_generation tool) + slicing + vertical composition pipeline.
- It uses your Codex OAuth session — no API key, no per-token billing.
- One command, one JSON result.

## Preconditions

1. `codex >= 0.121.0` is on PATH (check with `codex --version`) and `codex login status` reports an active OAuth/ChatGPT session (not an API key).
2. `CODEX_API_KEY` env var is **unset** — if set, it overrides OAuth at runtime. (`OPENAI_API_KEY` is ignored by `codex responses`; no need to unset.)
3. `sangpye --version` succeeds (install via `uv tool install git+https://github.com/<YOUR USER>/codex-sangpye-skill`).
4. 1–14 product image files exist locally.

If any precondition fails, tell the user how to fix and stop.

## Command path

`sangpye` (installed globally via `uv tool install`).

## Parameters

| Flag | Required | Default | Description |
|---|---|---|---|
| `--image PATH` | yes | — | Repeat 1–14 times. Product image path. |
| `--prompt TEXT` | yes | — | Korean product brief. |
| `--category` | no | `general` | One of: electronics, fashion, food, beauty, home, general. |
| `--output DIR` | no | `./sangpye-output` | Parent output directory. |
| `--quality` | no | `high` | One of: standard, high. |
| `--job-id ID` | no | random 8-char hex | Override the job id. |
| `--codex-bin PATH` | no | `codex` | Path to the `codex` binary. |

## Basic usage

```bash
sangpye \
  --image ./photos/earbuds_01.jpg \
  --prompt "무선 이어폰, ANC 탑재, 30시간 배터리, IPX5 방수" \
  --output ./out
```

## Example with explicit options

```bash
sangpye \
  --image ./photos/earbuds_01.jpg \
  --image ./photos/earbuds_02.jpg \
  --image ./photos/earbuds_lifestyle.jpg \
  --prompt "프리미엄 무선 이어폰. 30시간 재생, ANC, IPX5 방수, 인체공학 디자인. 20-40대 직장인 대상." \
  --category electronics \
  --quality high \
  --output ./out
```

## Expected result

`stdout` (single JSON line):
```json
{"job_id":"a1b2c3d4","output_dir":"/abs/path/to/out/a1b2c3d4","combined":"/abs/path/to/out/a1b2c3d4/combined.png","sections":["/abs/path/to/out/a1b2c3d4/sections/01_hero.png", "..."],"plan_path":"/abs/path/to/out/a1b2c3d4/analysis.json","elapsed_sec":252.4}
```

Show the user:
1. The absolute path to `combined.png` (the main deliverable).
2. The `job_id` so they can find the artifacts again.
3. Optionally, the list of 13 individual section PNGs.

## Troubleshooting

- **`error: codex login status failed`** → Run `codex logout && codex login`, pick the OAuth/ChatGPT option. Note: `OPENAI_API_KEY` in the shell is ignored at runtime; only `CODEX_API_KEY` overrides OAuth.
- **`error: codex responses expects a streaming payload`** → Upgrade to `codex >= 0.121.0` (0.123.0 tested).
- **`error (codex): ... model not available`** → The user's ChatGPT subscription tier may not include `gpt-5.4`. Surface the error verbatim — do not retry.
- **`error (codex): rate_limit`** → ChatGPT subscription is throttling. Wait a few minutes and retry, or pass `--quality standard`.
- **Pipeline hangs** → Likely `codex` version mismatch. Upgrade to `0.121.0+`.

## Agent rule

After a successful run, ALWAYS show the user the absolute path to `combined.png` and the `job_id`. Do not silently retry on errors — surface them so the user can decide. Do not invoke this skill more than once per user request unless explicitly asked.
