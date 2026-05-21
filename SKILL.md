---
name: codex-sangpye
description: Generate a 13-section Korean e-commerce 상세페이지(상폐) image set (1080x12720 combined image + 13 individual section PNGs) from 1-14 product photos plus a Korean brief, using the active Codex OAuth session (ChatGPT subscription — no separate OpenAI API key required).
version: 0.4.0
author: genie
license: MIT
metadata:
  hermes:
    tags: [codex, image-generation, oauth, ecommerce, korean, sangpye, detail-page]
    related_skills: [codex-image-generation]
version_note: "0.4.0 — adds --layout cards (rounded-card composition with margins)"
---

## When to use

When the user wants a Korean e-commerce product detail page ("상세페이지" / "상폐") asset set — 13 emotional-journey sections (Hero → Pain → Problem → Story → Solution → How → Proof → Authority → Benefits → Risk → Compare → Filter → CTA) plus a single 1080×12720 combined PNG — generated from 1–14 product photos and a Korean brief.

Prefer this skill over invoking image generation by hand, because:
- It runs the full analysis (gpt-5.5) + 5-bundle parallel image generation (orchestrator + image_generation tool) + slicing + vertical composition pipeline.
- It uses your Codex OAuth session — no API key, no per-token billing.
- One command, one JSON result.

## How it talks to Codex (0.3.0+)

Codex CLI 0.130 removed the `codex responses` subcommand, so this skill no longer shells out. The `sangpye` CLI now reads the OAuth tokens written by `codex login` (`~/.codex/auth.json`) and POSTs directly to `https://chatgpt.com/backend-api/codex/responses` — the same endpoint the old subcommand used. Wire format, model (`gpt-5.5` + `image_generation` tool), and ChatGPT-subscription billing are unchanged. You no longer need any specific version of the `codex` binary on PATH; only the auth file matters.

## Preconditions

1. `~/.codex/auth.json` exists with a ChatGPT OAuth session. If missing or expired, run `codex login` once and pick the **ChatGPT** option (not API key).
2. `sangpye --version` succeeds (install via `uv tool install git+https://github.com/NewTurn2017/codex-sangpye-skill`).
3. 1–14 product image files exist locally.

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
| `--layout` | no | `flat` | `flat` = sections stacked edge-to-edge (full-bleed, default — product 상폐). `cards` = rounded cards on a unified dark background with margins (lecture / content). |
| `--card-side` | no | `30` | [cards] left/right margin px. |
| `--card-gap` | no | `40` | [cards] vertical gap between cards px. |
| `--card-pad` | no | `40` | [cards] top/bottom page padding px. |
| `--card-radius` | no | `24` | [cards] card corner radius px. |
| `--card-bg` | no | `#0B1020` | [cards] unified background color. |

## Layouts: flat vs cards

`--layout flat` (default) stacks the 13 sections with **zero gap** into the canonical **1080×12720** PNG — the standard full-bleed e-commerce 상폐 look.

`--layout cards` places each section as a **rounded card on a unified dark background** with even margins (left/right `--card-side`, between cards `--card-gap`, page top/bottom `--card-pad`). This removes the abrupt background-color jumps at section seams and gives a tidy "card rhythm" — well suited to lecture / content detail pages (e.g. the `/video-use-summary` pipeline passes `--layout cards`). The combined height is no longer exactly 12720 because each card is width-inset and gaps are added. The `--card-*` flags only take effect with `--layout cards`.

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

- **`error: ~/.codex/auth.json not found`** → Run `codex login` and pick the ChatGPT/OAuth option.
- **`error: ~/.codex/auth.json has no ChatGPT OAuth tokens`** → The current auth.json is API-key mode. Run `codex logout && codex login`, choose ChatGPT.
- **`error: ChatGPT OAuth rejected the request (HTTP 401)`** → The access token in `~/.codex/auth.json` expired (lifetime ~10 days). Run `codex login` to refresh.
- **`error (codex): HTTP 500: ...` or `HTTP 503`** → Upstream/ChatGPT outage. Retry in a few minutes.
- **`responses network error`** → Local network problem reaching `chatgpt.com`. Check connectivity.
- **`error (codex): rate_limit` / `429`** → ChatGPT subscription is throttling. Wait, retry, or pass `--quality standard`.
- **Frequent `server overloaded` retries visible in stderr** → Lower parallelism by running with `SANGPYE_MAX_CONCURRENCY=1 sangpye ...` (default is 2).
- **`The model 'gpt-5.5' does not exist or you do not have access to it`** → Your ChatGPT subscription tier does not yet include `gpt-5.5`. Set `SANGPYE_MODEL=gpt-5.4` as a temporary fallback, or surface the error verbatim.

## Runtime expectations

- **Typical**: 5–10 minutes for a full 13-section run.
- **Under load**: up to ~15 minutes; the CLI transparently retries `server overloaded` and `rate_limit` events with exponential backoff (10s/30s/60s/90s/150s × 1.5 for overload).
- `analysis.json` is persisted to `output_dir/{job_id}/analysis.json` **immediately after Step 1** (Codex analysis), so it survives later image-gen failures.
- Stderr shows per-bundle lifecycle events (`▶ B2_OPENING generating...`, `⟲ B2_OPENING overloaded, backing off 45s`, `✓ B2_OPENING done in 67.3s`) so progress is visible during long runs.

## Agent rule

After a successful run, ALWAYS show the user the absolute path to `combined.png` and the `job_id`. Do not silently retry on errors — surface them so the user can decide. Do not invoke this skill more than once per user request unless explicitly asked.
