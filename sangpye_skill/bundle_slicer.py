"""Slice a gpt-image-2 bundle PNG into individual section PNGs and resize 1088→1080."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class SectionSlice:
    name: str         # e.g., "02_pain"
    y_start: int
    y_end: int        # exclusive

    def __post_init__(self):
        if self.y_end <= self.y_start:
            raise ValueError(f"slice {self.name}: y_end ({self.y_end}) must exceed y_start ({self.y_start})")


class BundleSlicer:
    def slice_and_resize(
        self,
        bundle_png: Path,
        slices: list[SectionSlice],
        output_dir: Path,
        target_width: int = 1080,
    ) -> list[Path]:
        if not slices:
            return []
        output_dir.mkdir(parents=True, exist_ok=True)
        with Image.open(bundle_png) as bundle:
            bundle = bundle.convert("RGB")
            bw, bh = bundle.size
            out_paths: list[Path] = []
            for s in slices:
                if s.y_end > bh:
                    raise ValueError(f"slice {s.name}: y_end {s.y_end} exceeds bundle height {bh}")
                crop = bundle.crop((0, s.y_start, bw, s.y_end))
                # resize width only (1088 → 1080), preserving slice height
                if bw != target_width:
                    slice_h = s.y_end - s.y_start
                    crop = crop.resize((target_width, slice_h), Image.LANCZOS)
                out = output_dir / f"{s.name}.png"
                crop.save(out, "PNG")
                out_paths.append(out)
                logger.info("sliced %s -> %s", s.name, out)
            return out_paths
