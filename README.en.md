# codex-sangpye-skill

<p align="center">
  <a href="examples/demo/skill_hero.png">
    <img src="examples/demo/skill_hero_preview.jpg" alt="codex-sangpye-skill intro — drop product photos, run sangpye once, get a full 상세페이지" width="540">
  </a>
</p>

<p align="center"><sub>↑ Skill overview poster (1080×12720). Click for full-resolution original.</sub></p>

---

> **Korean e-commerce product detail pages, generated from your ChatGPT subscription alone — no OpenAI API key required.**

**한국어 버전:** [README.md](README.md)

Give it 1–14 product photos plus a Korean brief → get **13 section images + a 1080×12720 vertical composite** back. It runs entirely on your `codex login` OAuth session. No API key to manage, no extra billing.

> **What is "sangpye" (상폐)?** It's Korean e-commerce slang short for "상세페이지" — the tall, multi-section product detail page format used on Naver SmartStore, Coupang, Cafe24, and other Korean marketplaces.

<p align="center">
  <a href="examples/demo/combined_preview.jpg">
    <img src="examples/demo/combined_preview.jpg" alt="Live-E2E-generated sample combined detail page (1080×12720 scaled to 540×6360)" width="360">
  </a>
</p>

<p align="center"><sub>↑ Sample produced by the actual live integration test (1080×12720, shown at 50%).</sub></p>

---

## 🚀 Start here — Codex OAuth is the whole point

The one idea that makes this skill interesting: **it runs on your ChatGPT Plus/Pro subscription, not on an API key.**

Internally, every model call tunnels through `codex responses` and inherits your active OAuth session. So:

- No API key to create or store · No separate billing · Runs inside your ChatGPT quota
- `gpt-5.4` multimodal analysis + 5 parallel `image_generation` tool calls → 13 sections auto-assembled
- Typical runtime: **5–10 minutes** (as fast as ~5 min when ChatGPT is idle, up to ~15 min under load). The CLI auto-retries `server overloaded` / `rate_limit` transparently.

### Prerequisites (3 things)

```bash
# 1. codex CLI, latest (>= 0.121.0)
npm install -g @openai/codex@latest
codex --version   # codex-cli 0.123.0 or above

# 2. Log in with your ChatGPT account (NOT an API key)
codex login       # choose "Sign in with ChatGPT"

# 3. CODEX_API_KEY must NOT be set (it overrides OAuth)
echo "${CODEX_API_KEY:-<unset>}"     # must say <unset>
```

> `OPENAI_API_KEY` is **ignored** by `codex responses` at runtime — you don't need to unset it. Only `CODEX_API_KEY` overrides OAuth.

### One-shot install

**macOS / Linux / WSL**
```bash
curl -fsSL https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/install.sh | bash
```

**Windows (PowerShell)**
```powershell
iwr -useb https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/install.ps1 | iex
```

The installer:
1. Verifies `uv`, `codex >= 0.121.0`, and OAuth login status
2. Installs the `sangpye` CLI globally via `uv tool install`
3. Drops `SKILL.md` into `~/.claude/skills/codex-sangpye/` for Claude Code auto-discovery
4. Runs a smoke check

Review the script first if you want: [install.sh](install.sh) / [install.ps1](install.ps1). Safe to re-run (idempotent).

### First run

```bash
sangpye \
  --image ./your_product.jpg \
  --prompt "Wireless earbuds, ANC, 30-hour battery, IPX5" \
  --category electronics \
  --output ./out
```

~5 minutes later:
```json
{"job_id":"a1b2c3d4","combined":"/abs/.../combined.png","sections":["/abs/.../01_hero.png", ...],"elapsed_sec":312.5}
```

> **Note:** the `--prompt` should generally be in Korean for best section copy quality (that's what the model's prompts are tuned for). English prompts also work, but the generated in-image copy will be Korean regardless.

---

## 📸 Actual samples (from the live E2E test)

