# Design — `codex-sangpye-skill` (Codex OAuth, fully local, separate OSS repo)

**Date**: 2026-04-23
**Owner**: genie
**Status**: Approved — ready for implementation plan
**Reference skill**: https://github.com/Gyu-bot/codex-image-generation-skill

> **Model upgrade note (2026-04-24):** all `gpt-5.4` references in this spec describe the original Phase 0 validation. The shipped skill now defaults to `gpt-5.5` (released 2026-04-23) via the same `codex responses` payload shape — re-validated end-to-end on `codex-cli >= 0.124.0`. Set `SANGPYE_MODEL=gpt-5.4` to fall back during the rollout.

---

## 1. Goal

Package the current FastAPI product-detail-page backend (`make-detailed-product-page`, branch `feat/openai-migration`) as a **local, Docker-less Claude Code / Codex CLI skill** that:

1. Runs the full 5-bundle → 13-section → 1080×7500 combined image pipeline synchronously on the user's machine.
2. Uses the user's **Codex OAuth session** (ChatGPT Plus/Pro) for **both** text analysis and image generation — no `OPENAI_API_KEY`, no separate billing.
3. Ships as a proper open-source Python package installable via `uv tool install git+...`, exposing a single `sangpye` console command.
4. Lives in its own public GitHub repo (`codex-sangpye-skill`), separate from the production backend, so external users can adopt it.

## 2. Success Criteria

- `codex login status` — OK, then `sangpye --image X --image Y --prompt "..." --output ./out` produces `combined.png` (1080×7500) + 13 section PNGs in under 10 minutes end-to-end on a typical ChatGPT-authenticated session.
- Zero Docker, zero Redis, zero Celery, zero `OPENAI_API_KEY` on the user's machine.
- Install flow: `uv tool install git+https://github.com/<user>/codex-sangpye-skill` + drop `SKILL.md` into `~/.claude/skills/` (or Hermes equivalent). No other setup.
- The skill is usable both as a CLI and as a SKILL-invoked tool from inside Codex/Claude Code.
- All existing pipeline quality (prompts, DNA injection, bundle slicing, composer) is preserved — only the transport layer changes.

## 3. Non-goals

- Not replacing the production FastAPI server — that continues serving `api.codewithgenie.com/sangpye/` for web users.
- Not supporting `OPENAI_API_KEY` fallback in v0.1 — OAuth-only. If the spike fails, the project is abandoned (not forked into an API-key variant).
- Not supporting Windows native in v0.1 — macOS/Linux first (same as `codex` CLI support matrix).
- Not building a UI — CLI only. Web UI remains in `make-detailed-product-page/web/`.
- Not vendoring the FastAPI/Celery/Redis layer — dropped entirely.

## 4. Phase 0 — OAuth Verification Spike (GO/NO-GO gate)

**Rationale**: The reference skill only proves `codex responses` works for **image generation with text-only prompts**. Our pipeline also needs (a) multimodal text analysis with image inputs returning structured JSON, and (b) image-to-image generation using a reference master image. Both must work under OAuth before we commit to the full extract.

### Location

Spike lives inside the **current repo** under `spike/codex_oauth/` (not the new repo yet). It is throwaway validation code.

```
make-detailed-product-page/
└── spike/
    └── codex_oauth/
        ├── 01_text_analysis.py     # Multimodal text → JSON
        ├── 02_image_with_ref.py    # Image-to-image 1088×1600
        ├── 03_parallel_3.py        # 3 concurrent image calls
        ├── sample_inputs/
        │   ├── earbuds_01.jpg      # 1-2 sample product images
        │   └── earbuds_02.jpg
        └── README.md               # Results + GO/NO-GO verdict
```

**NOTE (2026-04-23)**: the payload snippets below were the initial hypothesis. During spike execution several OAuth-only constraints surfaced — see **§14.1** for the corrected call-shape table. The snippets here remain as historical record of how the spike scripts were initially written before we discovered the server's validation.

