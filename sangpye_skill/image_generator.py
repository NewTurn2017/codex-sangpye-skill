"""ImageGenerator — parallel image_generation tool calls for bundles."""
from __future__ import annotations
import asyncio
import logging
import time
from pathlib import Path
from typing import Callable, Literal
from sangpye_skill.codex_client import CodexClient

logger = logging.getLogger(__name__)

# Phase 0 spike: ChatGPT OAuth refuses direct image-model calls
# ("not supported when using Codex with a ChatGPT account").
# The image_generation tool must be invoked via a chat orchestrator model.
# codex_client.generate_image_with_reference hides the tool plumbing.
ORCHESTRATOR_MODEL = "gpt-5.4"
MAX_CONCURRENCY = 3        # 5 bundles, but tier limits may cap below 5 — set via R6 finding
MAX_RETRIES = 5
RETRY_BACKOFF_SEC = [15, 45, 90, 150, 240]
OVERLOAD_SIGNALS = ("rate_limit", "429", "overloaded", "UNAVAILABLE", "RESOURCE_EXHAUSTED")


class JobCancelled(Exception): ...


class ImageGenerator:
    def __init__(
        self,
        client: CodexClient,
        quality: Literal["standard", "high"] = "high",
    ):
        self.client = client
        self.quality = quality

    def _generate_single_bundle(
        self,
        master_image: Path,
        bundle: dict,
        cancel_check: Callable[[], bool] | None,
    ) -> bytes:
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            if cancel_check and cancel_check():
                raise JobCancelled()
            try:
                size = (bundle["size"][0], bundle["size"][1])
                # Phase 0 spike: ChatGPT OAuth rejects direct image-model calls.
                # The image_generation tool is invoked via a chat orchestrator; codex_client
                # handles the tool/tool_choice/store/stream plumbing.
                return self.client.generate_image_with_reference(
                    orchestrator_model=ORCHESTRATOR_MODEL,
                    reference_image=master_image,
                    prompt=bundle["prompt"],
                    size=size,
                    quality=self.quality,
                )
            except Exception as e:
                last_error = e
                if attempt >= MAX_RETRIES:
                    break
                err = str(e)
                is_overload = any(s in err for s in OVERLOAD_SIGNALS)
                delay = int(RETRY_BACKOFF_SEC[attempt - 1] * (1.5 if is_overload else 1))
                logger.warning("bundle %s retry %d/%d in %ds: %s",
                               bundle["bundle_id"], attempt, MAX_RETRIES, delay, e)
                t_end = time.time() + delay
                while time.time() < t_end:
                    if cancel_check and cancel_check():
                        raise JobCancelled()
                    time.sleep(max(0, min(3, t_end - time.time())))
        raise last_error or RuntimeError("bundle generation failed")

    def render_bundles_parallel(
        self,
        master_image: Path,
        bundles: list[dict],
        output_dir: Path,
        cancel_check: Callable[[], bool] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[dict]:
        """Generate all bundles concurrently (bounded by MAX_CONCURRENCY).

        Returns: [{"bundle_id": ..., "path": Path}, ...] in input order.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        sem = asyncio.Semaphore(MAX_CONCURRENCY)
        completed = [0]

        async def run_one(bundle: dict) -> dict:
            async with sem:
                img_bytes = await asyncio.to_thread(
                    self._generate_single_bundle, master_image, bundle, cancel_check
                )
                out = output_dir / f"{bundle['bundle_id']}.png"
                out.write_bytes(img_bytes)
                completed[0] += 1
                if progress_callback:
                    progress_callback(completed[0], len(bundles))
                return {"bundle_id": bundle["bundle_id"], "path": out}

        async def gather_all():
            return await asyncio.gather(*[run_one(b) for b in bundles])

        return asyncio.run(gather_all())