The repo's [`examples/sample_product.jpg`](examples/sample_product.jpg) (a character reference image called "지니") was fed into `sangpye` with the prompt `"프리미엄 무선 이어폰, ANC, 30시간 배터리"`. Below are 4 representative sections from the 13 that came out:

<table>
<tr>
<th>01 Hero — urgency headline</th>
<th>04 Story — before/after</th>
</tr>
<tr>
<td><a href="examples/demo/01_hero.png"><img src="examples/demo/01_hero.png" alt="01 Hero section" width="360"></a></td>
<td><a href="examples/demo/04_story.png"><img src="examples/demo/04_story.png" alt="04 Story section" width="360"></a></td>
</tr>
<tr>
<th>07 Proof — social proof</th>
<th>13 CTA — final call-to-action</th>
</tr>
<tr>
<td><a href="examples/demo/07_proof.png"><img src="examples/demo/07_proof.png" alt="07 Proof section" width="360"></a></td>
<td><a href="examples/demo/13_cta.png"><img src="examples/demo/13_cta.png" alt="13 CTA section" width="360"></a></td>
</tr>
</table>

Full combined output (all 13 sections stacked, scaled preview):

<p align="center">
  <a href="examples/demo/combined_preview.jpg">
    <img src="examples/demo/combined_preview.jpg" alt="Full 13-section combined detail page" width="540">
  </a>
</p>

<details>
<summary>Excerpt of this run's <code>analysis.json</code> — AI-generated Product DNA + Korean copy + 13 section prompts (click to expand)</summary>

```json
{
  "product_analysis": {
    "name": "지니 무선 이어폰",
    "category": "electronics",
    "usp": "30시간 재생의 새로운 기준",
    "pain_points": ["자주 끊기는 연결", "짧은 배터리", "방수 없는 이전 모델"],
    "tone": "premium, trustworthy",
    "positioning_tier": "premium_indie"
  },
  "bundles": [
    {"bundle_id": "B1_HERO", "size": {"width": 1088, "height": 1600}, ...},
    {"bundle_id": "B2_OPENING", "size": {"width": 1088, "height": 2800}, ...},
    "..."
  ]
}
```

Full JSON: [examples/demo/analysis.json](examples/demo/analysis.json).
</details>

---

## 🎯 Output spec

### The 13 sections (emotional journey)

| # | Section | Height | Purpose |
|---|---|---|---|
| 1 | **Hero** | 1600px | Urgency headline + main product shot |
| 2 | Pain | 800px | "Do you struggle with…?" empathy |
| 3 | Problem | 800px | Define the core problem |
| 4 | **Story** | 1200px | Before→After narrative |
| 5 | Solution | 800px | Introduce the solution |
| 6 | How | 900px | How it works (visual) |
| 7 | **Proof** | 1420px | Reviews, numbers, testimonials |
| 8 | Authority | 800px | Expert endorsement |
| 9 | Benefits | 1200px | Key benefits, visually |
| 10 | Risk | 800px | Guarantee / return policy |
| 11 | Compare | 800px | Final before/after |
| 12 | Filter | 700px | Target audience filter |
| 13 | **CTA** | 900px | Final call-to-action |

Total: **1080 × 12720 pixels**.

### Output directory layout

```
./out/a1b2c3d4/                 # {job_id}
├── analysis.json               # Product DNA + 5 bundle specs + 13 Korean copies
├── bundles/
│   ├── B1_HERO.png             # 1088×1600 raw bundle
│   ├── B2_OPENING.png          # 1088×2800
│   ├── B3_SOLUTION.png         # 1088×3120
│   ├── B4_TRUST.png            # 1088×2800
│   └── B5_ACTION.png           # 1088×2400
├── sections/                   # 1080×variable (13 images)
│   ├── 01_hero.png            (1600)
│   ├── 02_pain.png            (800)
│   ├── ...
│   └── 13_cta.png             (900)
└── combined.png                # 1080×12720 vertical composite
```