### Spike payloads (concrete — initial hypothesis)

All three scripts shell out to `codex responses` via `subprocess.run(["codex", "responses"], input=json.dumps(payload), ...)` and parse the JSONL stdout stream — identical pattern to `codex-image-generation-skill/scripts/gen_image.py`.

**Spike 01 — text analysis (gpt-5.4 multimodal + JSON output)**:

```python
payload = {
    "model": "gpt-5.4",
    "input": [
        {"role": "system", "content": "Return a single JSON object with keys: name, category, usp, key_features (list). No prose."},
        {"role": "user", "content": [
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64_sample_01}"},
            {"type": "input_text", "text": "이 제품을 한국 이커머스용으로 분석해줘."},
        ]},
    ],
    "text": {"format": {"type": "json_object"}},
    "stream": True,
}
```
- **PASS** if accumulated `response.output_text.delta` events concatenate into a JSON string that parses and has all 4 keys. The stream terminator is `response.completed` — the Codex CLI does **not** emit `response.output_text.done` (verified against `codex-rs/codex-api/src/common.rs` ResponseEvent enum in openai/codex@rust-v0.123.0).
- **FAIL** signals: auth error, model not available to OAuth tier, JSON format unsupported, empty output.

**Spike 02 — image-to-image with reference (1088×1600 hero bundle)**:

```python
payload = {
    "model": "gpt-image-2",
    "input": [{
        "role": "user",
        "content": [
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64_sample_01}"},
            {"type": "input_text", "text": "Cinematic product hero portrait, 1088×1600 vertical, 긴급 헤드라인 한국어 카피 포함 (예: '지금, 무선의 한계를 넘다'). Dark techwear lighting."},
        ],
    }],
    "tools": [{"type": "image_generation", "size": "1088x1600", "quality": "high"}],
    "tool_choice": {"type": "image_generation"},
    "stream": True,
}
```
- **PASS** if a `response.output_item.done` event with `item.type == "image_generation_call"` arrives carrying a base64 `result`, and the decoded PNG is 1088×1600 with the reference product recognizable and Korean text legible.
- **FAIL** signals: tool unavailable, size not supported, reference image ignored, text garbled.

**Spike 03 — concurrency (3 parallel image calls)**:

Fires 3 copies of Spike 02 payload concurrently via `asyncio.gather` + `asyncio.to_thread(subprocess.run, ...)`. Mirrors `ImageGeneratorV3.MAX_CONCURRENCY = 3`.
- **PASS** if all 3 complete successfully within 3 minutes total, no rate-limit errors.
- **FAIL** signals: ChatGPT subscription throttles parallel image gen, unclear retry semantics.

### GO/NO-GO decision

- **All 3 PASS** → proceed with full design, scaffold new repo.
- **Any 1 FAIL** → project abandoned per user directive. Document findings in `spike/codex_oauth/README.md`.

Time budget: 30–60 minutes. Cost: counts against the user's ChatGPT subscription usage quota (no per-token billing under OAuth) — roughly equivalent to a few minutes of typical image generation.

## 5. New Repo — scaffold + packaging

### 5.1 Repo basics

- **Name**: `codex-sangpye-skill`
- **Location** (local dev): `~/dev/side/codex-sangpye-skill/`
- **License**: MIT (matches reference skill)
- **Python**: 3.12 (matches production backend)
- **Build/install tool**: `uv` (modern, reproducible, fast)

### 5.2 Folder layout

