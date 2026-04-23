# codex-sangpye-skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

---

## ⚡ Current Status (2026-04-23) — START HERE

The plan was originally written for a fresh-start scenario. Some early phases have already been executed manually before subagent dispatch began. **Read this section before picking up any task.**

### ✅ Already done (do NOT redo)

- **Phase 0 — OAuth verification spike: GO** (commit `2f6c0d6` in this repo). All 3 spikes passed against `codex-cli 0.123.0`. Findings folded into spec §14.1 and the `codex_client.py` task descriptions below. See `spike/codex_oauth/README.md` for the verdict and the 5 OAuth-only payload constraints we discovered.
- **Phase 1 — repo scaffolding** (commits `f10fd8b`, `d1eeef0`). Already present: `.gitignore`, `LICENSE`, `.python-version`, `pyproject.toml` (with console script `sangpye = "sangpye_skill.cli:main"`), `sangpye_skill/__init__.py` (with `__version__ = "0.1.0"`), `README.md`, empty `tests/`, `scripts/`, `examples/` directories. `uv sync --extra dev` already ran successfully — `.venv/` is set up.

### ▶️ Pick up at Task 2.1

The next executable task is **Task 2.1 — Create `constants.py`** in Phase 2.

### 🔄 Path adjustments for already-done phases

When a task's "Files: Create:" path references something that already exists from Phase 1 (e.g. `pyproject.toml`, `__init__.py`, `LICENSE`), the file is already present and may differ in cosmetic details from the snippet in the plan. Verify it matches the plan's intent; only edit if a substantive divergence would block downstream tasks. Do not overwrite a working file just to match snippet wording.

### 🧠 Spec §14.1 — Required reading before any code touches `codex_client.py`

The Phase 0 spike surfaced 5 OAuth-only constraints that diverge from the spec's initial §4 hypothesis. The plan's Task 3.4 / 3.5 / 4.1 / 5.1 already incorporate them. If you find the implementation snippets confusing, read `docs/spec.md` §14.1 for the corrected call-shape table and the rationale.

### 🗂 Plan ↔ implementation environment

- This plan now lives at `docs/plan.md` inside the new repo (`NEW_REPO`). The original copy in `make-detailed-product-page/docs/superpowers/plans/` remains as historical reference.
- All `EXISTING_REPO` paths point to the source backend (read-only — used only to copy files from for vendoring).
- All `NEW_REPO` paths point to **this repo**.

---

**Goal:** Extract the v3 product-detail-page pipeline into a separate open-source repo (`codex-sangpye-skill`) installable via `uv tool install`, that runs synchronously on the user's machine and authenticates exclusively through the user's Codex OAuth session — replacing FastAPI + Celery + Redis + OpenAI SDK with a single `sangpye` console command.

**Architecture:** A Phase 0 spike inside the existing repo verifies that `codex responses` can carry both the multimodal-JSON analysis call and the image-with-reference generation call our pipeline needs. If GO, scaffold a brand-new repo, vendor the pure Pillow/Pydantic modules as-is, replace `app/services/openai_client.py` with a `codex_client.py` subprocess wrapper, port the three call-site modules (`analysis.py`, `image_generator_v3.py`, `pipeline.py`) so they call the new client, wrap the pipeline in an argparse CLI that prints a single JSON line on stdout, and ship a `SKILL.md` mirroring the reference `codex-image-generation-skill` structure.

**Tech Stack:** Python 3.12 · Pillow 11 · Pydantic 2 · `uv` (build + tool install) · `pytest` · `codex` CLI (OAuth) · subprocess + JSONL parsing.

**Spec:** `docs/superpowers/specs/2026-04-23-codex-sangpye-skill-design.md`

**Path conventions:**
- `EXISTING_REPO` = `/Users/genie/dev/side/make-detailed-product-page`
- `NEW_REPO` = `/Users/genie/dev/side/codex-sangpye-skill`
- `REF_REPO` = https://github.com/Gyu-bot/codex-image-generation-skill (read-only reference)

---

## File Structure (target — `NEW_REPO/`)

```
codex-sangpye-skill/
├── SKILL.md                           # Hermes/Claude skill manifest
├── README.md                          # Public install + usage
├── LICENSE                            # MIT
├── pyproject.toml                     # uv-compatible, console-script `sangpye`
├── .python-version                    # "3.12"
├── .gitignore
├── sangpye_skill/
│   ├── __init__.py                    # __version__ = "0.1.0"
│   ├── cli.py                         # argparse entry → main()
│   ├── codex_client.py                # NEW — subprocess wrapper
│   ├── constants.py                   # NEW — IMAGE_SIZE, SECTION_COUNT, MAX_UPLOAD_IMAGES
│   ├── pipeline.py                    # ported from app/services/pipeline.py
│   ├── analysis.py                    # ported from app/services/analysis.py
│   ├── image_generator.py             # ported from app/services/image_generator_v3.py
│   ├── bundle_slicer.py               # vendored from app/services/bundle_slicer.py
│   ├── composer.py                    # vendored from app/services/composer.py
│   ├── product_dna.py                 # vendored from app/services/product_dna.py
│   ├── section_language.py            # vendored from app/services/section_language.py
│   └── category_briefs.py             # vendored from app/services/category_briefs.py
├── scripts/
│   └── generate.py                    # thin fallback wrapper
├── tests/
│   ├── __init__.py
│   ├── test_codex_client.py           # subprocess-mocked unit tests
│   └── test_pipeline_live.py          # @pytest.mark.live, opt-in
└── examples/
    └── sample_product.jpg             # demo image
```

The Phase 0 spike lives in `EXISTING_REPO/spike/codex_oauth/` — throwaway, validates the OAuth path before any work in `NEW_REPO`.

---

## Phase 0 — OAuth Verification Spike (GO/NO-GO gate)

**ALL tasks in Phase 0 run inside `EXISTING_REPO`. Do not create `NEW_REPO` until Phase 0 is GO.**

### Task 0.1: Scaffold spike directory + sample input

**Files:**
- Create: `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/README.md`
- Create: `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/sample_inputs/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/sample_inputs
touch /Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/sample_inputs/.gitkeep
```

- [ ] **Step 2: Write the spike README skeleton**

Write to `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/README.md`:

```markdown
# Codex OAuth verification spike

Goal: prove that `codex responses` (OAuth) can carry the two call types our pipeline needs:
1. Multimodal text → structured JSON (gpt-5.4 + image input + json_object format)
2. Image-to-image generation with a reference master image (gpt-image-2, custom 1088×1600)
3. 3 of #2 in parallel without hitting OAuth rate limits

If any of the three FAIL, the codex-sangpye-skill project is abandoned.

## Prereqs

- `codex` CLI on PATH
- `codex login status` returns OK (OAuth, not API key)
- A sample product image at `sample_inputs/earbuds_01.jpg`

## Scripts

- `01_text_analysis.py` — runs Spike 1
- `02_image_with_ref.py` — runs Spike 2
- `03_parallel_3.py` — runs Spike 3

## Results

- [ ] Spike 1: ___
- [ ] Spike 2: ___
- [ ] Spike 3: ___

**GO/NO-GO verdict:** ___
```

- [ ] **Step 3: Drop in a sample product image**

Find any reasonable product photo (1024×1024 or larger, JPEG, ~200KB-2MB). Use one of the existing test images if available, otherwise a generic free product photo.

```bash
# If you have an existing test image in the repo:
ls /Users/genie/dev/side/make-detailed-product-page/tests/
# or under output/ from past runs:
ls /Users/genie/dev/side/make-detailed-product-page/output/jobs/ 2>/dev/null | head -3
# Copy one to sample_inputs/earbuds_01.jpg
```

If none exist, manually drop a product photo into `sample_inputs/earbuds_01.jpg`.

Run: `ls -la /Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/sample_inputs/`
Expected: shows `earbuds_01.jpg` with non-zero size.

- [ ] **Step 4: Verify codex CLI is ready**

Run:
```bash
which codex && codex --version && codex login status
echo "CODEX_API_KEY=${CODEX_API_KEY:-<unset>}"
```
Expected:
- Path is printed, version is **>= `rust-v0.122.0`** (the `responses` subcommand was stabilized here — verified against openai/codex source).
- `codex login status` reports OAuth (ChatGPT) session active.
- `CODEX_API_KEY=<unset>` — if a value is printed, `unset CODEX_API_KEY` before running the spike (it overrides OAuth at runtime).

If `codex login status` shows API-key mode, run `codex logout && codex login` and pick the OAuth/ChatGPT option. If version is below `rust-v0.122.0`, upgrade codex per https://github.com/openai/codex. (`OPENAI_API_KEY` in shell is **ignored** at runtime by `codex responses` — no need to unset.)

- [ ] **Step 5: Commit the scaffold**

```bash
cd /Users/genie/dev/side/make-detailed-product-page
git add spike/codex_oauth/
git commit -m "spike: scaffold codex OAuth verification (Phase 0 of codex-sangpye-skill)"
```

---

### Task 0.2: Spike 01 — multimodal text → JSON

**Files:**
- Create: `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/01_text_analysis.py`

- [ ] **Step 1: Write the spike script**

