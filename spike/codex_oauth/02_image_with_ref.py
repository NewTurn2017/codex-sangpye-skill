"""Spike 02 — verify `codex responses` can carry an image-generation tool call
with a reference image (input_image) and a custom 1088×1600 size.

Validates:
- image_generation tool is available under the active OAuth session
- custom (non-standard) sizes pass through the Responses API
- the reference image is honored (visual sanity check — product recognizable)
- Korean text inside the prompt renders as Korean text inside the image
"""
from __future__ import annotations
import base64
import json
import subprocess
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).parent
SAMPLE = SPIKE_DIR / "sample_inputs" / "genie.jpg"
OUT = SPIKE_DIR / "spike02_hero.png"


def main() -> int:
    if not SAMPLE.exists():
        print(f"FAIL: sample missing at {SAMPLE}", file=sys.stderr)
        return 2

    b64 = base64.b64encode(SAMPLE.read_bytes()).decode()
    prompt = (
        "Vertical promo hero image, 1088x1600, Korean e-commerce ad style. "
        "The uploaded reference shows a character named '지니' (genie). "
        "Keep the character's face, hair, expression, and outfit recognizable — use them as the hero. "
        "Place the character on the left side of the composition, looking at the viewer with confidence. "
        "Dramatic studio lighting, clean premium backdrop (soft gradient — cobalt to magenta). "
        "Korean headline overlay top-right, large bold sans-serif, legible: "
        "'codex-sangpye-skill'. "
        "Sub-line directly below: '지니가 만드는 한국 이커머스 상세페이지 스킬'. "
        "Small tagline at the bottom: '상품 사진만 있으면, 고전환 상세페이지 13장 자동 생성'. "
        "Render all Korean text crisply and legibly. "
        "Feel: confident, playful, premium. Save as a launch banner ready to post on SNS."
    )
    # NOTE: model here is the *orchestrator* (which calls the image_generation tool).
    # ChatGPT OAuth refuses direct gpt-image-2 calls ("model is not supported"), but
    # the image_generation tool invoked by a chat model is permitted.
    payload = {
        "model": "gpt-5.4",
        "instructions": (
            "You are a Korean e-commerce art director. Produce a single vertical 1088x1600 "
            "promo hero image. Always preserve the identity of the referenced character "
            "(face, hair, expression, outfit) and render all Korean text crisply and legibly."
        ),
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
        "store": False,
    }

    print(f"[spike 02] generating 1088x1600 hero from {SAMPLE.name}...", file=sys.stderr)
    try:
        proc = subprocess.run(
            ["codex", "responses"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        print("FAIL: `codex` not on PATH", file=sys.stderr)
        return 7
    except subprocess.TimeoutExpired:
        print("FAIL: `codex responses` timed out after 300s", file=sys.stderr)
        return 8

    if proc.returncode != 0:
        print(f"FAIL: codex exit={proc.returncode}", file=sys.stderr)
        print(f"STDERR:\n{proc.stderr}", file=sys.stderr)
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
            if item.get("type") == "image_generation_call" and item.get("result"):
                image_b64 = item["result"]
                break

    if not image_b64:
        print("FAIL: no image_generation_call.result observed in stream", file=sys.stderr)
        print(f"raw stdout (truncated):\n{proc.stdout[:2000]}", file=sys.stderr)
        return 4

    OUT.write_bytes(base64.b64decode(image_b64))

    # Verify dimensions
    try:
        from PIL import Image
    except ImportError:
        print(f"WARN: Pillow not installed — dimension check skipped. PNG saved to {OUT}", file=sys.stderr)
        return 0

    with Image.open(OUT) as im:
        w, h = im.size
    if (w, h) != (1088, 1600):
        print(f"FAIL: image is {w}x{h}, expected 1088x1600", file=sys.stderr)
        print(f"      (note: Responses API may reject custom sizes — retry with 1024x1536)", file=sys.stderr)
        return 5

    print(f"PASS: spike 02 — 1088x1600 PNG saved to {OUT}", file=sys.stderr)
    print(f"      visual sanity check: open the file and confirm", file=sys.stderr)
    print(f"      1) the reference product is recognizable", file=sys.stderr)
    print(f"      2) the Korean headline/sub-line are legible", file=sys.stderr)
    print(str(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
