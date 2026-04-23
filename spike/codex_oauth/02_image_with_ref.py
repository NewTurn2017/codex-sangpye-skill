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
SAMPLE = SPIKE_DIR / "sample_inputs" / "earbuds_01.jpg"
OUT = SPIKE_DIR / "spike02_hero.png"


def main() -> int:
    if not SAMPLE.exists():
        print(f"FAIL: sample missing at {SAMPLE}", file=sys.stderr)
        return 2

    b64 = base64.b64encode(SAMPLE.read_bytes()).decode()
    prompt = (
        "Cinematic vertical product hero, 1088x1600. "
        "Reference the uploaded product image — keep the silhouette, color, and form recognizable. "
        "Dark techwear lighting, dramatic rim light, clean background. "
        "Korean headline overlay top-center reading: '지금, 무선의 한계를 넘다'. "
        "Sub-line: '30시간 배터리 · IPX5 방수 · 액티브 노이즈 캔슬링'. "
        "Render the Korean text crisply and legibly. Premium e-commerce composition, "
        "ready to drop into a detail page."
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