```python
"""Spike 01 — verify codex responses can carry multimodal text input
and return a JSON-formatted response (json_object format) for gpt-5.4."""
from __future__ import annotations
import base64
import json
import subprocess
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).parent
SAMPLE = SPIKE_DIR / "sample_inputs" / "earbuds_01.jpg"


def main() -> int:
    if not SAMPLE.exists():
        print(f"FAIL: sample missing at {SAMPLE}", file=sys.stderr)
        return 2

    b64 = base64.b64encode(SAMPLE.read_bytes()).decode()
    payload = {
        "model": "gpt-5.4",
        "input": [
            {
                "role": "system",
                "content": "Return ONLY a single JSON object with keys: name (string), category (string), usp (string), key_features (list of strings). No prose, no markdown.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                    {"type": "input_text", "text": "이 제품을 한국 이커머스용으로 분석해서 위 4개 키만 채워줘."},
                ],
            },
        ],
        "text": {"format": {"type": "json_object"}},
        "stream": True,
    }

    print(f"[spike 01] sending payload (model={payload['model']}, image={SAMPLE.name})", file=sys.stderr)
    proc = subprocess.run(
        ["codex", "responses"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        print(f"FAIL: codex exit={proc.returncode}\nSTDERR:\n{proc.stderr}", file=sys.stderr)
        return 3

    # Accumulate output_text.delta events until response.completed (terminator).
    # NOTE: codex CLI does NOT emit response.output_text.done — verified against
    # openai/codex source (codex-api/src/common.rs ResponseEvent enum).
    deltas: list[str] = []
    completed = False
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = event.get("type", "")
        if etype == "response.output_text.delta":
            deltas.append(event.get("delta", ""))
        elif etype == "response.completed":
            completed = True
            break

    if not completed:
        print("FAIL: stream ended without response.completed", file=sys.stderr)
        print(f"raw stdout (truncated):\n{proc.stdout[:2000]}", file=sys.stderr)
        return 6

    text = "".join(deltas)
    print(f"[spike 01] raw output ({len(text)} chars):", file=sys.stderr)
    print(text, file=sys.stderr)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"FAIL: output is not valid JSON: {e}", file=sys.stderr)
        return 4
    required = {"name", "category", "usp", "key_features"}
    missing = required - set(obj.keys())
    if missing:
        print(f"FAIL: missing keys: {missing}", file=sys.stderr)
        return 5
    print("PASS: spike 01 — JSON returned with all 4 required keys", file=sys.stderr)
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the spike**

```bash
cd /Users/genie/dev/side/make-detailed-product-page
python spike/codex_oauth/01_text_analysis.py
```

Expected: PASS message on stderr + a JSON object on stdout. Exit code 0.

- [ ] **Step 3: Record result in spike README**

Edit `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/README.md` and update the `Spike 1:` line with PASS/FAIL + a one-line note (latency, model echo, anything notable).

- [ ] **Step 4: Decision gate**

If FAIL: stop here. Update the README with the verdict `NO-GO — abandoning project. Reason: <error>`. Commit the spike README. Do not proceed.

If PASS: commit and continue.

```bash
git add spike/codex_oauth/01_text_analysis.py spike/codex_oauth/README.md
git commit -m "spike: 01 text+JSON via codex responses — PASS"
```

---

### Task 0.3: Spike 02 — image-to-image with reference (1088×1600)

**Files:**
- Create: `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/02_image_with_ref.py`

- [ ] **Step 1: Write the spike script**

```python
"""Spike 02 — verify codex responses can carry an image-generation tool call
with a reference image and a custom 1088×1600 size."""
from __future__ import annotations
import base64
import json
import subprocess
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).parent
SAMPLE = SPIKE_DIR / "sample_inputs" / "earbuds_01.jpg"
OUT = SPIKE_DIR / "spike02_hero.png"