---

## 🤖 Use it as a Claude Code / Codex / Hermes skill

The installer drops `SKILL.md` into `~/.claude/skills/codex-sangpye/`. Open a new Claude Code session and just ask in Korean (or English) — the agent will auto-dispatch the skill.

### Example (natural language)

```
> Generate a detail page from this photo: ./mug.jpg
> Prompt: "handmade mug, microwave-safe, artisan ceramic"
```

Claude will:
1. Recognize the `codex-sangpye` skill from the available-skills list
2. Invoke `sangpye --image ./mug.jpg --prompt "..." --output ./out`
3. Show stderr progress live (~5 min)
4. Parse the result JSON and return the `combined.png` path

### Manual skill drop (if you skipped the installer)

```bash
mkdir -p ~/.claude/skills/codex-sangpye
curl -fsSL https://raw.githubusercontent.com/NewTurn2017/codex-sangpye-skill/main/SKILL.md \
  -o ~/.claude/skills/codex-sangpye/SKILL.md
```

For Hermes:
```bash
mkdir -p ~/.hermes/skills/creative/codex-sangpye
cp ~/.claude/skills/codex-sangpye/SKILL.md ~/.hermes/skills/creative/codex-sangpye/
```

---

## 🛠️ Full CLI reference

```bash
sangpye \
  --image ./photos/earbuds_01.jpg \
  --image ./photos/earbuds_02.jpg \
  --image ./photos/earbuds_lifestyle.jpg \
  --prompt "프리미엄 무선 이어폰. 30시간 재생, ANC, IPX5 방수, 인체공학 디자인." \
  --category electronics \
  --quality high \
  --output ./out
```

### Flags

| Flag | Required | Default | Description |
|---|---|---|---|
| `--image PATH` | ✅ | — | Repeat 1–14 times. Product image file. |
| `--prompt TEXT` | ✅ | — | Korean product brief (English works too, but in-image copy stays Korean). |
| `--category` | | `general` | `electronics` \| `fashion` \| `food` \| `beauty` \| `home` \| `general` |
| `--output DIR` | | `./sangpye-output` | Parent output directory (a `{job_id}/` subdir is created inside). |
| `--quality` | | `high` | `standard` \| `high`. Drop to `standard` if you hit rate limits. |
| `--job-id ID` | | random 8-char hex | Override the auto-generated id (becomes the subdir name). |
| `--codex-bin PATH` | | `codex` | Path to the `codex` binary if it's not on PATH. |

### Output contract

- **stdout**: on success, a single JSON line — `job_id`, `output_dir`, `combined`, `sections[13]`, `plan_path`, `elapsed_sec`
- **stderr**: human-readable progress (`[analyzing] Codex(gpt-5.4) 분석 중...`, `[generating_images] ...`, etc.)

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Codex auth error (not logged in / session expired) |
| 2 | Input error (bad path, too many images, etc.) |
| 3 | API / generation error — `combined.png` was NOT produced |
| 4 | Filesystem error (permissions, disk full) |
| 5 | **Partial success** — some bundles failed but `combined.png` was still produced (failed sections use dark placeholders). Check the `failed_bundles` JSON field. |

### 🔁 Auto-resume

If a run partially fails (e.g., one bundle exhausted all retries under server load), **re-invoke with the same `--output` and `--job-id`**:

```bash
sangpye \
  --image ./your_product.jpg \
  --prompt "..." \
  --output ./out \
  --job-id <same as previous run>    # stderr shows the id on failure
```

- `output_dir/{job_id}/analysis.json` exists → **Step 1 (gpt-5.4 analysis) is auto-skipped** — saves quota + ~30s
- `bundles/{bundle_id}.png` already present → **that bundle is NOT re-generated**. With 4 of 5 already complete, only the failed one retries (~2-3 min)
- `sections/` + `combined.png` are always rebuilt (their cost is negligible)

