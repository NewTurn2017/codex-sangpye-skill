"""13 Section Visual Language templates — used by analysis to steer image_prompt per section."""
from __future__ import annotations

SECTION_LANGUAGES: dict[str, dict[str, str]] = {
    "Hero": {
        "label": "cinematic_product_portrait",
        "rules": (
            "Full-bleed cinematic hero shot. Product is the protagonist, dramatic rim light from "
            "3/4 angle. Editorial typography top-left: 72pt bold headline, 36pt subhead below. "
            "CTA capsule button on center-left. Small urgency badge top-right. Spacious layout — "
            "at least 30% negative space. Premium Korean e-commerce feel."
        ),
    },
    "Pain": {
        "label": "emotional_photography_no_product",
        "rules": (
            "Desaturated dark mood photograph or dark visual metaphor. NO product bottle — this "
            "section is about the viewer's pain, not the solution. 4 bullet-list pain points in "
            "32pt, each with small icon. Empathy-driven tone. Soft shadows, muted palette."
        ),
    },
    "Problem": {
        "label": "clinical_infographic",
        "rules": (
            "Clean infographic style on white or cream background. Subtle geometric accents. "
            "Diagram-like arrangement with 3 numbered causes (01/02/03). Possibly cross-section "
            "illustration or molecular diagram. Clear hierarchy: reversal hook headline, numbered "
            "list, closing shift. Minimal ornamentation."
        ),
    },
    "Story": {
        "label": "editorial_split_before_after",
        "rules": (
            "Split layout: left half cool-toned foggy 'before', right half warm radiant 'after'. "
            "Diagonal or soft divider. Typography straddles the divider. Before state top-left, "
            "turning-point label center, after state top-right, evidence stat as large bottom banner. "
            "Lifestyle photography, not product-centric."
        ),
    },
    "Solution": {
        "label": "product_beauty_shot",
        "rules": (
            "Studio beauty shot. Product dead-center on clean gradient or reflection surface. "
            "Perfect lighting — softboxes, subtle reflections on glass. Minimal text: product "
            "name (10자 이내), one-liner below, target fit tagline. This is the product's big reveal."
        ),
    },
    "How": {
        "label": "illustrated_step_sequence",
        "rules": (
            "3 numbered steps in horizontal or vertical flow. Each step has iconic graphic + "
            "title + short description. Arrows or connectors between steps. Clean casual tone, "
            "approachable. Result highlight at bottom. Could use illustration style not photo."
        ),
    },
    "Proof": {
        "label": "magazine_spread",
        "rules": (
            "Editorial magazine spread — asymmetric grid. Large statistics (3 stat blocks) "
            "interleaved with 3 reviewer photos + quotes. Mixed typography: bold large numbers, "
            "quoted testimonial in italic serif. Generous whitespace. Feels like a feature article."
        ),
    },
    "Authority": {
        "label": "portrait_with_quote",
        "rules": (
            "Large portrait (3/4 crop) of founder or expert, faced slight-right. Quote box overlay "
            "bottom-right with name + title + credentials. Desaturated background, warm subject "
            "lighting. Could use black-and-white for timeless authority feel."
        ),
    },
    "Benefits": {
        "label": "icon_grid_with_lifestyle",
        "rules": (
            "3×2 or 2×3 grid of benefits, each with custom icon + short label. Below or interspersed: "
            "a lifestyle photo showing product in real use. Bonus items in an accent box. Total "
            "value + offer price at bottom. Color-grouped to signal hierarchy."
        ),
    },
    "Risk": {
        "label": "document_with_seal",
        "rules": (
            "Document or certificate aesthetic. Guarantee headline top, FAQ list below in alternating "
            "background rows. Official-looking seal or badge in corner. Muted corporate palette. "
            "Goal: visually signal 'trusted, backed, safe'."
        ),
    },
    "Compare": {
        "label": "split_screen_vs",
        "rules": (
            "50/50 vertical split: left half 'without product' (muted, frustrated mood) vs right "
            "half 'with product' (bright, successful mood). Same composition structure on both sides "
            "for direct comparison. 3 points on each side. Clear VS divider."
        ),
    },
    "Filter": {
        "label": "checklist_visual",
        "rules": (
            "Two columns: 'Recommend' (green checks) and 'Not Recommend' (red X). Each list has "
            "3 target-fit statements. Simple, list-heavy layout. Almost a decision-tree feel."
        ),
    },
    "CTA": {
        "label": "urgent_product_reveal",
        "rules": (
            "Final CTA section. Hero-style product shot (can reuse Hero angle) with urgency overlay. "
            "Prominent strikethrough original price + discount price in accent color. Countdown or "
            "scarcity copy. Big CTA button. Closing tagline below button."
        ),
    },
}


def get_language_rules(section_name: str) -> str:
    """Return the rendering rules string (label prefixed) for a section, empty if unknown."""
    entry = SECTION_LANGUAGES.get(section_name)
    if not entry:
        return ""
    return f"{entry['label']} — {entry['rules']}"
