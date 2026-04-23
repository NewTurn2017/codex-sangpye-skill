"""Product Visual DNA — canonical product identity injected into every bundle prompt."""
from __future__ import annotations
from typing import Literal
import yaml
from pydantic import BaseModel, Field


class DNAPhysical(BaseModel):
    form: str
    dimensions_hint: str | None = None
    colors: list[str] = Field(default_factory=list)
    material: str
    texture_keywords: list[str] = Field(default_factory=list)
    signature_angle: str | None = None
    surface_details: list[str] = Field(default_factory=list)


class DNAPositioning(BaseModel):
    tier: Literal["mass", "premium_indie", "luxury"]
    price_tier_hint: str | None = None
    tone: str
    brand_archetype: str | None = None


class DNAPalette(BaseModel):
    primary: str
    secondary: str | None = None
    accent: str | None = None
    background: str
    text_dark: str | None = None
    text_light: str | None = None


class DNATypography(BaseModel):
    headline: str = "modern serif"
    body: str = "clean sans"
    tracking: str | None = None


class ProductDNA(BaseModel):
    physical: DNAPhysical
    positioning: DNAPositioning
    palette: DNAPalette
    typography_hint: DNATypography = Field(default_factory=DNATypography)
    visual_language: str
    target_context: str | None = None


def inject_dna_into_prompt(dna: ProductDNA, bundle_prompt: str) -> str:
    """Prepend the DNA YAML block as context to every bundle prompt."""
    dna_yaml = yaml.safe_dump(dna.model_dump(exclude_none=True), allow_unicode=True, sort_keys=False)
    return f"## PRODUCT DNA\n```yaml\n{dna_yaml}```\n\n{bundle_prompt}"