Net UX: "re-run = pick up where it left off, retry only what failed."

---

## 🧠 How it works

```
Input: 1–14 images + Korean prompt
   ↓
[1] gpt-5.4 analysis (multimodal)
   → ProductDNA + 5 Bundle specs + 13 Korean copies
   ↓
[2] image_generation tool × 5 calls (concurrency = 3)
   → 5 large bundle images (each 1088×N)
   ↓
[3] Slice each bundle by Y-coordinate
   → 13 section images (each 1080×variable)
   ↓
[4] Pillow vertical composition
   → combined.png (1080×12720)
```

No Celery, no Redis, no Docker. Just a single local `sangpye` process that runs synchronously until combined.png is on disk.

`codex_client.py` wraps the `codex responses` subprocess call. If you want to swap in a faster transport later (e.g. direct HTTPS to the private ChatGPT endpoint — see [NomaDamas/god-tibo-imagen](https://github.com/NomaDamas/god-tibo-imagen)), only that one file needs changing.

---

## 🏗️ Project origin

This skill is an **extract** of the core pipeline from a private FastAPI + Celery + Redis production backend that currently serves `api.codewithgenie.com/productpage/`. The port drops all the multi-tenant / queue / HTTP infrastructure and keeps only what's needed to run the pipeline synchronously on a user's machine.

| Original | Here | Change |
|---|---|---|
| `app/services/openai_client.py` | `sangpye_skill/codex_client.py` | Rewritten: subprocess wrapper around `codex responses` |
| `app/services/pipeline.py` | `sangpye_skill/pipeline.py` | Synchronous variant; no Celery, no Redis, no cancel hooks |
| `app/services/analysis.py` | `sangpye_skill/analysis.py` | Same prompts + schemas; calls `codex_client.call_responses` |
| `app/services/image_generator_v3.py` | `sangpye_skill/image_generator.py` | Same retry/concurrency logic; calls `codex_client.generate_image_with_reference` |
| `app/services/{bundle_slicer, composer, product_dna, section_language, category_briefs}.py` | same names | Vendored verbatim |
| FastAPI / Celery / Redis / Docker | — | Dropped |

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---|---|
| `codex: command not found` | `npm install -g @openai/codex` |
| `codex --version` < 0.121.0 | `npm install -g @openai/codex@latest` |
| `error: codex login status failed` | `codex login` → "Sign in with ChatGPT" |
| OAuth doesn't seem to be used | `unset CODEX_API_KEY` (or `Remove-Item Env:CODEX_API_KEY` on Windows) |
| `error: codex responses expects a streaming payload` | Upgrade codex |
| `error (codex): ... model not available` | Your ChatGPT tier may not expose `gpt-5.4` — upgrade subscription |
| `error (codex): rate_limit` | ChatGPT quota throttle — wait, or use `--quality standard` |
| Runs take >10 min | Retries absorbing overload — let it finish. Expected under ChatGPT load |
| Frequent `server overloaded` | Lower concurrency: `SANGPYE_MAX_CONCURRENCY=1` (default is 2). Longer total, fewer retries |
| Pipeline hangs | Check `codex --version` ≥ 0.121.0; older versions use a different event schema |
| Run crashed mid-way | `output_dir/{job_id}/analysis.json` was saved right after Step 1 — you can reuse it manually |

---

## 🔗 Related

- Private origin backend: `make-detailed-product-page` (FastAPI + Celery + Redis)
- Reference skill: [Gyu-bot/codex-image-generation-skill](https://github.com/Gyu-bot/codex-image-generation-skill) — minimal single-image variant
- Faster transport idea: [NomaDamas/god-tibo-imagen](https://github.com/NomaDamas/god-tibo-imagen) — direct HTTPS to the private ChatGPT endpoint (v0.2 candidate)

---

## 📄 License

MIT — fork and use freely. Maintained by [@NewTurn2017](https://github.com/NewTurn2017).
