# sangpye_skill/analysis.py
"""Analysis service — single gpt-5.4 call producing ProductDNA + 5 bundle specs."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
from sangpye_skill.product_dna import ProductDNA


BundleId = Literal["B1_HERO", "B2_OPENING", "B3_SOLUTION", "B4_TRUST", "B5_ACTION"]


class SectionSpec(BaseModel):
    section_number: int
    section_name: str
    visual_language: str
    y_range: tuple[int, int]
    korean_copy: dict
    image_prompt: str


class BundleSize(BaseModel):
    width: int
    height: int


class BundleSpec(BaseModel):
    bundle_id: BundleId
    size: BundleSize
    sections: list[SectionSpec]


class ProductAnalysis(BaseModel):
    name: str
    category: str
    sub_category: str | None = None
    usp: str
    key_features: list[str] = Field(default_factory=list)
    target_persona: str | None = None
    pain_points: list[str] = Field(default_factory=list)
    tone: str
    positioning_tier: Literal["mass", "premium_indie", "luxury"]


class AnalysisPlan(BaseModel):
    product_analysis: ProductAnalysis
    product_dna: ProductDNA
    master_image_index: int = Field(ge=0)
    bundles: list[BundleSpec] = Field(min_length=5, max_length=5)
    bundle_meta_prompt: str


# ---- Service implementation continues below ----

import base64
import json
import logging
from pathlib import Path
from sangpye_skill.codex_client import CodexClient
from sangpye_skill.section_language import SECTION_LANGUAGES
from sangpye_skill.category_briefs import get_brief, CATEGORY_BRIEFS

logger = logging.getLogger(__name__)

MODEL = "gpt-5.4"
MAX_RETRIES = 2

# Concrete JSON output template — the model MUST mirror this exact shape.
OUTPUT_TEMPLATE = r"""
{{
  "product_analysis": {{
    "name": "<string>",
    "category": "<string>",
    "sub_category": null,
    "usp": "<string>",
    "key_features": ["<string>", ...],
    "target_persona": "<string>",
    "pain_points": ["<string>", ...],
    "tone": "<string>",
    "positioning_tier": "mass | premium_indie | luxury"
  }},
  "product_dna": {{
    "physical": {{
      "form": "<string>",
      "dimensions_hint": null,
      "colors": ["#RRGGBB", ...],
      "material": "<string>",
      "texture_keywords": ["<string>", ...],
      "signature_angle": null,
      "surface_details": ["<string>", ...]
    }},
    "positioning": {{
      "tier": "mass | premium_indie | luxury",
      "price_tier_hint": null,
      "tone": "<string>",
      "brand_archetype": null
    }},
    "palette": {{
      "primary": "#RRGGBB",
      "secondary": null,
      "accent": null,
      "background": "#RRGGBB",
      "text_dark": null,
      "text_light": null
    }},
    "typography_hint": {{
      "headline": "modern serif",
      "body": "clean sans",
      "tracking": null
    }},
    "visual_language": "<string>",
    "target_context": null
  }},
  "master_image_index": 0,
  "bundles": [
    {{"bundle_id": "B1_HERO",     "size": {{"width": 1088, "height": 1600}}, "sections": [
      {{"section_number": 1, "section_name": "01_hero", "visual_language": "cinematic_product_portrait", "y_range": [0, 1600], "korean_copy": {{"headline": "...", "sub": "..."}}, "image_prompt": "..."}}
    ]}},
    {{"bundle_id": "B2_OPENING",  "size": {{"width": 1088, "height": 2800}}, "sections": [
      {{"section_number": 2, "section_name": "02_pain",    "visual_language": "emotional_photography_no_product", "y_range": [0, 800],    "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 3, "section_name": "03_problem", "visual_language": "clinical_infographic",             "y_range": [800, 1600], "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 4, "section_name": "04_story",   "visual_language": "editorial_split_before_after",     "y_range": [1600,2800], "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}}
    ]}},
    {{"bundle_id": "B3_SOLUTION", "size": {{"width": 1088, "height": 3120}}, "sections": [
      {{"section_number": 5, "section_name": "05_solution", "visual_language": "product_beauty_shot",        "y_range": [0, 800],    "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 6, "section_name": "06_how",      "visual_language": "illustrated_step_sequence",  "y_range": [800, 1700], "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 7, "section_name": "07_proof",    "visual_language": "magazine_spread",            "y_range": [1700, 3120],"korean_copy": {{"headline":"..."}}, "image_prompt": "..."}}
    ]}},
    {{"bundle_id": "B4_TRUST",    "size": {{"width": 1088, "height": 2800}}, "sections": [
      {{"section_number": 8, "section_name": "08_authority", "visual_language": "portrait_with_quote",       "y_range": [0, 800],    "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 9, "section_name": "09_benefits",  "visual_language": "icon_grid_with_lifestyle",  "y_range": [800, 2000], "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 10,"section_name": "10_risk",      "visual_language": "document_with_seal",        "y_range": [2000, 2800],"korean_copy": {{"headline":"..."}}, "image_prompt": "..."}}
    ]}},
    {{"bundle_id": "B5_ACTION",   "size": {{"width": 1088, "height": 2400}}, "sections": [
      {{"section_number": 11,"section_name": "11_compare", "visual_language": "split_screen_vs",             "y_range": [0, 800],    "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 12,"section_name": "12_filter",  "visual_language": "checklist_visual",            "y_range": [800, 1500], "korean_copy": {{"headline":"..."}}, "image_prompt": "..."}},
      {{"section_number": 13,"section_name": "13_cta",     "visual_language": "urgent_product_reveal",       "y_range": [1500, 2400],"korean_copy": {{"headline":"..."}}, "image_prompt": "..."}}
    ]}}
  ],
  "bundle_meta_prompt": "<common visual direction applied across all 5 bundles>"
}}
""".strip()

SYSTEM_PROMPT = """You are a senior Korean e-commerce creative director. Your job is to analyze a product
(via reference images + a natural-language brief) and produce a COMPLETE creative plan for generating a
13-section high-conversion Korean detail page as 5 BUNDLED images.

You MUST return ONLY a single JSON object. No prose, no markdown fences — raw JSON only.

## Output JSON template — match this exact shape

Replace every "<string>" / "..." with your creative output. Keep all listed keys. Use EXACT field names.
The `master_image_index` value MUST be a plain integer (0-indexed, referring to the uploaded image list) — never a scoring object.

```
{output_template}
```

## The 13-section emotional journey
Hero → Pain → Problem → Story → Solution → How → Proof → Authority → Benefits → Risk → Compare → Filter → CTA

## Bundling plan (FIXED — do not deviate)
B1_HERO (1088×1600): Hero [y=0..1600]
B2_OPENING (1088×2800): Pain [0..800], Problem [800..1600], Story [1600..2800]
B3_SOLUTION (1088×3120): Solution [0..800], How [800..1700], Proof [1700..3120]
B4_TRUST (1088×2800): Authority [0..800], Benefits [800..2000], Risk [2000..2800]
B5_ACTION (1088×2400): Compare [0..800], Filter [800..1500], CTA [1500..2400]

## Visual Language (mandatory, per section)
Each section's image_prompt MUST reflect the named visual language.
{section_languages_block}

## Category brief (apply to product_dna + every prompt)
{category_brief_block}

## master_image_index
Pick the single BEST user-uploaded image index based on: product-centeredness, background cleanness,
resolution, signature angle fit. Return ONLY the final integer."""


def _build_system_prompt(category: str) -> str:
    langs = "\n".join(f"- {name}: {entry['label']} — {entry['rules'][:120]}…"
                      for name, entry in SECTION_LANGUAGES.items())
    brief = get_brief(category)
    return SYSTEM_PROMPT.format(
        output_template=OUTPUT_TEMPLATE,
        section_languages_block=langs,
        category_brief_block=brief,
    )


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