```
codex-sangpye-skill/
├── SKILL.md                      # Frontmatter + agent instructions (Claude/Hermes skill format)
├── README.md                     # Public-facing install/usage/troubleshooting
├── LICENSE                       # MIT
├── pyproject.toml                # uv-compatible, declares console script `sangpye`
├── .python-version               # "3.12"
├── .gitignore
├── sangpye_skill/            # Importable Python package
│   ├── __init__.py               # __version__ = "0.1.0"
│   ├── cli.py                    # argparse entry; `main()` is the console-script target
│   ├── codex_client.py           # NEW — subprocess wrapper for `codex responses`
│   ├── pipeline.py               # PORTED from app/services/pipeline.py
│   ├── analysis.py               # PORTED from app/services/analysis.py
│   ├── image_generator.py        # PORTED from app/services/image_generator_v3.py
│   ├── bundle_slicer.py          # VENDORED as-is from app/services/bundle_slicer.py
│   ├── composer.py               # VENDORED as-is from app/services/composer.py
│   ├── product_dna.py            # VENDORED as-is from app/services/product_dna.py
│   ├── section_language.py       # VENDORED as-is from app/services/section_language.py
│   └── category_briefs.py        # VENDORED as-is from app/services/category_briefs.py
├── scripts/
│   └── generate.py               # Fallback thin wrapper for users without console-script install
├── tests/
│   ├── __init__.py
│   ├── test_codex_client.py      # Unit tests with mocked subprocess
│   └── test_pipeline_live.py     # Live OAuth integration test (pytest marker `live`, skipped by default)
└── examples/
    └── sample_product.jpg        # Demo image used by README examples
```

### 5.3 `pyproject.toml` (key fields)

```toml
[project]
name = "codex-sangpye-skill"
version = "0.1.0"
description = "Generate Korean e-commerce product detail page images (13 sections, 1080×7500 combined) via Codex OAuth."
requires-python = ">=3.12"
license = {text = "MIT"}
dependencies = [
    "Pillow>=11.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0",   # optional .env loader for OUTPUT_DIR etc.
]

[project.scripts]
sangpye = "sangpye_skill.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Notably absent: `openai`, `fastapi`, `celery`, `redis`, `uvicorn`, `httpx`, `python-multipart`. All transport/server deps are gone. Only Pillow (composition/slicing) and pydantic (schemas) remain from the production stack.

## 6. Vendoring Map (existing → new)

| Existing path (`make-detailed-product-page/`) | New path (`codex-sangpye-skill/sangpye_skill/`) | Action | Notes |
|---|---|---|---|
| `app/services/openai_client.py` | `codex_client.py` | **REWRITE** | OpenAI SDK `OpenAI(api_key=...)` factory → `CodexClient()` subprocess wrapper. No API key param. |
| `app/services/pipeline.py` | `pipeline.py` | **PORT** | Drop `cancel_check`/`status_callback`/`progress_callback` params; keep `progress_callback` as stderr print. Replace `get_openai_client(api_key)` with `CodexClient()`. |
| `app/services/analysis.py` | `analysis.py` | **PORT** | Replace `self.client.responses.create(...)` call with `self.client.call_responses(...)`. Prompt templates, schemas, `AnalysisPlan` all unchanged. |
| `app/services/image_generator_v3.py` | `image_generator.py` | **PORT** | Replace `self.client.images.edit(model=, image=, prompt=, size=, quality=, n=1)` with `self.client.generate_image_with_reference(model=, reference_image=, prompt=, size=, quality=)`. Keep `MAX_CONCURRENCY=3`, `MAX_RETRIES=5`, backoff table. |
| `app/services/bundle_slicer.py` | `bundle_slicer.py` | **COPY** | Pillow only. No changes. |
| `app/services/composer.py` | `composer.py` | **COPY** | Pillow only. No changes. |
| `app/services/product_dna.py` | `product_dna.py` | **COPY** | Pydantic schemas only. No changes. |
| `app/services/section_language.py` | `section_language.py` | **COPY** | Python dict constant. No changes. |
| `app/services/category_briefs.py` | `category_briefs.py` | **COPY** | Python dict constant + `get_brief()`. No changes. |
| `app/config.py` | embedded into `cli.py` | **ABSORB** | Keep `IMAGE_SIZE=1080`, `SECTION_COUNT=13`, `MAX_UPLOAD_IMAGES=14`. Drop `REDIS_URL`, `HOST`, `PORT`, `JOB_TTL_SECONDS`. `OUTPUT_DIR` becomes `--output` CLI flag. |
| `app/main.py`, `app/api/`, `app/tasks.py`, `app/worker.py`, `app/models/` | — | **DROP** | FastAPI/Celery/Redis infrastructure not needed for sync CLI. |
| `Dockerfile`, `docker-compose.yml` | — | **DROP** | |
| `requirements.txt` | `pyproject.toml` | **REPLACE** | Dep set reduced (see §5.3). |
| `web/`, `output/`, `spike/` (non-codex), `tests/` (FastAPI) | — | **DROP** | New repo gets its own `tests/`. |

## 7. `codex_client.py` — interface

```python
from __future__ import annotations
import base64, json, subprocess
from pathlib import Path

