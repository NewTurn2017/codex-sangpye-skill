"""Spike 03 — verify 3 concurrent `codex responses` image calls don't get
rate-limited or serialized badly under ChatGPT subscription OAuth.

Mirrors the production pipeline's MAX_CONCURRENCY = 3 setting. PASS criteria:
all 3 complete, no fatal rate-limit errors. WARN if total wall > 180s (OAuth
may be serializing parallel requests — not a failure, but note it).
"""
from __future__ import annotations
import asyncio
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

SPIKE_DIR = Path(__file__).parent
SAMPLE = SPIKE_DIR / "sample_inputs" / "genie.jpg"


VARIATIONS = {
    "hero": (
        "Vertical hero portrait, 1088x1600. Feature the referenced '지니' character front-and-center, "
        "confident pose, premium lighting. Korean headline top: 'codex-sangpye-skill'. "
        "Sub: '지니의 상세페이지 자동 생성 스킬'."
    ),
    "lifestyle": (
        "Vertical lifestyle scene, 1088x1600. The '지니' character at a laptop, watching 13 product "
        "detail-page sections auto-generate on screen. Warm café lighting. "
        "Korean caption bottom: '사진 업로드 한 번, 상세페이지 13장 끝'."
    ),
    "feature": (
        "Vertical feature infographic, 1088x1600. The '지니' character pointing at a visual of "
        "13 stacked detail-page sections. Clean minimal design. "
        "Korean headline: 'Hero → CTA, 13섹션 자동 생성'."
    ),
}


def build_payload(b64: str, label: str) -> dict:
    return {
        "model": "gpt-image-2",
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                {"type": "input_text", "text": VARIATIONS[label]},
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
    except FileNotFoundError:
        return idx, False, time.time() - t0, "codex not on PATH"
    except subprocess.TimeoutExpired:
        return idx, False, time.time() - t0, "timeout"

    elapsed = time.time() - t0
    if proc.returncode != 0:
        return idx, False, elapsed, f"exit {proc.returncode}: {proc.stderr.strip()[:200]}"

    # Look for rate-limit signals in the stream
    rate_limit_hits = []
    found_image = False
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = ev.get("type", "")
        if etype == "response.rate_limits":
            rate_limit_hits.append(ev)
        elif etype == "response.output_item.done":
            item = ev.get("item", {})
            if item.get("type") == "image_generation_call" and item.get("result"):
                found_image = True
                break

    if not found_image:
        return idx, False, elapsed, "no image_generation_call.result"
    note = "ok"
    if rate_limit_hits:
        note = f"ok (rate_limit events seen: {len(rate_limit_hits)})"
    return idx, True, elapsed, note


async def main() -> int:
    if not SAMPLE.exists():
        print(f"FAIL: sample missing at {SAMPLE}", file=sys.stderr)
        return 2
    b64 = base64.b64encode(SAMPLE.read_bytes()).decode()
    payloads = [build_payload(b64, lbl) for lbl in ("hero", "lifestyle", "feature")]

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
        print(f"      (not a failure, but consider MAX_CONCURRENCY=1 or 2 in production)", file=sys.stderr)
    print("PASS: spike 03 — 3 parallel calls completed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
