# Codex OAuth verification spike

Goal: prove `codex responses` (OAuth, ChatGPT subscription) can carry the three call types the codex-productpage-skill pipeline needs:

1. **Multimodal text → JSON** — gpt-5.4 with an image input + `text.format = json_object`
2. **Image-to-image generation** — gpt-image-2 with an `input_image` reference + custom 1088×1600 size
3. **3 parallel calls** — concurrency under OAuth without rate-limit fatal errors

If any of the three FAIL, the codex-productpage-skill project is abandoned per the design spec.

## Prereqs

```bash
codex --version        # must be >= rust-v0.122.0
codex login status     # must report OAuth / ChatGPT session
echo "${CODEX_API_KEY:-<unset>}"   # must be <unset> (else it overrides OAuth)
# (OPENAI_API_KEY in shell is ignored at runtime by codex responses — no need to unset.)
```

Drop a sample product image at `sample_inputs/earbuds_01.jpg` (or any JPEG 1024×1024 or larger).

## Scripts

- `01_text_analysis.py` — runs Spike 1 (multimodal JSON)
- `02_image_with_ref.py` — runs Spike 2 (image-to-image, 1088×1600)
- `03_parallel_3.py` — runs Spike 3 (3 concurrent image calls)

## Run order

```bash
cd /Users/genie/dev/side/codex-productpage-skill

# Install Pillow (needed for Spike 02 size verification)
uv sync --extra dev

# Run the three spikes sequentially (each gates the next)
uv run python spike/codex_oauth/01_text_analysis.py
uv run python spike/codex_oauth/02_image_with_ref.py
uv run python spike/codex_oauth/03_parallel_3.py
```

## Results

_Fill in after each run._

- [ ] **Spike 1 (text + JSON):** ___
- [ ] **Spike 2 (image + ref + 1088×1600):** ___
- [ ] **Spike 3 (3 parallel):** ___ (total wall: ___ s)

## GO/NO-GO verdict

_Fill in after all 3 run._

___

---

## Event-stream notes (verified against openai/codex @ rust-v0.123.0)

- `codex responses` emits a JSONL SSE-style stream on stdout.
- Text accumulation: collect `response.output_text.delta.delta` strings until `response.completed`. There is **no** `response.output_text.done` event.
- Image accumulation: on `response.output_item.done` where `item.type == "image_generation_call"`, extract `item.result` (base64 PNG).
- `stream: true` is a hard requirement — omitting it causes bail.
- `CODEX_API_KEY` overrides OAuth at runtime. `OPENAI_API_KEY` does not.