class CodexAuthError(RuntimeError): ...
class CodexCallError(RuntimeError): ...

class CodexClient:
    """Subprocess wrapper around `codex responses`. Uses the user's OAuth session."""

    def __init__(self, codex_bin: str = "codex", timeout_sec: int = 600):
        self.codex_bin = codex_bin
        self.timeout_sec = timeout_sec
        self._verify_login()

    # -- public ------------------------------------------------------------

    def call_responses(
        self,
        *,
        model: str,
        input: list[dict],
        response_format: dict | None = None,
        instructions: str | None = None,
    ) -> str:
        """Text/structured call. Returns aggregated `output_text`."""
        payload: dict = {"model": model, "input": input, "stream": True}
        if response_format:
            payload["text"] = {"format": response_format}
        if instructions:
            payload["instructions"] = instructions
        return self._run_and_extract_text(payload)

    def generate_image_with_reference(
        self,
        *,
        model: str,
        reference_image: Path,
        prompt: str,
        size: tuple[int, int],
        quality: str = "high",
    ) -> bytes:
        """Image-to-image. Returns PNG bytes."""
        b64 = base64.b64encode(reference_image.read_bytes()).decode()
        payload = {
            "model": model,
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"},
                    {"type": "input_text", "text": prompt},
                ],
            }],
            "tools": [{"type": "image_generation", "size": f"{size[0]}x{size[1]}", "quality": quality}],
            "tool_choice": {"type": "image_generation"},
            "stream": True,
        }
        return self._run_and_extract_image(payload)

    # -- private -----------------------------------------------------------

    def _verify_login(self) -> None:
        result = subprocess.run([self.codex_bin, "login", "status"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise CodexAuthError(
                f"`codex login status` failed (exit={result.returncode}). "
                f"Run `codex login` first. stderr={result.stderr.strip()}"
            )

    def _run_and_extract_text(self, payload: dict) -> str: ...   # JSONL parse, concat output_text deltas
    def _run_and_extract_image(self, payload: dict) -> bytes: ... # JSONL parse, decode image_generation_call.result
```

## 8. CLI contract (`cli.py`)

Invocation:
```bash
sangpye \
  --image photo1.jpg --image photo2.jpg \
  --prompt "무선 이어폰, ANC 탑재, 30시간 배터리, IPX5 방수" \
  --category electronics \
  --output ./out \
  --quality high
```

Flags:
- `--image PATH` — repeatable, 1–14 paths required
- `--prompt TEXT` — required
- `--category {electronics,fashion,food,beauty,home,general}` — default `general`
- `--output DIR` — default `./sangpye-output`
- `--quality {standard,high}` — default `high`
- `--job-id ID` — default: 8-char random hex
- `--codex-bin PATH` — default `codex`
- `--version` / `--help`

stdout (success, single JSON line):
```json
{"job_id":"a1b2c3d4","output_dir":"./out/a1b2c3d4","combined":"./out/a1b2c3d4/combined.png","sections":["./out/a1b2c3d4/sections/01_hero.png","..."],"plan_path":"./out/a1b2c3d4/analysis.json","elapsed_sec":252.4}
```

stderr (human progress log, not machine-parsed):
```
[1/6] codex login status: OK
[2/6] Analyzing product (gpt-5.4, 2 images)...
[3/6] Bundle plan: 5 bundles, master_image_index=0
[4/6] Generating 5 bundles (concurrency=3)...
       B1_HERO     ✓ 47s
       B2_OPENING  ✓ 52s
       B3_SOLUTION ✓ 68s
       B4_TRUST    ✓ 41s
       B5_ACTION   ✓ 39s
[5/6] Slicing 13 sections
[6/6] Composing combined.png (1080×7500)
Done. Total: 4m 12s.
```

Exit codes:
- `0` — success
- `1` — codex auth error (`CodexAuthError`)
- `2` — input/argument error
- `3` — API / generation error (`CodexCallError` or pipeline raise)
- `4` — filesystem error (e.g. output dir unwritable)

## 9. `SKILL.md`

```yaml
---
name: codex-sangpye
description: Generate a 13-section Korean e-commerce product detail page (1080×7500 combined image + 13 individual section PNGs) from product photos + a brief, using Codex OAuth (no OpenAI API key required).
version: 0.1.0
author: <user>
license: MIT
metadata:
  hermes:
    tags: [codex, image-generation, oauth, ecommerce, korean, detail-page]
    related_skills: [codex-image-generation]
---
```

Body sections (mirroring `codex-image-generation-skill/SKILL.md` structure):

1. **When to use** — when the user wants a Korean e-commerce product detail page image set from product photos.
2. **Preconditions** — `codex >= rust-v0.122.0` on PATH (first stable cut with the `responses` subcommand + modern auth wiring), `codex login status` reports OAuth, `sangpye --version` OK, and `CODEX_API_KEY` is **unset** (if set, it overrides OAuth and may unlock different models / billing). If any fail, tell the user how to fix and stop.
3. **Command path** — `sangpye` (installed globally via `uv tool install`).
4. **Parameters** — flag table mirroring §8.
5. **Basic usage** — minimal one-liner.
6. **Example with explicit options** — full multi-image invocation with all flags.
7. **Expected result** — the success JSON, the `combined.png` path to show the user, the 13 section paths.
8. **Troubleshooting** — 4 failure modes: auth (run `codex login`, pick OAuth option — note `OPENAI_API_KEY` env var is **ignored** at runtime by `codex responses`; only `CODEX_API_KEY` overrides OAuth), model unavailable (ChatGPT subscription tier may not expose `gpt-5.4` or `gpt-image-2`), rate-limit (lower `--quality`, wait, watch for `response.rate_limits` events), stale codex (upgrade to `>= rust-v0.122.0`).
9. **Agent rule** — "After successful generation, always show the user the absolute path to `combined.png` and the `job_id`. Do not regenerate on transient errors — surface them to the user."

## 10. Testing plan

### Unit tests (offline, fast, default)

- `tests/test_codex_client.py`
  - Mock `subprocess.run` return value with canned JSONL streams.
  - Verify `_run_and_extract_text` aggregates `output_text` deltas correctly.
  - Verify `_run_and_extract_image` extracts the first `image_generation_call.result` base64 and decodes to bytes.
  - Verify `_verify_login` raises `CodexAuthError` on non-zero exit.
  - Verify payload shape for `call_responses` (system/user roles, `text.format`, `stream:True`).
  - Verify payload shape for `generate_image_with_reference` (input_image content part, tools, tool_choice).

### Integration test (live, opt-in)

- `tests/test_pipeline_live.py`, marked `@pytest.mark.live`, skipped unless `pytest -m live`.
  - End-to-end: `PipelineService().run(images=[examples/sample_product.jpg], prompt="테스트", category="electronics", ...)` → asserts 13 section PNGs + `combined.png` of correct dimensions exist.
  - Cost: counts against ChatGPT subscription quota (one full pipeline run). Not in CI by default — explicitly opt-in to avoid incidental quota burn.

### CLI smoke test (manual, post-install)

```bash
uv tool install -e .
sangpye --image examples/sample_product.jpg --prompt "데모" --output /tmp/sangpye-smoke
# Assert exit 0 and /tmp/sangpye-smoke/*/combined.png exists at 1080×7500.
```

## 11. Rollout steps

1. **Phase 0** — Run spike in `make-detailed-product-page/spike/codex_oauth/`. GO only if all 3 pass.
2. **Scaffold** — `git init` new repo, add `pyproject.toml`, `LICENSE`, `.gitignore`, empty package.
3. **Copy pure modules** — `bundle_slicer`, `composer`, `product_dna`, `section_language`, `category_briefs`. Run `python -c "from sangpye_skill import ..."` import smoke.
4. **Implement `codex_client.py`** — with unit tests. Verify against spike's proven payloads.
5. **Port `analysis.py`** — swap single call site. Run a live 1-image analysis test.
6. **Port `image_generator.py`** — swap single call site. Run a live 1-bundle image test.
7. **Port `pipeline.py`** — wire everything. Run the live integration test (1 full pass).
8. **Implement `cli.py`** — argparse + stderr progress + stdout JSON. CLI smoke test.
9. **Write `SKILL.md`** — copy structure from reference skill, adapt.
10. **Write `README.md`** — install (`uv tool install git+...`), prereqs (`codex login`), usage, troubleshooting, a demo image.
11. **Publish GitHub repo** — public, `uv tool install git+https://github.com/<user>/codex-sangpye-skill` validated from a clean venv.
12. **Wire into Claude Code / Codex / Hermes** — drop `SKILL.md` into the appropriate skills directory on the user's machine, confirm discovery.

## 12. Risks & mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| `codex responses` doesn't support `text.format = json_object` | Medium | Fatal (NO-GO) | Spike 01 catches this. Fallback: use instructions-based JSON extraction with more forgiving parser, but only if project continues. |
| `image_generation` tool doesn't produce 1088×1600 (custom size) | Medium | Fatal or major rework | Spike 02 tests exact bundle size. If only standard sizes supported, rework bundle dimensions or abandon. |
| Reference image ignored by `image_generation` tool (text-only generation) | Medium | Major — loses image-to-image fidelity | Spike 02 visual check. If reference is ignored, evaluate text-only pipeline quality; user decides whether to ship or abandon. |
| ChatGPT subscription rate-limits 3 concurrent image calls | Medium | Annoying but recoverable | Spike 03 measures. Mitigation: reduce `MAX_CONCURRENCY` to 1-2, accept longer wall time. |
| `codex` CLI JSONL event schema changes | Low | Fixable | Pin minimum `codex` version (`rust-v0.122.0`) in SKILL.md preconditions. Integration test catches drift. Terminator is `response.completed`, not `response.output_text.done` (verified against source). |
| `CODEX_API_KEY` accidentally set in shell | Low | Silent mode-switch | `_verify_login` logs whether OAuth or API-key mode is active; surface in stderr at start of run. |
| OAuth session expires mid-pipeline (5+ min run) | Low | Recoverable | `CodexClient._verify_login` at init. If mid-call expires, surface the error clearly with re-login instructions. |
| `uv tool install git+...` doesn't pick up `[project.scripts]` entry | Low | Install-UX bug | Tested in rollout step 11 before public announcement. Fallback to `uv run --project ...`. |

## 13. Open questions (defer to implementation)

- Minimum `codex` CLI version — **resolved**: `rust-v0.122.0` (per openai/codex source inspection — first release with the `responses` subcommand on stable auth wiring).
- Whether to pin `gpt-5.4` and `gpt-image-2` model IDs in the skill or read from env (default: pinned, env override allowed).
- Whether `--quality` should map differently under OAuth vs API-key tiers (default: same mapping).
- How to visibly report progress through the SKILL invocation boundary (stderr is invisible to the invoking agent unless the harness streams it — may need structured stderr events).

## 14. Ownership & next action

- Design owner / author: genie
- Next action: **Phase 0 spike**. Will be covered by the writing-plans skill in the next step.

## 14.1 Phase 0 spike results (2026-04-23) — GO

All three spikes passed against `codex-cli 0.123.0`. See `codex-sangpye-skill/spike/codex_oauth/README.md` for details. The project is renamed to `codex-sangpye-skill` (상폐 = 상세페이지 Korean e-commerce slang).

**New payload-shape constraints discovered during spike execution** (NOT in the original §4 payloads — honour in `codex_client.py`):

1. **`instructions` required at top level.** A `role:"system"` message in `input` returns `400 {"detail":"Instructions are required"}`. System prompt must move to the top-level `instructions` field.
2. **`store: false` required.** Server defaults to true and rejects: `400 {"detail":"Store must be set to false"}`.
3. **`text.format = json_object` requires the literal word `json` in the user message.** OpenAI-level constraint — returns `400 "must contain the word 'json'"` otherwise.
4. **`model: "gpt-image-2"` is rejected under ChatGPT OAuth.** The Images Edit endpoint does not exist in this path. Error: `"The 'gpt-image-2' model is not supported when using Codex with a ChatGPT account."`
5. **Workaround — orchestrator model + tool call.** Use `model: "gpt-5.4"` + `tools:[{type:"image_generation",...}]` + `tool_choice:{type:"image_generation"}`. The chat model invokes the image tool. This IS allowed and returns the same `response.output_item.done` / `image_generation_call.result` shape. Custom sizes (1088×1600) pass through.
6. **Concurrency**: 3 parallel OAuth calls complete in ~100 s wall (soft-serializes to ~2 effective streams, each call sees ~2 informational `response.rate_limits` events). Not fatal. `MAX_CONCURRENCY = 3` is defensible; could drop to 2 without meaningful UX cost.

### Updated call-shape table (supersedes §4 sample payloads)

| Production backend call | OAuth-compatible `codex responses` payload |
|---|---|
| `client.responses.create(model="gpt-5.4", input=[{role:"system",…}, {role:"user", content:[image,text]}], text={"format":{"type":"json_object"}})` | `{model:"gpt-5.4", instructions:<system>, input:[{role:"user", content:[input_image, input_text}]}], text:{format:{type:"json_object"}}, stream:true, store:false}` — user text **must mention "json"** |
| `client.images.edit(model="gpt-image-2", image=ref, prompt=p, size=(1088,1600), quality="high", n=1)` | `{model:"gpt-5.4", instructions:<art-director-system>, input:[{role:"user", content:[input_image(ref), input_text(p)]}], tools:[{type:"image_generation", size:"1088x1600", quality:"high"}], tool_choice:{type:"image_generation"}, stream:true, store:false}` |

**Implication for `image_generator.py`**: the port is NOT a drop-in replacement of `client.images.edit(...)` with a same-shaped codex call. It is a **tool-call-via-chat-model** pattern. `codex_client.generate_image_with_reference()` now wraps the orchestrator+tool shape internally so `image_generator.py`'s retry/concurrency logic stays intact.

## 15. Future work — low-latency transport (post-v0.1)

For reference: `NomaDamas/god-tibo-imagen` demonstrates a faster transport pattern — read the bearer token + account id directly from `~/.codex/auth.json` and POST to the private endpoint `https://chatgpt.com/backend-api/codex/responses`. This eliminates the per-call subprocess spawn (~500ms × 5 bundles ≈ 2.5s saved) and enables native in-process concurrency + real-time SSE progress events.

**Not adopted in v0.1** because:
- Private endpoint is explicitly undocumented ("may change" per god-tibo's own README).
- Open-source skill users hit harder-to-diagnose breakage if OpenAI rotates the private endpoint.
- For a 5-minute pipeline, 2.5s overhead is negligible UX.

**Mitigation for future adoption**: `codex_client.py` isolates all transport behind the `CodexClient` class. A v0.2 feature flag (`--transport private-http|subprocess`, default `subprocess`) could add the private-HTTP backend as an alternative without touching `pipeline.py`, `analysis.py`, or `image_generator.py`.