def main() -> int:
    if not SAMPLE.exists():
        print(f"FAIL: sample missing at {SAMPLE}", file=sys.stderr)
        return 2

    b64 = base64.b64encode(SAMPLE.read_bytes()).decode()
    prompt = (
        "Cinematic vertical product hero, 1088x1600. "
        "Reference the uploaded product. Dark techwear lighting, dramatic rim light, "
        "Korean headline overlay top-center reading: '지금, 무선의 한계를 넘다'. "
        "Sub-line: '30시간 배터리 · IPX5 방수 · 액티브 노이즈 캔슬링'. "
        "Render the Korean text crisply. Premium e-commerce composition."
    )
    payload = {
        "model": "gpt-image-2",
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                {"type": "input_text", "text": prompt},
            ],
        }],
        "tools": [{"type": "image_generation", "size": "1088x1600", "quality": "high"}],
        "tool_choice": {"type": "image_generation"},
        "stream": True,
    }

    print(f"[spike 02] generating 1088x1600 hero from {SAMPLE.name}...", file=sys.stderr)
    proc = subprocess.run(
        ["codex", "responses"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        print(f"FAIL: codex exit={proc.returncode}\nSTDERR:\n{proc.stderr}", file=sys.stderr)
        return 3

    image_b64: str | None = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "response.output_item.done":
            item = event.get("item", {})
            if item.get("type") == "image_generation_call":
                image_b64 = item.get("result")
                break

    if not image_b64:
        print("FAIL: no image_generation_call.result observed", file=sys.stderr)
        print(f"raw stdout (truncated):\n{proc.stdout[:2000]}", file=sys.stderr)
        return 4

    OUT.write_bytes(base64.b64decode(image_b64))

    # Verify dimensions
    from PIL import Image
    with Image.open(OUT) as im:
        w, h = im.size
    if (w, h) != (1088, 1600):
        print(f"FAIL: image is {w}x{h}, expected 1088x1600", file=sys.stderr)
        return 5

    print(f"PASS: spike 02 — 1088x1600 PNG saved to {OUT}", file=sys.stderr)
    print(str(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Install Pillow if missing (needed for size check)**

```bash
cd /Users/genie/dev/side/make-detailed-product-page
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
pip install Pillow
```

- [ ] **Step 3: Run the spike**

```bash
python spike/codex_oauth/02_image_with_ref.py
```

Expected: PASS message, output `spike02_hero.png` written, exit 0.

- [ ] **Step 4: Visual sanity check**

```bash
open /Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/spike02_hero.png
```

Manually verify:
1. Image is 1088×1600.
2. The product from `sample_inputs/earbuds_01.jpg` is recognizable (silhouette, color, form).
3. Korean text is rendered legibly.
4. Quality is acceptable for e-commerce.

If the reference is *ignored* (totally unrelated product) or text is garbled beyond recognition, that's a soft FAIL — note it in the README, escalate to user before proceeding.

- [ ] **Step 5: Record result + commit**

Update `spike/codex_oauth/README.md` Spike 2 line with PASS/FAIL + visual notes.

```bash
git add spike/codex_oauth/02_image_with_ref.py spike/codex_oauth/spike02_hero.png spike/codex_oauth/README.md
git commit -m "spike: 02 image-with-reference via codex responses — PASS"
```

---

### Task 0.4: Spike 03 — concurrency (3 parallel image calls)

**Files:**
- Create: `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/03_parallel_3.py`

- [ ] **Step 1: Write the spike script**

```python
"""Spike 03 — verify 3 concurrent codex responses image calls don't get throttled."""
from __future__ import annotations
import asyncio
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

SPIKE_DIR = Path(__file__).parent
SAMPLE = SPIKE_DIR / "sample_inputs" / "earbuds_01.jpg"


def build_payload(b64: str, label: str) -> dict:
    return {
        "model": "gpt-image-2",
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                {"type": "input_text", "text": f"Vertical product image, 1088x1600, {label} variation, premium look."},
            ],
        }],
        "tools": [{"type": "image_generation", "size": "1088x1600", "quality": "high"}],
        "tool_choice": {"type": "image_generation"},
        "stream": True,
    }


def run_one(payload: dict, idx: int) -> tuple[int, bool, float, str]:
    t0 = time.time()
    try:
        proc = subprocess.run(
            ["codex", "responses"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return idx, False, time.time() - t0, "timeout"
    elapsed = time.time() - t0
    if proc.returncode != 0:
        return idx, False, elapsed, f"exit {proc.returncode}: {proc.stderr[:200]}"
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "response.output_item.done":
            item = ev.get("item", {})
            if item.get("type") == "image_generation_call" and item.get("result"):
                return idx, True, elapsed, "ok"
    return idx, False, elapsed, "no image_generation_call.result"


async def main() -> int:
    if not SAMPLE.exists():
        print(f"FAIL: sample missing at {SAMPLE}", file=sys.stderr)
        return 2
    b64 = base64.b64encode(SAMPLE.read_bytes()).decode()
    payloads = [build_payload(b64, lbl) for lbl in ("hero", "lifestyle", "detail")]

    print("[spike 03] firing 3 parallel image calls...", file=sys.stderr)
    t0 = time.time()
    results = await asyncio.gather(*[
        asyncio.to_thread(run_one, p, i) for i, p in enumerate(payloads)
    ])
    total_elapsed = time.time() - t0

    failed = []
    for idx, ok, elapsed, note in sorted(results):
        flag = "OK" if ok else "FAIL"
        print(f"  [{idx}] {flag} ({elapsed:.1f}s) {note}", file=sys.stderr)
        if not ok:
            failed.append((idx, note))

    print(f"[spike 03] total wall: {total_elapsed:.1f}s", file=sys.stderr)
    if failed:
        print(f"FAIL: {len(failed)}/3 calls failed: {failed}", file=sys.stderr)
        return 3
    if total_elapsed > 180:
        print(f"WARN: total wall {total_elapsed:.1f}s > 180s — concurrency may be serialized", file=sys.stderr)
    print("PASS: spike 03 — 3 parallel calls completed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

- [ ] **Step 2: Run the spike**

```bash
cd /Users/genie/dev/side/make-detailed-product-page
python spike/codex_oauth/03_parallel_3.py
```

Expected: PASS, 3 OK lines, exit 0. Note total wall time — if >180s, OAuth is likely serializing requests (still PASS-with-warning, but adjust `MAX_CONCURRENCY` accordingly later).

- [ ] **Step 3: Record + commit**

Update `spike/codex_oauth/README.md` Spike 3 line with PASS/FAIL + observed wall time.

```bash
git add spike/codex_oauth/03_parallel_3.py spike/codex_oauth/README.md
git commit -m "spike: 03 parallel x3 via codex responses — PASS"
```

---

### Task 0.5: GO/NO-GO decision

- [ ] **Step 1: Update README with verdict**

Edit `/Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/README.md` and replace `**GO/NO-GO verdict:** ___` with one of:

- `**GO** — all 3 spikes PASS. Proceed to Phase 1.`
- `**NO-GO** — <which spike(s) failed and why>. Project abandoned per spec §4.`

- [ ] **Step 2: Commit verdict**

```bash
cd /Users/genie/dev/side/make-detailed-product-page
git add spike/codex_oauth/README.md
git commit -m "spike: GO|NO-GO verdict — <fill in>"
```

- [ ] **Step 3: Halt if NO-GO**

If NO-GO, do not proceed to Phase 1. Report findings to the user and stop. Otherwise continue.

---

## Phase 1 — New repo scaffolding

**ALL tasks from Phase 1 onward operate inside `NEW_REPO` = `/Users/genie/dev/side/codex-sangpye-skill/`.**

### Task 1.1: Create the new repo

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/.gitignore`
- Create: `/Users/genie/dev/side/codex-sangpye-skill/LICENSE`
- Create: `/Users/genie/dev/side/codex-sangpye-skill/.python-version`

- [ ] **Step 1: Create the directory and init git**

```bash
mkdir -p /Users/genie/dev/side/codex-sangpye-skill
cd /Users/genie/dev/side/codex-sangpye-skill
git init -b main
```

Expected: `Initialized empty Git repository in /Users/genie/dev/side/codex-sangpye-skill/.git/`

- [ ] **Step 2: Write `.gitignore`**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/.gitignore <<'EOF'
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.uv/
dist/
build/
.pytest_cache/
.ruff_cache/
.coverage
*.png
!examples/sample_product.jpg
!examples/*.png
.DS_Store
EOF
```

- [ ] **Step 3: Write the LICENSE (MIT)**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/LICENSE <<'EOF'
MIT License

Copyright (c) 2026 <YOUR NAME>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

Replace `<YOUR NAME>` with the actual author name when committing.

- [ ] **Step 4: Pin Python version**

```bash
echo "3.12" > /Users/genie/dev/side/codex-sangpye-skill/.python-version
```

- [ ] **Step 5: Verify scaffolding**

Run: `ls -la /Users/genie/dev/side/codex-sangpye-skill/`
Expected: shows `.git/`, `.gitignore`, `.python-version`, `LICENSE`.

---

### Task 1.2: `pyproject.toml` with deps + console script

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/pyproject.toml`

- [ ] **Step 1: Write `pyproject.toml`**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/pyproject.toml <<'EOF'
[project]
name = "codex-sangpye-skill"
version = "0.1.0"
description = "Generate Korean e-commerce product detail page images (13 sections, 1080x7500 combined) via Codex OAuth — no OpenAI API key required."
readme = "README.md"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [{name = "<YOUR NAME>"}]
keywords = ["codex", "image-generation", "ecommerce", "korean", "detail-page", "skill"]
dependencies = [
    "Pillow>=11.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
]

[project.scripts]
sangpye = "sangpye_skill.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["sangpye_skill"]

[tool.pytest.ini_options]
markers = [
    "live: hits real codex OAuth (skipped by default; opt in with `pytest -m live`)",
]
addopts = "-m 'not live'"
EOF
```

- [ ] **Step 2: Verify it parses**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
python -c "import tomllib; tomllib.loads(open('pyproject.toml').read()); print('OK')"
```
Expected: `OK`

---

### Task 1.3: Empty package skeleton

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/__init__.py`

- [ ] **Step 1: Create the package**

```bash
mkdir -p /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill
cat > /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/__init__.py <<'EOF'
"""codex-sangpye-skill — Korean e-commerce detail page generator via Codex OAuth."""
__version__ = "0.1.0"
EOF
```

- [ ] **Step 2: Smoke-import**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
python -c "import sangpye_skill; print(sangpye_skill.__version__)"
```
Expected: `0.1.0`

---

### Task 1.4: Verify `uv sync` works

- [ ] **Step 1: Run uv sync**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv sync --extra dev
```

Expected: `.venv/` created, Pillow + pydantic + python-dotenv + pytest installed, no errors. (If `uv` is not installed, run `brew install uv` first.)

- [ ] **Step 2: Verify the env**

```bash
uv run python -c "from PIL import Image; import pydantic; import sangpye_skill; print('imports OK')"
```
Expected: `imports OK`

---

### Task 1.5: Initial commit

- [ ] **Step 1: Commit scaffold**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
git add .
git commit -m "chore: scaffold codex-sangpye-skill (Python 3.12, uv, console-script sangpye)"
```

---

## Phase 2 — Vendor pure modules (Pillow / Pydantic only)

The following modules have no `app.*` runtime dependencies beyond `app.config.settings.IMAGE_SIZE`. We extract that single constant into `constants.py` so the vendored code can be a clean copy.

### Task 2.1: Create `constants.py`

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/constants.py`

- [ ] **Step 1: Write constants**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/constants.py <<'EOF'
"""Constants extracted from the original app/config.py.

Only the ones used by vendored Pillow/Pydantic modules are kept. Server/queue
constants (REDIS_URL, HOST, PORT, JOB_TTL_SECONDS) are intentionally dropped.
"""
IMAGE_SIZE = 1080
SECTION_COUNT = 13
MAX_UPLOAD_IMAGES = 14
EOF
```

- [ ] **Step 2: Smoke-import**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python -c "from sangpye_skill.constants import IMAGE_SIZE; print(IMAGE_SIZE)"
```
Expected: `1080`

---

### Task 2.2: Vendor `bundle_slicer.py` (no edits)

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/bundle_slicer.py`
  (from: `/Users/genie/dev/side/make-detailed-product-page/app/services/bundle_slicer.py`)

- [ ] **Step 1: Copy the file verbatim**

```bash
cp /Users/genie/dev/side/make-detailed-product-page/app/services/bundle_slicer.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/bundle_slicer.py
```

- [ ] **Step 2: Verify no `app.*` imports**

```bash
grep -E "from app\.|import app\." /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/bundle_slicer.py
```
Expected: no output (no matches).

If matches exist, edit the file and replace each `from app.<module> import X` with `from sangpye_skill.<module> import X`.

- [ ] **Step 3: Smoke-import**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python -c "from sangpye_skill.bundle_slicer import BundleSlicer, SectionSlice; print('OK')"
```
Expected: `OK`

---

### Task 2.3: Vendor `composer.py` (rewrite settings import)

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/composer.py`
  (from: `/Users/genie/dev/side/make-detailed-product-page/app/services/composer.py`)

- [ ] **Step 1: Copy the file**

```bash
cp /Users/genie/dev/side/make-detailed-product-page/app/services/composer.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/composer.py
```

- [ ] **Step 2: Replace the `app.config.settings` import**

Edit `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/composer.py`:

Replace:
```python
from app.config import settings
```
with:
```python
from sangpye_skill.constants import IMAGE_SIZE
```

Replace:
```python
WIDTH = settings.IMAGE_SIZE  # 1080
```
with:
```python
WIDTH = IMAGE_SIZE  # 1080
```

- [ ] **Step 3: Verify no `app.*` imports remain**

```bash
grep -E "from app\.|import app\." /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/composer.py
```
Expected: no output.

- [ ] **Step 4: Smoke-import + verify SECTIONS constant**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python -c "from sangpye_skill.composer import ComposerService, SECTIONS, WIDTH, TOTAL_HEIGHT; print(WIDTH, TOTAL_HEIGHT, len(SECTIONS))"
```
Expected: `1080 7500 13`

---

### Task 2.4: Vendor `product_dna.py`

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/product_dna.py`
  (from: `/Users/genie/dev/side/make-detailed-product-page/app/services/product_dna.py`)

- [ ] **Step 1: Copy + rewrite imports**

```bash
cp /Users/genie/dev/side/make-detailed-product-page/app/services/product_dna.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/product_dna.py
```

Then edit and replace any `from app.services.X import Y` with `from sangpye_skill.X import Y`. Verify with:

```bash
grep -E "from app\.|import app\." /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/product_dna.py
```
Expected: no output.

- [ ] **Step 2: Smoke-import**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python -c "from sangpye_skill.product_dna import ProductDNA, inject_dna_into_prompt; print('OK')"
```
Expected: `OK`

---

### Task 2.5: Vendor `section_language.py` and `category_briefs.py`

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/section_language.py`
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/category_briefs.py`

- [ ] **Step 1: Copy both**

```bash
cp /Users/genie/dev/side/make-detailed-product-page/app/services/section_language.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/section_language.py
cp /Users/genie/dev/side/make-detailed-product-page/app/services/category_briefs.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/category_briefs.py
```

- [ ] **Step 2: Rewrite any `app.*` imports**

```bash
grep -lE "from app\.|import app\." \
  /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/section_language.py \
  /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/category_briefs.py
```

For any matched file, replace `from app.X import Y` → `from sangpye_skill.X import Y`.

- [ ] **Step 3: Smoke-import**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python -c "from sangpye_skill.section_language import SECTION_LANGUAGES; from sangpye_skill.category_briefs import get_brief, CATEGORY_BRIEFS; print(len(SECTION_LANGUAGES), len(CATEGORY_BRIEFS), get_brief('general')[:40])"
```
Expected: integer counts + first 40 chars of the general brief.

---

### Task 2.6: Commit Phase 2

- [ ] **Step 1: Commit**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
git add sangpye_skill/
git commit -m "feat: vendor pure Pillow/Pydantic modules (slicer, composer, dna, language, briefs) + constants"
```

---

## Phase 3 — `codex_client.py` (TDD)

This is the only NEW module. Build it test-first using mocked `subprocess.run`.

### Task 3.1: `tests/__init__.py` and conftest

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/tests/__init__.py`
- Create: `/Users/genie/dev/side/codex-sangpye-skill/tests/conftest.py`

- [ ] **Step 1: Create empty `__init__.py`**

```bash
mkdir -p /Users/genie/dev/side/codex-sangpye-skill/tests
touch /Users/genie/dev/side/codex-sangpye-skill/tests/__init__.py
```

- [ ] **Step 2: Write conftest with shared fixtures**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/tests/conftest.py <<'EOF'
"""Shared pytest fixtures."""
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock
import pytest


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["codex", "responses"], returncode=returncode, stdout=stdout, stderr=stderr
    )


@pytest.fixture
def fake_login_ok(monkeypatch):
    """Make `codex login status` return success."""
    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(stdout="logged in via OAuth (ChatGPT)\n", returncode=0)
        raise RuntimeError(f"unexpected subprocess call: {cmd}")
    monkeypatch.setattr(subprocess, "run", fake_run)


@pytest.fixture
def fake_login_fail(monkeypatch):
    """Make `codex login status` return failure."""
    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(stderr="not logged in\n", returncode=1)
        raise RuntimeError(f"unexpected subprocess call: {cmd}")
    monkeypatch.setattr(subprocess, "run", fake_run)


def jsonl_text_stream(parts: list[str]) -> str:
    """Build a fake JSONL stream of output_text deltas terminated by response.completed.

    NOTE: The real codex CLI does NOT emit response.output_text.done. The terminator
    is response.completed; consumers must concatenate deltas themselves.
    """
    lines = [json.dumps({"type": "response.created"})]
    for p in parts:
        lines.append(json.dumps({"type": "response.output_text.delta", "delta": p}))
    lines.append(json.dumps({"type": "response.completed"}))
    return "\n".join(lines) + "\n"


def jsonl_image_stream(b64_result: str) -> str:
    """Build a fake JSONL stream containing one image_generation_call.done."""
    return "\n".join([
        json.dumps({"type": "response.created"}),
        json.dumps({
            "type": "response.output_item.done",
            "item": {"type": "image_generation_call", "result": b64_result},
        }),
        json.dumps({"type": "response.completed"}),
    ]) + "\n"
EOF
```

---

### Task 3.2: TDD `_verify_login` success path

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/tests/test_codex_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_codex_client.py
"""Unit tests for sangpye_skill.codex_client."""
from __future__ import annotations
import pytest
from sangpye_skill.codex_client import CodexClient, CodexAuthError


def test_verify_login_success(fake_login_ok):
    """Constructor returns successfully when codex login status exits 0."""
    client = CodexClient()
    assert isinstance(client, CodexClient)
```

- [ ] **Step 2: Run, expect ImportError**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run pytest tests/test_codex_client.py::test_verify_login_success -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'sangpye_skill.codex_client'`.

- [ ] **Step 3: Create skeleton `codex_client.py`**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/codex_client.py <<'EOF'
"""Subprocess wrapper around `codex responses`. Uses the user's OAuth session."""
from __future__ import annotations
import base64
import json
import subprocess
from pathlib import Path


class CodexAuthError(RuntimeError):
    """Raised when `codex login status` indicates the user is not authenticated."""


class CodexCallError(RuntimeError):
    """Raised when a `codex responses` call fails or returns an unexpected payload."""


class CodexClient:
    def __init__(self, codex_bin: str = "codex", timeout_sec: int = 600):
        self.codex_bin = codex_bin
        self.timeout_sec = timeout_sec
        self._verify_login()

    def _verify_login(self) -> None:
        result = subprocess.run(
            [self.codex_bin, "login", "status"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise CodexAuthError(
                f"`codex login status` failed (exit={result.returncode}). "
                f"Run `codex login` first. stderr={result.stderr.strip()}"
            )
EOF
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_codex_client.py::test_verify_login_success -v
```
Expected: PASS.

---

### Task 3.3: TDD `_verify_login` failure path

- [ ] **Step 1: Add the failing test**

Append to `tests/test_codex_client.py`:

```python
def test_verify_login_raises_on_failure(fake_login_fail):
    """Constructor raises CodexAuthError when codex login status exits non-zero."""
    with pytest.raises(CodexAuthError, match="codex login"):
        CodexClient()
```

- [ ] **Step 2: Run, expect PASS (already implemented)**

```bash
uv run pytest tests/test_codex_client.py::test_verify_login_raises_on_failure -v
```
Expected: PASS — the implementation from Task 3.2 already covers this.

---

### Task 3.4: TDD `call_responses` (text aggregation + payload shape)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_codex_client.py`:

```python
import json
import subprocess
from tests.conftest import jsonl_text_stream, _completed


def test_call_responses_aggregates_text(monkeypatch, fake_login_ok):
    """call_responses returns concatenated output_text AND builds a payload
    that honours all OAuth-only constraints discovered in Phase 0 spike:
    instructions top-level, store:false, stream:true.
    """
    captured = {}

    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            captured["payload"] = json.loads(kw["input"])
            return _completed(stdout=jsonl_text_stream(['{"k":', ' "v"}']))
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    out = client.call_responses(
        model="gpt-5.4",
        instructions="Return a JSON object with key k.",
        messages=[{"role": "user", "content": "give me json"}],
        response_format={"type": "json_object"},
    )
    assert out == '{"k": "v"}'
    p = captured["payload"]
    assert p["model"] == "gpt-5.4"
    assert p["instructions"] == "Return a JSON object with key k."
    assert p["stream"] is True
    assert p["store"] is False
    assert p["text"] == {"format": {"type": "json_object"}}
    assert p["input"] == [{"role": "user", "content": "give me json"}]
```

- [ ] **Step 2: Run, expect FAIL**

```bash
uv run pytest tests/test_codex_client.py::test_call_responses_aggregates_text -v
```
Expected: `AttributeError: 'CodexClient' object has no attribute 'call_responses'`.

- [ ] **Step 3: Implement `call_responses` + `_run_and_extract_text`**

Append to `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/codex_client.py`:

```python
    def call_responses(
        self,
        *,
        model: str,
        instructions: str,
        input: list[dict],
        response_format: dict | None = None,
    ) -> str:
        """Text/structured response. Returns aggregated output_text.

        Honours OAuth-only payload constraints discovered in the Phase 0 spike:
        - `instructions` is REQUIRED at top level (server 400 without it).
        - `store: false` is REQUIRED (server defaults true and rejects).
        - `stream: true` is REQUIRED.
        - When `response_format = {"type":"json_object"}`, the caller is responsible
          for ensuring the user-role input contains the literal word "json"
          (OpenAI's own Responses API constraint, surfaced as 400).
        """
        payload: dict = {
            "model": model,
            "instructions": instructions,
            "input": input,
            "stream": True,
            "store": False,
        }
        if response_format:
            payload["text"] = {"format": response_format}
        return self._run_and_extract_text(payload)

    def _run_and_extract_text(self, payload: dict) -> str:
        """Accumulate response.output_text.delta events until response.completed.

        The codex CLI (verified against openai/codex @ rust-v0.123.0 source) does
        NOT emit response.output_text.done. Terminator is response.completed.
        """
        proc = subprocess.run(
            [self.codex_bin, "responses"],
            input=json.dumps(payload),
            capture_output=True, text=True, timeout=self.timeout_sec,
        )
        if proc.returncode != 0:
            raise CodexCallError(
                f"codex responses exit={proc.returncode}: {proc.stderr.strip()[:500]}"
            )
        deltas: list[str] = []
        completed = False
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = event.get("type", "")
            if etype == "response.output_text.delta":
                deltas.append(event.get("delta", ""))
            elif etype == "response.completed":
                completed = True
                break
        if not completed:
            raise CodexCallError(
                f"stream ended without response.completed (got {len(proc.stdout)} bytes)"
            )
        return "".join(deltas)
```

- [ ] **Step 4: Run, expect PASS**

```bash
uv run pytest tests/test_codex_client.py::test_call_responses_aggregates_text -v
```
Expected: PASS.

---

### Task 3.5: TDD `generate_image_with_reference` (payload shape + bytes return)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_codex_client.py`:

```python
import base64
from tests.conftest import jsonl_image_stream


def test_generate_image_with_reference(tmp_path, monkeypatch, fake_login_ok):
    """generate_image_with_reference returns decoded PNG bytes and builds a payload
    that honours OAuth-only constraints: orchestrator chat model (NOT gpt-image-2),
    top-level instructions, store:false, image_generation tool + tool_choice.
    """
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    fake_b64 = base64.b64encode(b"fakepngbytes").decode()

    captured = {}

    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            captured["payload"] = json.loads(kw["input"])
            return _completed(stdout=jsonl_image_stream(fake_b64))
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    img = client.generate_image_with_reference(
        orchestrator_model="gpt-5.4",
        reference_image=ref,
        prompt="hero shot",
        size=(1088, 1600),
        quality="high",
    )
    assert img == b"fakepngbytes"

    p = captured["payload"]
    assert p["model"] == "gpt-5.4"  # orchestrator, NOT gpt-image-2
    assert "instructions" in p and len(p["instructions"]) > 0
    assert p["stream"] is True
    assert p["store"] is False
    assert p["tools"] == [{"type": "image_generation", "size": "1088x1600", "quality": "high"}]
    assert p["tool_choice"] == {"type": "image_generation"}
    content = p["input"][0]["content"]
    assert content[0]["type"] == "input_image"
    assert content[0]["image_url"].startswith("data:image/png;base64,")
    assert content[1] == {"type": "input_text", "text": "hero shot"}
```

- [ ] **Step 2: Run, expect FAIL**

```bash
uv run pytest tests/test_codex_client.py::test_generate_image_with_reference -v
```
Expected: `AttributeError: 'CodexClient' object has no attribute 'generate_image_with_reference'`.

- [ ] **Step 3: Implement `generate_image_with_reference` + `_run_and_extract_image`**

Append to `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/codex_client.py`:

```python
    # Fixed art-director instructions for image calls — keeps identity of the
    # referenced subject and renders Korean text legibly. Tuned during Phase 0 spike.
    _IMAGE_INSTRUCTIONS = (
        "You are a Korean e-commerce art director. Produce a single vertical "
        "promo image at the requested size. Always preserve the identity of the "
        "referenced subject (face, form, colours) and render all Korean text "
        "crisply and legibly."
    )

    def generate_image_with_reference(
        self,
        *,
        orchestrator_model: str,    # MUST be a chat model (e.g. 'gpt-5.4'), NOT gpt-image-2
        reference_image: Path,
        prompt: str,
        size: tuple[int, int],
        quality: str = "high",
    ) -> bytes:
        """Image-to-image generation under ChatGPT OAuth.

        Phase 0 spike established that `model="gpt-image-2"` is rejected by
        ChatGPT OAuth ("not supported"). The working pattern is an orchestrator
        chat model (e.g. gpt-5.4) that invokes the image_generation tool:
        the chat model passes the reference image and prompt through to the
        tool, and the tool emits the PNG in a `response.output_item.done` event.

        Returns decoded PNG bytes.
        """
        b64 = base64.b64encode(reference_image.read_bytes()).decode()
        payload = {
            "model": orchestrator_model,
            "instructions": self._IMAGE_INSTRUCTIONS,
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
            "store": False,
        }
        return self._run_and_extract_image(payload)

    def _run_and_extract_image(self, payload: dict) -> bytes:
        proc = subprocess.run(
            [self.codex_bin, "responses"],
            input=json.dumps(payload),
            capture_output=True, text=True, timeout=self.timeout_sec,
        )
        if proc.returncode != 0:
            raise CodexCallError(
                f"codex responses exit={proc.returncode}: {proc.stderr.strip()[:500]}"
            )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "response.output_item.done":
                item = event.get("item", {})
                if item.get("type") == "image_generation_call" and item.get("result"):
                    return base64.b64decode(item["result"])
        raise CodexCallError(
            f"no image_generation_call.result in stdout (got {len(proc.stdout)} bytes)"
        )
```

- [ ] **Step 4: Run, expect PASS**

```bash
uv run pytest tests/test_codex_client.py::test_generate_image_with_reference -v
```
Expected: PASS.

---

### Task 3.6: Run full test suite + commit

- [ ] **Step 1: Run all unit tests**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run pytest tests/ -v
```
Expected: 4 PASS (verify_login success, verify_login failure, call_responses, generate_image_with_reference). Live tests should be skipped.

- [ ] **Step 2: Commit**

```bash
git add sangpye_skill/codex_client.py tests/
git commit -m "feat: codex_client subprocess wrapper (TDD, mocked subprocess) — verify_login + call_responses + generate_image_with_reference"
```

---

## Phase 4 — Port `analysis.py`

### Task 4.1: Vendor + adapt analysis.py

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/analysis.py`
  (from: `/Users/genie/dev/side/make-detailed-product-page/app/services/analysis.py`)

- [ ] **Step 1: Copy the file**

```bash
cp /Users/genie/dev/side/make-detailed-product-page/app/services/analysis.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/analysis.py
```

- [ ] **Step 2: Rewrite imports — drop `OpenAI`, switch to `CodexClient`**

Edit `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/analysis.py`:

Replace:
```python
from openai import OpenAI
from app.services.section_language import SECTION_LANGUAGES
from app.services.category_briefs import get_brief, CATEGORY_BRIEFS
from app.services.product_dna import ProductDNA
```
with:
```python
from sangpye_skill.codex_client import CodexClient
from sangpye_skill.section_language import SECTION_LANGUAGES
from sangpye_skill.category_briefs import get_brief, CATEGORY_BRIEFS
from sangpye_skill.product_dna import ProductDNA
```

(Note: there are two import blocks in the file — one at top for `ProductDNA`, one mid-file for the rest. Update both.)

- [ ] **Step 3: Adapt `AnalysisService.__init__` and `build_plan`**

In the same file, replace the `AnalysisService` class with:

```python
class AnalysisService:
    def __init__(self, client: CodexClient, model: str = MODEL):
        self.client = client
        self.model = model

    def build_plan(self, images: list[Path], prompt: str, category: str) -> AnalysisPlan:
        if category not in CATEGORY_BRIEFS:
            category = "general"
        # Phase 0 spike: when text.format=json_object is set, the user message
        # MUST contain the literal word "json" or the server returns 400.
        user_text = (
            f"User prompt: {prompt}\nCategory: {category}\nImage count: {len(images)}\n"
            f"Return your answer as a JSON object matching the schema in the instructions. "
            f"JSON only, no prose."
        )
        content: list[dict] = [{"type": "input_text", "text": user_text}]
        for img in images:
            b64 = base64.b64encode(img.read_bytes()).decode()
            content.append({"type": "input_image", "image_url": f"data:image/png;base64,{b64}"})

        instructions = _build_system_prompt(category)

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Phase 0 spike: system role in `input` returns 400; the system
                # prompt must be passed as the top-level `instructions` field.
                raw = self.client.call_responses(
                    model=self.model,
                    instructions=instructions,
                    messages=[{"role": "user", "content": content}],
                    response_format={"type": "json_object"},
                )
                logger.info("analysis response (%d chars): %s", len(raw), raw[:800])
                data = json.loads(raw)
                plan = AnalysisPlan.model_validate(data)
                if plan.master_image_index >= len(images):
                    plan.master_image_index = 0  # clamp
                logger.info("analysis OK: master=%d, bundles=%d", plan.master_image_index, len(plan.bundles))
                return plan
            except Exception as e:
                last_error = e
                logger.warning("analysis attempt %d/%d failed: %s", attempt, MAX_RETRIES, e)
        raise RuntimeError(f"analysis failed after {MAX_RETRIES} attempts: {last_error}")
```

- [ ] **Step 4: Verify no `app.*` or `openai` imports remain**

```bash
grep -E "from app\.|import app\.|from openai|import openai" \
  /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/analysis.py
```
Expected: no output.

- [ ] **Step 5: Smoke-import**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python -c "from sangpye_skill.analysis import AnalysisService, AnalysisPlan; print('OK')"
```
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add sangpye_skill/analysis.py
git commit -m "feat: port analysis.py to use CodexClient (replaces OpenAI SDK responses.create)"
```

---

## Phase 5 — Port `image_generator.py`

### Task 5.1: Vendor + adapt image_generator_v3.py

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/image_generator.py`
  (from: `/Users/genie/dev/side/make-detailed-product-page/app/services/image_generator_v3.py`)

- [ ] **Step 1: Copy + rename**

```bash
cp /Users/genie/dev/side/make-detailed-product-page/app/services/image_generator_v3.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/image_generator.py
```

- [ ] **Step 2: Rewrite imports + swap MODEL constant**

Edit `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/image_generator.py`:

Replace:
```python
from openai import OpenAI
```
with:
```python
from sangpye_skill.codex_client import CodexClient
```

Replace the constant:
```python
MODEL = "gpt-image-2"
```
with:
```python
# Phase 0 spike: ChatGPT OAuth refuses direct gpt-image-2 calls. Use a chat
# orchestrator that invokes the image_generation tool via codex_client.
ORCHESTRATOR_MODEL = "gpt-5.4"
```

- [ ] **Step 3: Replace the `_generate_single_bundle` body**

In the same file, replace the entire `_generate_single_bundle` method body with:

```python
    def _generate_single_bundle(
        self,
        master_image: Path,
        bundle: dict,
        cancel_check: Callable[[], bool] | None,
    ) -> bytes:
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            if cancel_check and cancel_check():
                raise JobCancelled()
            try:
                size = (bundle["size"][0], bundle["size"][1])
                # Phase 0 spike: ChatGPT OAuth rejects direct gpt-image-2 calls.
                # The image_generation tool must be invoked via a chat orchestrator.
                return self.client.generate_image_with_reference(
                    orchestrator_model=ORCHESTRATOR_MODEL,
                    reference_image=master_image,
                    prompt=bundle["prompt"],
                    size=size,
                    quality=self.quality,
                )
            except Exception as e:
                last_error = e
                if attempt >= MAX_RETRIES:
                    break
                err = str(e)
                is_overload = any(s in err for s in OVERLOAD_SIGNALS)
                delay = int(RETRY_BACKOFF_SEC[attempt - 1] * (1.5 if is_overload else 1))
                logger.warning("bundle %s retry %d/%d in %ds: %s",
                               bundle["bundle_id"], attempt, MAX_RETRIES, delay, e)
                t_end = time.time() + delay
                while time.time() < t_end:
                    if cancel_check and cancel_check():
                        raise JobCancelled()
                    time.sleep(min(3, t_end - time.time()))
        raise last_error or RuntimeError("bundle generation failed")
```

- [ ] **Step 4: Update the `__init__` signature to take `CodexClient`**

In the same file, change:
```python
    def __init__(
        self,
        client: OpenAI,
        quality: Literal["standard", "high"] = "high",
    ):
```
to:
```python
    def __init__(
        self,
        client: CodexClient,
        quality: Literal["standard", "high"] = "high",
    ):
```

- [ ] **Step 5: Rename the class for clarity**

Rename `class ImageGeneratorV3:` → `class ImageGenerator:` (since v3 is the only version in the new repo).

```bash
sed -i '' 's/class ImageGeneratorV3:/class ImageGenerator:/' \
  /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/image_generator.py
```

- [ ] **Step 6: Verify clean imports + smoke**

```bash
grep -E "from app\.|import app\.|from openai|import openai" \
  /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/image_generator.py
```
Expected: no output.

```bash
uv run python -c "from sangpye_skill.image_generator import ImageGenerator, JobCancelled, MAX_CONCURRENCY; print(MAX_CONCURRENCY)"
```
Expected: `3`

- [ ] **Step 7: Commit**

```bash
git add sangpye_skill/image_generator.py
git commit -m "feat: port image_generator.py — single call site swaps images.edit -> CodexClient.generate_image_with_reference"
```

---

## Phase 6 — Port `pipeline.py`

### Task 6.1: Vendor + adapt pipeline.py

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/pipeline.py`
  (from: `/Users/genie/dev/side/make-detailed-product-page/app/services/pipeline.py`)

- [ ] **Step 1: Copy the file**

```bash
cp /Users/genie/dev/side/make-detailed-product-page/app/services/pipeline.py \
   /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/pipeline.py
```

- [ ] **Step 2: Rewrite imports**

Edit `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/pipeline.py`:

Replace the entire imports block at the top with:

```python
"""v3 Pipeline: analyze -> render 5 bundles -> slice 13 sections -> compose -> finalize.

Synchronous CLI variant — no Celery, no Redis, no cancel/status callbacks.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Callable, Literal

from sangpye_skill.codex_client import CodexClient
from sangpye_skill.analysis import AnalysisService
from sangpye_skill.image_generator import ImageGenerator, JobCancelled
from sangpye_skill.bundle_slicer import BundleSlicer, SectionSlice
from sangpye_skill.composer import ComposerService, SECTIONS
from sangpye_skill.product_dna import inject_dna_into_prompt
```

- [ ] **Step 3: Adapt `PipelineService.__init__`**

In the same file, replace the `__init__` with:

```python
class PipelineService:
    def __init__(
        self,
        quality: Literal["standard", "high"] = "high",
        codex_bin: str = "codex",
    ):
        self.client = CodexClient(codex_bin=codex_bin)
        self.analysis = AnalysisService(client=self.client)
        self.generator = ImageGenerator(client=self.client, quality=quality)
        self.slicer = BundleSlicer()
        self.composer = ComposerService()
```

- [ ] **Step 4: Simplify `run()` signature**

Change the `run()` method signature from:
```python
    def run(
        self,
        user_images: list[Path],
        prompt: str,
        category: str,
        output_dir: Path,
        job_id: str,
        cancel_check: Callable[[], bool] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
    ) -> dict:
```
to:
```python
    def run(
        self,
        user_images: list[Path],
        prompt: str,
        category: str,
        output_dir: Path,
        job_id: str,
        progress_callback: Callable[[int, int], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
    ) -> dict:
```

(Drop only `cancel_check`. Keep `progress_callback` and `status_callback` — the CLI will wire stderr printers to them.)

- [ ] **Step 5: Remove `cancel_check` references inside `run()`**

In the body of `run()`, delete every occurrence of:
```python
        if cancel_check and cancel_check():
            raise JobCancelled()
```

And in the call to `self.generator.render_bundles_parallel(...)`, drop the `cancel_check=cancel_check,` keyword argument. Also update `image_generator.py` later if needed — but the existing signature accepts `cancel_check=None` already, so passing nothing works.

Actually: just remove the `cancel_check=cancel_check,` line from the call.

- [ ] **Step 6: Verify clean imports + smoke**

```bash
grep -E "from app\.|import app\." \
  /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/pipeline.py
```
Expected: no output.

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python -c "from sangpye_skill.pipeline import PipelineService, BUNDLE_SECTION_MAP; print(len(BUNDLE_SECTION_MAP))"
```
Expected: `5`

- [ ] **Step 7: Commit**

```bash
git add sangpye_skill/pipeline.py
git commit -m "feat: port pipeline.py — drop async/cancel/Redis bits, wire CodexClient through PipelineService"
```

---

## Phase 7 — CLI

### Task 7.1: Implement `cli.py`

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/cli.py`

- [ ] **Step 1: Write the CLI**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/sangpye_skill/cli.py <<'EOF'
"""sangpye CLI — argparse entry point for the codex-sangpye-skill package."""
from __future__ import annotations
import argparse
import json
import logging
import secrets
import sys
import time
from pathlib import Path

from sangpye_skill import __version__
from sangpye_skill.codex_client import CodexAuthError, CodexCallError
from sangpye_skill.constants import MAX_UPLOAD_IMAGES
from sangpye_skill.pipeline import PipelineService

EXIT_OK = 0
EXIT_AUTH = 1
EXIT_INPUT = 2
EXIT_API = 3
EXIT_FS = 4

CATEGORIES = ["electronics", "fashion", "food", "beauty", "home", "general"]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sangpye",
        description="Generate a 13-section Korean e-commerce detail page (1080x7500 combined image) from product photos via Codex OAuth.",
    )
    p.add_argument("--version", action="version", version=f"sangpye {__version__}")
    p.add_argument("--image", action="append", required=True, metavar="PATH",
                   help=f"Product image path (repeat 1-{MAX_UPLOAD_IMAGES} times).")
    p.add_argument("--prompt", required=True, help="Korean product brief.")
    p.add_argument("--category", choices=CATEGORIES, default="general")
    p.add_argument("--output", default="./sangpye-output", metavar="DIR",
                   help="Parent output directory (default: ./sangpye-output).")
    p.add_argument("--quality", choices=["standard", "high"], default="high")
    p.add_argument("--job-id", default=None, help="Override the auto-generated 8-char job id.")
    p.add_argument("--codex-bin", default="codex", help="Path to the codex CLI binary (default: codex on PATH).")
    return p


def _validate_inputs(args: argparse.Namespace) -> tuple[list[Path], Path, str]:
    images = [Path(s).expanduser().resolve() for s in args.image]
    if not (1 <= len(images) <= MAX_UPLOAD_IMAGES):
        raise SystemExit(f"--image: must provide 1 to {MAX_UPLOAD_IMAGES} images (got {len(images)})")
    for img in images:
        if not img.exists() or not img.is_file():
            raise SystemExit(f"--image: not a file: {img}")
    job_id = args.job_id or secrets.token_hex(4)
    out_root = Path(args.output).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    output_dir = out_root / job_id
    return images, output_dir, job_id


def _stderr(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    parser = _build_parser()
    args = parser.parse_args()

    try:
        images, output_dir, job_id = _validate_inputs(args)
    except SystemExit as e:
        _stderr(f"error: {e}")
        return EXIT_INPUT

    _stderr(f"[1/6] codex login status: checking...")
    try:
        pipeline = PipelineService(quality=args.quality, codex_bin=args.codex_bin)
    except CodexAuthError as e:
        _stderr(f"error: {e}")
        return EXIT_AUTH

    _stderr(f"      OK ({len(images)} image(s), job_id={job_id})")

    def on_status(status: str, step: str) -> None:
        _stderr(f"      [{status}] {step}")

    def on_progress(done: int, total: int) -> None:
        _stderr(f"      progress: {done}/{total}")

    t0 = time.time()
    try:
        result = pipeline.run(
            user_images=images,
            prompt=args.prompt,
            category=args.category,
            output_dir=output_dir,
            job_id=job_id,
            progress_callback=on_progress,
            status_callback=on_status,
        )
    except (CodexAuthError, CodexCallError) as e:
        _stderr(f"error (codex): {e}")
        return EXIT_API
    except OSError as e:
        _stderr(f"error (filesystem): {e}")
        return EXIT_FS
    except Exception as e:
        _stderr(f"error (pipeline): {e}")
        return EXIT_API

    elapsed = round(time.time() - t0, 1)
    _stderr(f"Done. Total: {elapsed}s")

    # Emit machine-readable result on stdout
    plan_path = output_dir / "analysis.json"
    plan_path.write_text(json.dumps(result["plan"], ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {
        "job_id": job_id,
        "output_dir": str(output_dir),
        "combined": str(result["combined_path"]),
        "sections": [str(p) for p in result["section_paths"]],
        "plan_path": str(plan_path),
        "elapsed_sec": elapsed,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
EOF
```

- [ ] **Step 2: Verify `--help`**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run sangpye --help
```
Expected: argparse-formatted help showing all flags.

- [ ] **Step 3: Verify `--version`**

```bash
uv run sangpye --version
```
Expected: `sangpye 0.1.0`

- [ ] **Step 4: Negative test — missing required args**

```bash
uv run sangpye --prompt "test" 2>&1 | head -5
```
Expected: argparse error mentioning `--image` is required. Exit code 2.

- [ ] **Step 5: Commit**

```bash
git add sangpye_skill/cli.py
git commit -m "feat: cli.py — argparse entry, stderr progress, stdout JSON, exit codes (0/1/2/3/4)"
```

---

### Task 7.2: Fallback `scripts/generate.py`

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/scripts/generate.py`

- [ ] **Step 1: Write the thin wrapper**

```bash
mkdir -p /Users/genie/dev/side/codex-sangpye-skill/scripts
cat > /Users/genie/dev/side/codex-sangpye-skill/scripts/generate.py <<'EOF'
"""Fallback wrapper for users who haven't `uv tool install`ed the package globally.

Usage:
    python scripts/generate.py --image ... --prompt "..." --output ./out
"""
from sangpye_skill.cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
EOF
```

- [ ] **Step 2: Verify it runs**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run python scripts/generate.py --version
```
Expected: `sangpye 0.1.0`

- [ ] **Step 3: Commit**

```bash
git add scripts/generate.py
git commit -m "feat: scripts/generate.py fallback wrapper for non-installed use"
```

---

## Phase 8 — `SKILL.md`, `README.md`, examples

### Task 8.1: Write `SKILL.md`

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/SKILL.md`

- [ ] **Step 1: Write the skill manifest**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/SKILL.md <<'EOF'
---
name: codex-sangpye
description: Generate a 13-section Korean e-commerce product detail page (1080x7500 combined image + 13 individual section PNGs) from 1-14 product photos plus a Korean brief, using the Codex CLI's `codex responses` entrypoint under the active Codex OAuth session (no separate OpenAI API key required).
version: 0.1.0
author: <YOUR NAME>
license: MIT
metadata:
  hermes:
    tags: [codex, image-generation, oauth, ecommerce, korean, detail-page, sangpye]
    related_skills: [codex-image-generation]
---

## When to use

When the user wants a Korean e-commerce product detail page asset set — 13 emotional-journey sections (Hero -> Pain -> Problem -> Story -> Solution -> How -> Proof -> Authority -> Benefits -> Risk -> Compare -> Filter -> CTA) plus a single 1080x7500 combined PNG — generated from 1-14 product photos and a brief.

Prefer this skill over invoking image generation by hand, because:
- It runs the full analysis (gpt-5.4) + 5-bundle parallel image generation (gpt-image-2) + slicing + vertical composition pipeline.
- It uses your Codex OAuth session — no API key, no per-token billing.
- One command, one JSON result.

## Preconditions

1. `codex >= rust-v0.122.0` is on PATH (check with `codex --version`) and `codex login status` reports an active OAuth/ChatGPT session (not an API key).
2. `CODEX_API_KEY` env var is **unset** — if set, it overrides OAuth and may unlock different models / billing. (`OPENAI_API_KEY` is ignored at runtime by `codex responses` — do not rely on it.)
3. `sangpye --version` succeeds (install via `uv tool install git+https://github.com/<YOUR USER>/codex-sangpye-skill`).
4. 1-14 product image files exist locally.

If any precondition fails, tell the user how to fix and stop.

## Command path

`sangpye` (installed globally via `uv tool install`).

## Parameters

| Flag | Required | Default | Description |
|---|---|---|---|
| `--image PATH` | yes | — | Repeat 1-14 times. Product image path. |
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

`stdout` (machine-readable):
```json
{"job_id":"a1b2c3d4","output_dir":"./out/a1b2c3d4","combined":"./out/a1b2c3d4/combined.png","sections":["./out/a1b2c3d4/sections/01_hero.png","..."],"plan_path":"./out/a1b2c3d4/analysis.json","elapsed_sec":252.4}
```

Show the user:
1. The absolute path to `combined.png` (the main deliverable, 1080x7500).
2. The `job_id` so they can find the artifacts again.
3. Optionally, the list of 13 individual section PNGs.

## Troubleshooting

- **`error: codex login status failed`** -> Run `codex logout && codex login`, pick the OAuth/ChatGPT option. Note: `OPENAI_API_KEY` in the shell is ignored at runtime; only `CODEX_API_KEY` overrides OAuth.
- **`error: codex responses expects a streaming payload`** -> Upgrade to `codex >= rust-v0.122.0`.
- **`error (codex): ... model not available`** -> The user's ChatGPT subscription tier may not include `gpt-5.4` or `gpt-image-2`. Surface the error verbatim — do not retry.
- **`error (codex): rate_limit`** -> ChatGPT subscription is throttling. Wait a few minutes and retry, or pass `--quality standard`.
- **Pipeline hangs / `stream ended without response.completed`** -> `codex` version mismatch (older CLIs emit a different event schema). Upgrade and retry.

## Agent rule

After a successful run, ALWAYS show the user the absolute path to `combined.png` and the `job_id`. Do not silently retry on errors — surface them so the user can decide. Do not invoke this skill more than once per user request unless explicitly asked.
EOF
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "docs: SKILL.md — Hermes/Claude skill manifest mirroring codex-image-generation-skill structure"
```

---

### Task 8.2: Write `README.md`

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/README.md`

- [ ] **Step 1: Write README**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/README.md <<'EOF'
# codex-sangpye-skill

Generate Korean e-commerce product detail page images (13 sections + 1080x7500 combined) from 1-14 product photos and a brief — using your **Codex OAuth session** (ChatGPT Plus/Pro), no OpenAI API key required.

## What it produces

- **13 section PNGs** at 1080xH (variable height per section): Hero -> Pain -> Problem -> Story -> Solution -> How -> Proof -> Authority -> Benefits -> Risk -> Compare -> Filter -> CTA
- **1 combined PNG** at 1080x7500 (vertical composition of all 13)
- **1 analysis.json** with the full creative plan (Product DNA, bundle prompts, Korean copy)

## Install

```bash
# 1. Make sure you have `uv` and `codex >= rust-v0.122.0`
brew install uv
# codex install: see https://github.com/openai/codex
codex --version   # must be >= rust-v0.122.0

# 2. Log in to Codex with your ChatGPT account (NOT API key)
codex login       # pick the OAuth / ChatGPT option
unset CODEX_API_KEY   # if set, it overrides OAuth
# (OPENAI_API_KEY in your shell is ignored at runtime — no need to unset.)

# 3. Install sangpye globally
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
{"job_id":"a1b2c3d4","combined":"./out/a1b2c3d4/combined.png","sections":["./out/a1b2c3d4/sections/01_hero.png","..."],"elapsed_sec":252.4}
```

Stderr shows progress in real time.

## Use (as a Claude / Hermes / Codex skill)

Drop `SKILL.md` from this repo into your skills directory (e.g. `~/.claude/skills/codex-sangpye/SKILL.md` or `~/.hermes/skills/creative/codex-sangpye/SKILL.md`). The agent will discover it and call `sangpye` for you.

## How it works

1. **Analyze** — gpt-5.4 multimodal call returns ProductDNA + 5 bundle specs + Korean copy.
2. **Generate** — 5 parallel gpt-image-2 calls produce 5 large bundle PNGs (1088x{1600,2800,3120,2800,2400}), each using your master image as a reference.
3. **Slice** — each bundle is sliced by Y-coordinate into its constituent sections (1-3 per bundle, 13 total).
4. **Compose** — Pillow stitches the 13 sections vertically into `combined.png` (1080x7500).

All four steps run synchronously in one process. No Docker, no Redis, no Celery.

## Architecture (extract from the production backend)

Ported from the FastAPI/Celery production stack at `make-detailed-product-page` (branch `feat/openai-migration`):

| Original | Here | Change |
|---|---|---|
| `app/services/openai_client.py` | `sangpye_skill/codex_client.py` | Rewritten: subprocess wrapper around `codex responses` |
| `app/services/pipeline.py` | `sangpye_skill/pipeline.py` | Synchronous; no Celery, no Redis, no cancel hooks |
| `app/services/analysis.py` | `sangpye_skill/analysis.py` | Same prompt + schema; calls `codex_client.call_responses` |
| `app/services/image_generator_v3.py` | `sangpye_skill/image_generator.py` | Same retry/concurrency logic; calls `codex_client.generate_image_with_reference` |
| `app/services/{bundle_slicer,composer,product_dna,section_language,category_briefs}.py` | same names | Vendored as-is |
| FastAPI / Celery / Redis / Docker | — | Dropped |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `codex: command not found` | Install codex CLI from https://github.com/openai/codex |
| `codex --version` < `rust-v0.122.0` | Upgrade — the `responses` subcommand was stabilized in v0.122.0 |
| `error: codex login status failed` | `codex login` and pick OAuth/ChatGPT option |
| `stream ended without response.completed` | codex CLI version mismatch — upgrade to `>= rust-v0.122.0` |
| OAuth not being used despite `codex login` | Check `CODEX_API_KEY` — if set, it overrides OAuth. `unset CODEX_API_KEY` |
| `error (codex): model not available` | Your ChatGPT subscription tier may not expose `gpt-5.4` or `gpt-image-2` |
| `error (codex): rate_limit` | ChatGPT subscription is throttling — wait or use `--quality standard` |
| Slow runs (>10 min) | OAuth may serialize parallel calls; this is expected |

## License

MIT.
EOF
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README — install, usage, architecture extract diagram, troubleshooting"
```

---

### Task 8.3: Add a sample example image

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/examples/sample_product.jpg`

- [ ] **Step 1: Copy the spike sample (if Phase 0 used one)**

```bash
mkdir -p /Users/genie/dev/side/codex-sangpye-skill/examples
cp /Users/genie/dev/side/make-detailed-product-page/spike/codex_oauth/sample_inputs/earbuds_01.jpg \
   /Users/genie/dev/side/codex-sangpye-skill/examples/sample_product.jpg
```

- [ ] **Step 2: Commit**

```bash
git add examples/
git commit -m "docs: add examples/sample_product.jpg for README and live tests"
```

---

## Phase 9 — Live integration test

### Task 9.1: Write the live test

**Files:**
- Create: `/Users/genie/dev/side/codex-sangpye-skill/tests/test_pipeline_live.py`

- [ ] **Step 1: Write the test**

```bash
cat > /Users/genie/dev/side/codex-sangpye-skill/tests/test_pipeline_live.py <<'EOF'
"""Live integration test — hits real codex OAuth. Marked `live`, skipped by default.

Run with: `uv run pytest -m live tests/test_pipeline_live.py -v`
Cost: counts against ChatGPT subscription quota (one full pipeline run).
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
import pytest
from PIL import Image

REPO = Path(__file__).parent.parent
SAMPLE = REPO / "examples" / "sample_product.jpg"


@pytest.mark.live
def test_full_pipeline_via_cli(tmp_path):
    if not SAMPLE.exists():
        pytest.skip(f"sample missing at {SAMPLE}")

    proc = subprocess.run(
        [
            sys.executable, "-m", "sangpye_skill.cli",
            "--image", str(SAMPLE),
            "--prompt", "프리미엄 무선 이어폰, ANC, 30시간 배터리. 라이브 통합 테스트.",
            "--category", "electronics",
            "--output", str(tmp_path),
            "--quality", "standard",  # cheaper for tests
        ],
        capture_output=True, text=True, timeout=900,
    )
    assert proc.returncode == 0, f"CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Parse the single JSON line on stdout
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    assert "combined" in result
    assert "sections" in result
    assert len(result["sections"]) == 13

    combined = Path(result["combined"])
    assert combined.exists()
    with Image.open(combined) as im:
        assert im.size == (1080, 7500), f"combined size = {im.size}, expected (1080, 7500)"

    for section_path in result["sections"]:
        p = Path(section_path)
        assert p.exists(), f"missing section {p}"
        with Image.open(p) as im:
            assert im.width == 1080, f"section {p.name} width = {im.width}, expected 1080"
EOF
```

- [ ] **Step 2: Run the live test**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
uv run pytest -m live tests/test_pipeline_live.py -v
```
Expected: PASS within 5-10 minutes. If it fails, examine stderr; common causes: codex auth dropped mid-run, model not available, rate limit.

- [ ] **Step 3: Commit**

```bash
git add tests/test_pipeline_live.py
git commit -m "test: live end-to-end pipeline test (pytest -m live, off by default)"
```

---

## Phase 10 — Public release

### Task 10.1: Push to GitHub

- [ ] **Step 1: Create the GitHub repo**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
gh repo create codex-sangpye-skill --public --description "Generate Korean e-commerce product detail page images via Codex OAuth — 13 sections + 1080x7500 combined" --source=. --remote=origin
```
Expected: GitHub repo created, `origin` remote added.

- [ ] **Step 2: Push**

```bash
git push -u origin main
```
Expected: branch published, repo URL printed.

---

### Task 10.2: Verify `uv tool install git+...` from a clean env

- [ ] **Step 1: Install from GitHub in an isolated env**

```bash
# Use a temp dir with no Python state
TMPDIR=$(mktemp -d) && cd "$TMPDIR"
uv tool install git+https://github.com/<YOUR USER>/codex-sangpye-skill
which sangpye
sangpye --version
```
Expected: `sangpye 0.1.0`

- [ ] **Step 2: Run a quick smoke against the install**

```bash
sangpye \
  --image /Users/genie/dev/side/codex-sangpye-skill/examples/sample_product.jpg \
  --prompt "스모크 테스트" \
  --quality standard \
  --output /tmp/sangpye-smoke
```
Expected: completes in 5-10 min, JSON on stdout, `combined.png` at 1080x7500 in `/tmp/sangpye-smoke/<job_id>/`.

- [ ] **Step 3: Cleanup if anything looks off**

```bash
uv tool uninstall codex-sangpye-skill   # only if reinstall needed
```

---

### Task 10.3: Wire into Claude Code / Codex skill discovery

- [ ] **Step 1: Drop `SKILL.md` into the skills directory**

For Claude Code (user-level skills):
```bash
mkdir -p ~/.claude/skills/codex-sangpye
cp /Users/genie/dev/side/codex-sangpye-skill/SKILL.md ~/.claude/skills/codex-sangpye/SKILL.md
```

For Hermes / Codex (if applicable, mirroring the reference skill):
```bash
mkdir -p ~/.hermes/skills/creative/codex-sangpye
cp /Users/genie/dev/side/codex-sangpye-skill/SKILL.md ~/.hermes/skills/creative/codex-sangpye/SKILL.md
```

- [ ] **Step 2: Verify discovery in a fresh session**

Open a new Claude Code session in any directory and ask: "use the codex-sangpye skill to generate a detail page for this product photo: <path>". Confirm the agent invokes `sangpye` and surfaces the resulting `combined.png` path.

- [ ] **Step 3: Final commit + release tag**

```bash
cd /Users/genie/dev/side/codex-sangpye-skill
git tag -a v0.1.0 -m "v0.1.0 — initial release: codex OAuth, sangpye CLI, 13-section detail page generator"
git push origin v0.1.0
```

---

## Self-review

**Spec coverage:**
- §1 Goal — covered by all phases.
- §2 Success criteria — verified in Tasks 7.2, 7.3, 9.1, 10.2.
- §4 Phase 0 spike (3 sub-spikes + GO/NO-GO) — Tasks 0.1-0.5.
- §5 Repo scaffolding + packaging — Tasks 1.1-1.5.
- §6 Vendoring map (every row) — Tasks 2.1-2.6, 4.1, 5.1, 6.1.
- §7 CodexClient interface — Tasks 3.1-3.6.
- §8 CLI contract (flags, JSON output, exit codes) — Task 7.1.
- §9 SKILL.md (frontmatter + body sections) — Task 8.1.
- §10 Testing plan (unit + live + smoke) — Tasks 3.6, 9.1, 10.2.
- §11 Rollout (steps 1-12) — Tasks 0.5, 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 8.2, 10.1, 10.3.
- §12 Risks — mitigations baked into spike (auth, custom size, parallel rate limits) and CLI error mapping.

**Placeholder scan:**
- `<YOUR NAME>` and `<YOUR USER>` appear in LICENSE, pyproject.toml, SKILL.md, README.md — these are **intentional** placeholders for the user's identity and GitHub handle, filled in at scaffold time. Flagged in instructions.
- No "TBD", "TODO", "implement later" left in any task body.

**Type/name consistency:**
- `CodexClient` (class), `CodexAuthError`, `CodexCallError`, `call_responses`, `generate_image_with_reference`, `_verify_login`, `_run_and_extract_text`, `_run_and_extract_image` — used identically across Tasks 3.x, 4.1, 5.1, 6.1.
- `PipelineService(quality, codex_bin)` — defined in Task 6.1, called from Task 7.1.
- `ImageGenerator` (renamed from `ImageGeneratorV3`) — Task 5.1 step 5 renames, Task 6.1 step 2 imports the new name.
- `MAX_UPLOAD_IMAGES`, `IMAGE_SIZE`, `SECTION_COUNT` — defined in Task 2.1, imported in Task 7.1.
- Exit codes (0/1/2/3/4) — match CLI implementation in Task 7.1 and live test assertion in Task 9.1.

---

## Plan complete

Plan saved to `docs/superpowers/plans/2026-04-23-codex-sangpye-skill.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Especially good for the spike phase (Phase 0) since each spike is a self-contained validation script.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
