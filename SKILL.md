---
name: codex-sangpye
description: Generate a 13-section Korean e-commerce 상세페이지(상폐) image set (1080x12720 combined image + 13 individual section PNGs) from 1-14 product photos plus a Korean brief, using the Codex CLI's `codex responses` entrypoint under the active Codex OAuth session (no separate OpenAI API key required).
version: 0.2.0
author: genie
license: MIT
metadata:
  hermes:
    tags: [codex, image-generation, oauth, ecommerce, korean, sangpye, detail-page]
    related_skills: [codex-image-generation]
---

## When to use

When the user wants a Korean e-commerce product detail page ("상세페이지" / "상폐") asset set — 13 emotional-journey sections (Hero → Pain → Problem → Story → Solution → How → Proof → Authority → Benefits → Risk → Compare → Filter → CTA) plus a single 1080×12720 combined PNG — generated from 1–14 product photos and a Korean brief.

Prefer this skill over invoking image generation by hand, because:
- It runs the full analysis (gpt-5.5) + 5-bundle parallel image generation (orchestrator + image_generation tool) + slicing + vertical composition pipeline.
- It uses your Codex OAuth session — no API key, no per-token billing.
- One command, one JSON result.

## Preconditions

1. `codex >= 0.124.0` is on PATH (check with `codex --version`) and `codex login status` reports an active OAuth/ChatGPT session (not an API key). Older versions cannot route `gpt-5.5`.
2. `CODEX_API_KEY` env var is **unset** — if set, it overrides OAuth at runtime. (`OPENAI_API_KEY` is ignored by `codex responses`; no need to unset.)
3. `sangpye --version` succeeds (install via `uv tool install git+https://github.com/NewTurn2017/codex-sangpye-skill`).
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
{"job_id":"a1b2c3d4","output_dir":"/abs/...","combined":"/abs/.../combined.png","sections":["/abs/.../01_hero.png", "..."],"plan_path":"/abs/.../analysis.json","elapsed_sec":252.4,"failed_bundles":[],"reused_bundles":[]}
```

Show the user:
1. The absolute path to `combined.png` (the main deliverable).
2. The `job_id` so they can find the artifacts again.
3. Optionally, the list of 13 individual section PNGs.

### Partial success (exit code 5)

If `failed_bundles` is non-empty, the CLI exited with code 5: `combined.png` was still produced, but some sections use dark placeholders. Tell the user:
- How many bundles failed + which ones (e.g. `"B2_OPENING"`)
- They can **retry only the failed bundles** by re-running with the same `--output` and `--job-id` — the skill auto-resumes from the saved `analysis.json` and existing `bundles/*.png`.

### Auto-resume

When `output_dir/{job_id}/` already contains `analysis.json`:
- Step 1 (gpt-5.5 analysis) is skipped — the stored plan is reused.
- Individual bundles with a non-empty `bundles/{id}.png` on disk are reused.
- Only missing bundles are generated; then slice + compose run over the full set.

This makes a failed run trivial to recover from without re-burning quota. Suggest this to the user whenever they see `exit=5` or a bundle failure.

## Troubleshooting

- **`error: codex login status failed`** → Run `codex logout && codex login`, pick the OAuth/ChatGPT option. Note: `OPENAI_API_KEY` in the shell is ignored at runtime; only `CODEX_API_KEY` overrides OAuth.
- **`error: codex responses expects a streaming payload`** → Upgrade to `codex >= 0.124.0` (`npm i -g @openai/codex@latest`).
- **`error (codex): The model 'gpt-5.5' does not exist or you do not have access to it`** → Either (a) the codex CLI is too old — upgrade to `>= 0.124.0`; or (b) the user's ChatGPT subscription tier does not yet include `gpt-5.5` — fall back temporarily by setting `SANGPYE_MODEL=gpt-5.4` (per OpenAI's rollout note) or surface the error verbatim.
- **`error (codex): rate_limit`** → ChatGPT subscription is throttling. Wait a few minutes and retry, or pass `--quality standard`.
- **Frequent `server overloaded` retries visible in stderr** → Lower parallelism by running with `SANGPYE_MAX_CONCURRENCY=1 sangpye ...` (default is 2). Total runtime grows but retries shrink.
- **Pipeline hangs** → Likely `codex` version mismatch. Upgrade to `0.124.0+`.

## Runtime expectations

- **Typical**: 5–10 minutes for a full 13-section run.
- **Under load**: up to ~15 minutes; the CLI transparently retries `server overloaded` and `rate_limit` events with exponential backoff (10s/30s/60s/90s/150s × 1.5 for overload).
- `analysis.json` is persisted to `output_dir/{job_id}/analysis.json` **immediately after Step 1** (Codex analysis), so it survives later image-gen failures.
- Stderr shows per-bundle lifecycle events (`▶ B2_OPENING generating...`, `⟲ B2_OPENING overloaded, backing off 45s`, `✓ B2_OPENING done in 67.3s`) so progress is visible during long runs.

## Agent rule

After a successful run, ALWAYS show the user the absolute path to `combined.png` and the `job_id`. Do not silently retry on errors — surface them so the user can decide. Do not invoke this skill more than once per user request unless explicitly asked.
