# codex-sangpye-skill

**Status: 🟡 Phase 0 spike in progress — unreleased.**

한국 이커머스 **상세페이지(상폐)** 생성 스킬. 상품 사진 1~14장 + 한국어 프롬프트 → 13장 섹션 이미지 + 1080×7500 합성 이미지. 당신의 Codex OAuth 세션(ChatGPT Plus/Pro)을 그대로 씁니다. OpenAI API 키 불필요.

> 왜 "상폐"? 상세페이지의 한국 이커머스 업계 속어. 패션/뷰티/가전 셀러들이 다 이렇게 부릅니다.

## What it will produce (after Phase 0 GO)

- **13 section PNGs** at 1080×H (variable height per section): Hero → Pain → Problem → Story → Solution → How → Proof → Authority → Benefits → Risk → Compare → Filter → CTA
- **1 combined PNG** at 1080×7500 (vertical composition)
- **1 analysis.json** with Product DNA, bundle prompts, Korean copy

## Current state

The repo is currently in **Phase 0** — a verification spike under `spike/codex_oauth/` that proves `codex responses` (OAuth, ChatGPT Plus/Pro) can carry the three call types this skill needs. If any of the three spikes fail, the project is abandoned per the design spec.

Design documents (spec + implementation plan) are tracked in the source backend repository (`make-detailed-product-page`):

- Spec: `docs/superpowers/specs/2026-04-23-codex-productpage-skill-design.md`
- Plan: `docs/superpowers/plans/2026-04-23-codex-productpage-skill.md`

(The spec/plan were written under the working name `codex-productpage-skill` — this repo is the rename to the final shippable name `codex-sangpye-skill`.)

## Phase 0 spike layout

```
spike/codex_oauth/
├── 01_text_analysis.py     # gpt-5.4 multimodal + JSON output
├── 02_image_with_ref.py    # image-to-image, 1088×1600
├── 03_parallel_3.py        # 3 concurrent image calls
├── sample_inputs/          # reference images (genie.jpg)
└── README.md               # spike results + GO/NO-GO verdict
```

## Post-Phase-0 (deferred until GO)

- `sangpye_skill/` — Python package (codex_client, pipeline, analysis, image_generator, bundle_slicer, composer, product_dna, section_language, category_briefs)
- `sangpye` console script — installable via `uv tool install git+...`
- `SKILL.md` — Hermes/Claude skill manifest
- `tests/` — mocked unit tests + optional live integration test

## Future install (once shipped)

```bash
codex --version        # >= 0.121.0
codex login            # ChatGPT / OAuth option
unset CODEX_API_KEY    # if set, overrides OAuth
uv tool install git+https://github.com/<user>/codex-sangpye-skill
sangpye --image product.jpg --prompt "무선 이어폰..." --output ./out
```

## License

MIT.
