"""Spike 01 — verify `codex responses` can carry multimodal text input
and return a JSON-formatted response (json_object format) for gpt-5.5
(originally validated on gpt-5.4 in Phase 0; same payload shape).

Verified against openai/codex @ rust-v0.123.0:
- Stdin = raw Responses API JSON (passthrough, `stream: true` mandatory).
- Stdout = JSONL event stream. Text is delivered as `response.output_text.delta`
  events whose `.delta` fields concatenate into the final text. There is NO
  `response.output_text.done` event — the stream terminator is `response.completed`.
"""
from __future__ import annotations
import base64
import json
import subprocess
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).parent
SAMPLE = SPIKE_DIR / "sample_inputs" / "genie.jpg"


def main() -> int:
    if not SAMPLE.exists():
        print(f"FAIL: sample missing at {SAMPLE}", file=sys.stderr)
        print(f"      drop a JPEG reference image there before running this spike", file=sys.stderr)
        return 2

    b64 = base64.b64encode(SAMPLE.read_bytes()).decode()
    payload = {
        "model": "gpt-5.5",
        "instructions": (
            "You are analyzing a reference image for a Korean marketing/promo asset. "
            "Return ONLY a single JSON object with keys: "
            "name (string — who/what is in the image), "
            "category (string — e.g. character, person, mascot, product), "
            "usp (string — one-line Korean selling hook), "
            "key_features (list of 3-5 short Korean strings — visual or personality traits). "
            "No prose, no markdown, no code fences."
        ),
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                    {"type": "input_text",
                     "text": "이 이미지를 'codex-sangpye-skill' (한국 이커머스 상세페이지 자동 생성 스킬) 홍보 자산으로 쓰기 위해 분석해줘. 지정된 4개 키만 채운 JSON 객체로 응답. JSON 외의 텍스트는 절대 포함하지 마."},
                ],
            },
        ],
        "text": {"format": {"type": "json_object"}},
        "stream": True,
        "store": False,
    }

    print(f"[spike 01] sending payload (model={payload['model']}, image={SAMPLE.name})", file=sys.stderr)
    try:
        proc = subprocess.run(
            ["codex", "responses"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        print("FAIL: `codex` not on PATH — install from https://github.com/openai/codex", file=sys.stderr)
        return 7
    except subprocess.TimeoutExpired:
        print("FAIL: `codex responses` timed out after 120s", file=sys.stderr)
        return 8

    if proc.returncode != 0:
        print(f"FAIL: codex exit={proc.returncode}", file=sys.stderr)
        print(f"STDERR:\n{proc.stderr}", file=sys.stderr)
        return 3

    # Accumulate output_text.delta events until response.completed (terminator).
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
