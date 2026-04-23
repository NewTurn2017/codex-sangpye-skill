# Codex OAuth verification spike

Goal: prove `codex responses` (OAuth, ChatGPT subscription) can carry the three call types the `codex-sangpye-skill` pipeline needs:

1. **Multimodal text → JSON** — gpt-5.4 with an image input + `text.format = json_object`
2. **Image-to-image generation** — gpt-image-2 with an `input_image` reference + custom 1088×1600 size
3. **3 parallel calls** — concurrency under OAuth without rate-limit fatal errors

If any of the three FAIL, the `codex-sangpye-skill` project is abandoned per the design spec.

## Theme

All three spikes double as a real promo asset run: the reference image is the 지니 character, and the prompts ask for launch-banner-style assets promoting the `codex-sangpye-skill` itself. If GO, we ship the generated images as the repo's launch visuals.

## Prereqs

```bash
codex --version        # must be >= 0.121.0 (0.123.0 tested)
codex login status     # must report OAuth / ChatGPT session
echo "${CODEX_API_KEY:-<unset>}"   # must be <unset> (else it overrides OAuth)
# (OPENAI_API_KEY in shell is ignored at runtime by codex responses — no need to unset.)
```

Reference image: `sample_inputs/genie.jpg` (already present — 지니 character).

## Scripts

- `01_text_analysis.py` — Spike 1 (multimodal JSON, analyze genie as a promo asset)
- `02_image_with_ref.py` — Spike 2 (image-to-image, 1088×1600 — launch banner)
- `03_parallel_3.py` — Spike 3 (3 concurrent image calls — hero / lifestyle / feature variants)

## Run order

```bash
cd /Users/genie/dev/side/codex-sangpye-skill

# Install Pillow (needed for Spike 02 size verification)
uv sync --extra dev

# Run the three spikes sequentially (each gates the next)
uv run python spike/codex_oauth/01_text_analysis.py
uv run python spike/codex_oauth/02_image_with_ref.py
uv run python spike/codex_oauth/03_parallel_3.py
```

## Results (2026-04-23, codex-cli 0.123.0)

- [x] **Spike 1 (text + JSON):** PASS — gpt-5.4 returned a valid JSON object analyzing the 지니 character as "코덱스 상페 스킬 캐릭터" with 5 key_features in Korean.
- [x] **Spike 2 (image + ref + 1088×1600):** PASS — 2.1 MB PNG at exact size. Character recognizable, Korean launch-banner text rendered legibly. User-approved visual quality.
- [x] **Spike 3 (3 parallel):** PASS — 3/3 calls succeeded, total wall 103.5 s (individual 53.7 / 103.5 / 72.0 s), 2 informational `response.rate_limits` events per call, zero fatal errors.

## GO/NO-GO verdict

**🟢 GO** — all three spikes pass. Proceed to Phase 1+ of the implementation plan.

## Payload-shape findings (required to make `codex responses` work under ChatGPT OAuth)

These were NOT in the spec or plan — discovered during spike execution. The implementation (`codex_client.py`) must honour all of them:

1. **`instructions` is required at top level.** Putting a `role:"system"` message in `input` returns `400 {"detail":"Instructions are required"}`.
2. **`store: false` is required.** Default of `true` returns `400 {"detail":"Store must be set to false"}`.
3. **`stream: true` is required** (already noted in spec — verified).
4. **When using `text.format = json_object`, the user message MUST contain the literal word `json`** (OpenAI-level constraint, not Codex-specific). Returns `400 ... "must contain the word 'json'"` otherwise.
5. **`model: "gpt-image-2"` is rejected.** `{"detail":"The 'gpt-image-2' model is not supported when using Codex with a ChatGPT account."}` The Images Edit endpoint (`client.images.edit(...)`) does NOT exist under OAuth.
6. **Instead, use `model: "gpt-5.4"` (orchestrator) + `tools:[{type:"image_generation",...}]` + `tool_choice:{type:"image_generation"}`.** The chat model invokes the image tool. This IS allowed under ChatGPT OAuth and returns the same `response.output_item.done` / `image_generation_call.result` shape.
7. **Concurrency**: 3 parallel OAuth subprocesses complete in ~100 s (soft serialization — roughly 2 concurrent streams). Not fatal for 5 bundles. Plan-level `MAX_CONCURRENCY=3` is defensible; `MAX_CONCURRENCY=2` would have similar wall time with less rate-limit churn.

## Implications for the port

The original plan assumed the production backend's two-call shape would map 1:1: `client.responses.create(...)` for analysis and `client.images.edit(model="gpt-image-2", ...)` for bundles. The second half does not survive OAuth. The adapted mapping is:

| Production call | OAuth-compatible equivalent |
|---|---|
| `client.responses.create(model="gpt-5.4", input=[sys, user], text={"format":{"type":"json_object"}})` | `codex responses` payload: `{model:"gpt-5.4", instructions:<sys>, input:[user], text:{format:{type:"json_object"}}, stream:true, store:false}` — user text must mention "json" |
| `client.images.edit(model="gpt-image-2", image=ref, prompt=p, size="1088x1600", quality="high", n=1)` | `codex responses` payload: `{model:"gpt-5.4", instructions:<art-director-sys>, input:[{role:"user", content:[input_image, input_text(prompt)]}], tools:[{type:"image_generation", size:"1088x1600", quality:"high"}], tool_choice:{type:"image_generation"}, stream:true, store:false}` |

`codex_client.py` centralises the payload shaping; `analysis.py` and `image_generator.py` stay untouched at the pipeline level.

---

## Event-stream notes (verified against openai/codex @ rust-v0.123.0)

- `codex responses` emits a JSONL SSE-style stream on stdout.
- Text accumulation: collect `response.output_text.delta.delta` strings until `response.completed`. There is **no** `response.output_text.done` event.
- Image accumulation: on `response.output_item.done` where `item.type == "image_generation_call"`, extract `item.result` (base64 PNG).
- `stream: true` is a hard requirement — omitting it causes bail.
- `CODEX_API_KEY` overrides OAuth at runtime. `OPENAI_API_KEY` does not.
