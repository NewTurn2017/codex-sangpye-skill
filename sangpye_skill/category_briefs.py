"""10 Category Visual Brief templates — injected into analysis prompt based on user-selected category."""
from __future__ import annotations

CATEGORY_BRIEFS: dict[str, dict[str, str]] = {
    "electronics": {
        "lighting": "studio softbox + rim light, cool color temperature 5600K, controlled shadows",
        "composition": "geometric, symmetrical, tech grid overlays subtle, rule of thirds for product",
        "palette": "deep navy, warm silver, single neon accent (cyan or orange), black as space",
        "typography": "geometric sans-serif, wide tracking, all caps for CTAs, monospace for specs",
        "props": "minimal — cables abstracted, reflective surfaces, circuit patterns as background texture",
        "model": "rare; product is hero; hand-with-device shots acceptable for How/Benefits",
        "mood": "confident, precise, innovative, slightly futuristic",
    },
    "fashion": {
        "lighting": "natural window light, editorial styling; golden hour for outdoor lifestyle",
        "composition": "asymmetric, rule of thirds, lots of negative space, vertical flow",
        "palette": "blush pink, cream, muted gold, single strong editorial accent (emerald or rust)",
        "typography": "modern serif (Didone) for headlines, light sans for body, relaxed tracking",
        "props": "silk fabric drape, marble surfaces, single botanical stem, hangers for context",
        "model": "body/face crop acceptable, Korean 20s–30s, natural un-retouched feel",
        "mood": "aspirational, clean, modern-editorial",
    },
    "food": {
        "lighting": "golden hour warm; top-down hero shots; rustic shadow play",
        "composition": "top-down 45° hero shots, overhead flat-lays, tight product macro for texture",
        "palette": "warm cream, wood brown, muted green, terracotta accent, amber highlights",
        "typography": "slab-serif or warm serif for headlines, hand-lettered accents OK",
        "props": "linen napkin, wooden cutting board, ceramic plates, fresh ingredients scattered",
        "model": "hands-in-action for preparing/serving; lifestyle human presence welcome",
        "mood": "warm, abundant, appetizing, hand-crafted",
    },
    "beauty": {
        "lighting": "soft diffuse daylight with fill; golden hour for lifestyle; never harsh",
        "composition": "rule of thirds, generous negative space, vertical flow, product in dead-center for Solution",
        "palette": "blush pink, cream, muted gold, pale green, single editorial accent coral",
        "typography": "modern serif (Didone) for headlines, light sans for body, luxury feel",
        "props": "silk fabric drape, marble surface, water/glass droplets, botanical elements, clean glass",
        "model": "hand + face crops, Korean women 20s–30s, radiant natural skin, subtle makeup",
        "mood": "radiant, clean, aspirational, luxe-feeling but approachable",
    },
    "home": {
        "lighting": "ambient evening warm light; soft daylight from windows; candlelit accents",
        "composition": "lifestyle interiors, product-in-context, rule of thirds, human presence OK",
        "palette": "neutral beige, warm white, charcoal, wood tones, single earthy accent (sage or terracotta)",
        "typography": "modern serif or friendly sans, generous line height, cozy feel",
        "props": "linen textiles, plants, ceramics, books, warm wood furniture",
        "model": "people enjoying the space, hands interacting with product",
        "mood": "calm, cozy, intentional, lived-in",
    },
    "supplement": {
        "lighting": "clean clinical softbox with warm secondary; spotlight on product",
        "composition": "symmetric, centered product, lab-notes aesthetic, illustrated molecular diagrams",
        "palette": "clean white, navy medical, warm honey accent, safety green for certifications",
        "typography": "clean sans-serif for body, serif for headlines, monospace for lab specs",
        "props": "glass test tube accent, certification badges, ingredient illustration vignettes",
        "model": "hands holding capsules, professional context OK, not overly clinical",
        "mood": "trustworthy, scientific, warm-credible, not cold pharma",
    },
    "pet": {
        "lighting": "playful warm daylight, natural sun, soft shadows",
        "composition": "pet-in-action, low-angle shots, diagonal motion, product usage context",
        "palette": "pastel peach, sky blue, soft yellow, warm cream, tan accent",
        "typography": "rounded sans-serif, friendly slightly bouncy, generous spacing",
        "props": "toys, blankets, pet beds, natural outdoor environments, home interiors",
        "model": "the pet is the primary model; owners' hands acceptable for Benefits/How",
        "mood": "joyful, caring, heart-warming, domestic",
    },
    "kids": {
        "lighting": "bright saturated daylight, no dark moods, warm direct sun OK",
        "composition": "playful asymmetric, large friendly shapes, kid-at-play contexts, safe spaces",
        "palette": "bright primary-adjacent (coral, aqua, sunny yellow), white base, no neons",
        "typography": "large rounded sans (Nunito-like), hand-drawn accents, minimal small text",
        "props": "soft toys, blocks, art supplies, bright furniture, bedroom/playroom contexts",
        "model": "child hands/legs/back-of-head acceptable, parents hands OK; safe staging",
        "mood": "safe, bright, playful, nurturing — never dark or anxious",
    },
    "handmade": {
        "lighting": "warm honey natural light, single directional source, long soft shadows",
        "composition": "artisan's hands in action, tools visible, in-progress work, rule of thirds",
        "palette": "natural linen, warm walnut, honey gold, forest green accent, earthy neutrals",
        "typography": "slab-serif headlines, hand-lettered accents OK, letterpress feel",
        "props": "hand tools, workbench wood grain, linen cloth, raw materials visible",
        "model": "artisan's hands prominent; back-of-head acceptable; focus on craft",
        "mood": "warm, authentic, intentional, imperfection-as-feature",
    },
    "general": {
        "lighting": "clean balanced studio lighting, soft softbox, product-focused",
        "composition": "modern minimal, clean white background, single accent, center composition",
        "palette": "clean white, charcoal, single bold brand accent color, minimal secondary",
        "typography": "modern sans-serif for everything, occasional serif accent, tight tracking",
        "props": "minimal — only what's necessary; product speaks for itself",
        "model": "rare; only where clearly necessary",
        "mood": "clean, confident, adaptable, modern",
    },
}


def get_brief(category: str) -> str:
    """Return the Visual Brief string for a category. Falls back to 'general' for unknown."""
    entry = CATEGORY_BRIEFS.get(category) or CATEGORY_BRIEFS["general"]
    return "\n".join(f"- {k}: {v}" for k, v in entry.items())
