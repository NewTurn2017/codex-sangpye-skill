# codex-productpage-skill

**Status: 🟡 Phase 0 spike in progress — unreleased.**

Korean e-commerce product detail page generator (13 sections + 1080×7500 combined image) powered by your Codex OAuth session. Designed as a Claude Code / Codex / Hermes skill installable via `uv tool install`.

## What it will produce (after Phase 0 GO)

- **13 section PNGs** at 1080×H (variable height per section): Hero → Pain → Problem → Story → Solution → How → Proof → Authority → Benefits → Risk → Compare → Filter → CTA
- **1 combined PNG** at 1080×7500 (vertical composition)
- **1 analysis.json** with Product DNA, bundle prompts, Korean copy

## Current state

The repo is currently in **Phase 0** — a verification spike under `spike/codex_oauth/` that proves `codex responses` (OAuth, ChatGPT Plus/Pro) can carry the three call types this skill needs. If any of the three spikes fail, the project is abandoned per the design spec.

Design documents (spec + implementation plan) are tracked in the source backend repository (`make-detailed-product-page`):

- Spec: `docs/superpowers/specs/2026-04-23-codex-productpage-skill-design.md`
- Plan: `docs/superpowers/plans/2026-04-23-codex-productpage-skill.md`

## Phase 0 spike layout

```
spike/codex_oauth/
├── 01_text_analysis.py     # gpt-5.4 multimodal + JSON output
├── 02_image_with_ref.py    # image-to-image, 1088×1600
├── 03_parallel_3.py        # 3 concurrent image calls
├── sample_inputs/          # user-provided product images
└── README.md               # spike results + GO/NO-GO verdict
```

## Post-Phase-0 (deferred until GO)

- `productpage_skill/` — Python package (codex_client, pipeline, analysis, image_generator, bundle_slicer, composer, product_dna, section_language, category_briefs)
- `productpage` console script — installable via `uv tool install git+...`
- `SKILL.md` — Hermes/Claude skill manifest
- `tests/` — mocked unit tests + optional live integration test

## License

MIT.
