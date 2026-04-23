# codex-sangpye-skill

한국 이커머스 **상세페이지(상폐)** 생성 스킬. 상품 사진 1~14장 + 한국어 프롬프트 → 13장 섹션 이미지 + 1080×12720 합성 이미지. 당신의 Codex OAuth 세션(ChatGPT Plus/Pro)을 그대로 씁니다. OpenAI API 키 불필요.

> 왜 "상폐"? 상세페이지의 한국 이커머스 업계 속어. 패션/뷰티/가전 셀러들이 다 이렇게 부릅니다.

## What it produces

- **13 section PNGs** at 1080×H (variable height per section): Hero → Pain → Problem → Story → Solution → How → Proof → Authority → Benefits → Risk → Compare → Filter → CTA
- **1 combined PNG** at 1080×12720 (vertical composition)
- **1 analysis.json** with Product DNA, bundle prompts, Korean copy

## Install

```bash
# 1. Prereqs
brew install uv
# codex install: see https://github.com/openai/codex
codex --version   # must be >= 0.121.0

# 2. Log in with your ChatGPT account (NOT API key)
codex login       # pick the OAuth / ChatGPT option
unset CODEX_API_KEY   # if set, it overrides OAuth
# (OPENAI_API_KEY is ignored at runtime — no need to unset.)

# 3. Install the skill
uv tool install git+https://github.com/<YOUR USER>/codex-sangpye-skill

# 4. Verify
sangpye --version
codex login status
```

## Use (CLI)

```bash
sangpye \
  --image ./photos/earbuds_01.jpg \
  --image ./photos/earbuds_02.jpg \
  --prompt "무선 이어폰, ANC 탑재, 30시간 배터리, IPX5 방수" \
  --category electronics \
  --output ./out
```

Stdout (one JSON line on success):
```json
{"job_id":"a1b2c3d4","combined":"/abs/path/.../combined.png","sections":["/abs/path/.../01_hero.png","..."],"elapsed_sec":252.4}
```

Stderr shows live progress.

## Use (as a Claude / Hermes / Codex skill)

Drop `SKILL.md` from this repo into your skills directory (e.g. `~/.claude/skills/codex-sangpye/SKILL.md` or `~/.hermes/skills/creative/codex-sangpye/SKILL.md`). The agent will discover the skill and call `sangpye` for you.

## How it works

1. **Analyze** — gpt-5.4 multimodal call returns ProductDNA + 5 bundle specs + Korean copy.
2. **Generate** — 5 parallel image calls via the `image_generation` tool, each using your master image as a reference, produce 5 large bundle PNGs (1088×{1600, 2800, 3120, 2800, 2400}).
3. **Slice** — each bundle is sliced by Y-coordinate into its constituent sections (1–3 per bundle, 13 total).
4. **Compose** — Pillow stitches the 13 sections vertically into `combined.png`.

All four steps run synchronously in one process. No Docker, no Redis, no Celery.

## Architecture (extract from the production backend)

Ported from the FastAPI/Celery production stack at `make-detailed-product-page` (branch `feat/openai-migration`):

| Original | Here | Change |
|---|---|---|
| `app/services/openai_client.py` | `sangpye_skill/codex_client.py` | Rewritten: subprocess wrapper around `codex responses` |
| `app/services/pipeline.py` | `sangpye_skill/pipeline.py` | Synchronous; no Celery, no Redis, no cancel hooks |
| `app/services/analysis.py` | `sangpye_skill/analysis.py` | Same prompt + schema; calls `codex_client.call_responses` |
| `app/services/image_generator_v3.py` | `sangpye_skill/image_generator.py` | Same retry/concurrency logic; calls `codex_client.generate_image_with_reference` |
| `app/services/{bundle_slicer, composer, product_dna, section_language, category_briefs}.py` | same names | Vendored as-is |
| FastAPI / Celery / Redis / Docker | — | Dropped |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `codex: command not found` | Install codex CLI from https://github.com/openai/codex |
| `codex --version` < `0.121.0` | Upgrade — the `responses` subcommand is required |
| `error: codex login status failed` | `codex login` and pick OAuth/ChatGPT option |
| OAuth not being used despite `codex login` | Check `CODEX_API_KEY`; if set, `unset CODEX_API_KEY` |
| `error (codex): model not available` | Your ChatGPT subscription tier may not expose `gpt-5.4` |
| `error (codex): rate_limit` | ChatGPT subscription is throttling — wait or use `--quality standard` |
| Slow runs (>10 min) | OAuth may serialize parallel calls; this is expected |

## License

MIT.
