"""Pipeline: analyze → render 5 bundles → slice 13 sections → compose → finalize.

Synchronous CLI variant — no Celery, no Redis, no cancel/status callbacks beyond
the user-supplied progress_callback and status_callback (wired by the CLI to
stderr printers).
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Callable, Literal

from sangpye_skill.codex_client import CodexClient
from sangpye_skill.analysis import AnalysisService
from sangpye_skill.image_generator import ImageGenerator, JobCancelled
from sangpye_skill.bundle_slicer import BundleSlicer, SectionSlice
from sangpye_skill.composer import ComposerService, SECTIONS
from sangpye_skill.product_dna import inject_dna_into_prompt

logger = logging.getLogger(__name__)


# Fixed bundle → sections mapping (mirrors AnalysisService.SYSTEM_PROMPT)
BUNDLE_SECTION_MAP: dict[str, list[tuple[str, int, int]]] = {
    "B1_HERO":     [("01_hero",      0,    1600)],
    "B2_OPENING":  [("02_pain",      0,     800),
                    ("03_problem",   800,  1600),
                    ("04_story",     1600, 2800)],
    "B3_SOLUTION": [("05_solution",  0,     800),
                    ("06_how",       800,  1700),
                    ("07_proof",     1700, 3120)],
    "B4_TRUST":    [("08_authority", 0,     800),
                    ("09_benefits",  800,  2000),
                    ("10_risk",      2000, 2800)],
    "B5_ACTION":   [("11_compare",   0,     800),
                    ("12_filter",    800,  1500),
                    ("13_cta",       1500, 2400)],
}


class PipelineService:
    def __init__(
        self,
        quality: Literal["standard", "high"] = "high",
        codex_bin: str = "codex",
    ):
        self.client = CodexClient(codex_bin=codex_bin)
        self.analysis = AnalysisService(client=self.client)
        self.generator = ImageGenerator(client=self.client, quality=quality)
        self.slicer = BundleSlicer()
        self.composer = ComposerService()

    def run(
        self,
        user_images: list[Path],
        prompt: str,
        category: str,
        output_dir: Path,
        job_id: str,
        progress_callback: Callable[[int, int], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
    ) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)

        def emit_status(status: str, step: str) -> None:
            if status_callback:
                status_callback(status, step)

        # 1) Analyze
        emit_status("analyzing", "Codex(gpt-5.4) 분석 중: 제품 DNA + 5 묶음 스펙 생성")
        logger.info("[%s] analyze", job_id)
        plan = self.analysis.build_plan(images=user_images, prompt=prompt, category=category)

        # 2) Select master
        master_idx = min(plan.master_image_index, len(user_images) - 1)
        master = user_images[master_idx]

        # 3) Build bundle prompts with DNA injection
        bundles = []
        for bundle in plan.bundles:
            prompt_body = f"{plan.bundle_meta_prompt}\n\n## BUNDLE: {bundle.bundle_id}\n"
            for sec in bundle.sections:
                prompt_body += f"\n### Section {sec.section_name} (y={sec.y_range[0]}..{sec.y_range[1]})\n"
                prompt_body += f"Visual Language: {sec.visual_language}\n"
                prompt_body += f"Image prompt: {sec.image_prompt}\n"
                prompt_body += f"Korean copy: {sec.korean_copy}\n"
            full_prompt = inject_dna_into_prompt(plan.product_dna, prompt_body)
            bundles.append({
                "bundle_id": bundle.bundle_id,
                "size": (bundle.size.width, bundle.size.height),
                "prompt": full_prompt,
            })

        # 4) Generate bundles in parallel
        emit_status("generating_images", f"이미지 생성 중: {len(bundles)}개 묶음 병렬 생성")
        bundle_dir = output_dir / "bundles"
        logger.info("[%s] render %d bundles", job_id, len(bundles))
        results = self.generator.render_bundles_parallel(
            master_image=master,
            bundles=bundles,
            output_dir=bundle_dir,
            progress_callback=progress_callback,
        )

        # 5) Slice each bundle → 13 section PNGs
        emit_status("slicing", "이미지 분할 중: 5 묶음 → 13 섹션")
        section_dir = output_dir / "sections"
        section_paths: list[Path | None] = [None] * 13
        for result in results:
            bundle_id = result["bundle_id"]
            mapping = BUNDLE_SECTION_MAP.get(bundle_id)
            if mapping is None:
                raise ValueError(
                    f"Unknown bundle_id {bundle_id!r} — not in BUNDLE_SECTION_MAP. "
                    f"Known keys: {list(BUNDLE_SECTION_MAP)}"
                )
            slices = [SectionSlice(name=name, y_start=y0, y_end=y1) for name, y0, y1 in mapping]
            crops = self.slicer.slice_and_resize(
                bundle_png=result["path"], slices=slices, output_dir=section_dir,
                target_width=1080,
            )
            for crop_path, section_info in zip(crops, mapping):
                section_name = section_info[0]
                section_num = next(
                    (i for i, s in enumerate(SECTIONS) if s["name"] == section_name),
                    None,
                )
                if section_num is not None:
                    section_paths[section_num] = crop_path

        # 6) Compose combined
        emit_status("composing", "세로 합성 중: 13 섹션 → combined.png")
        logger.info("[%s] compose", job_id)
        combined_path = output_dir / "combined.png"
        # Filter None — placeholder composer handles missing paths
        final_paths: list[Path] = [p if p else output_dir / "MISSING.png" for p in section_paths]
        self.composer.compose_vertical(final_paths, output_path=combined_path)

        return {
            "section_paths": [p for p in section_paths if p is not None],
            "combined_path": combined_path,
            "plan": plan.model_dump(),
            "master_image_index": master_idx,
            "product_dna": plan.product_dna.model_dump(),
        }
