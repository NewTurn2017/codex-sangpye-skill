"""ImageGenerator — parallel image_generation tool calls for bundles."""
from __future__ import annotations
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Callable, Literal
from sangpye_skill.codex_client import CodexClient

logger = logging.getLogger(__name__)

# Phase 0 spike: ChatGPT OAuth refuses direct image-model calls
# ("not supported when using Codex with a ChatGPT account").
# The image_generation tool must be invoked via a chat orchestrator model.
# codex_client.generate_image_with_reference hides the tool plumbing.
# Default to gpt-5.5 (released 2026-04-23). Set SANGPYE_MODEL=gpt-5.4 to fall
# back during the rollout if the user's ChatGPT tier doesn't yet expose 5.5.
ORCHESTRATOR_MODEL = os.getenv("SANGPYE_MODEL", "gpt-5.5")

# Concurrency — OAuth throttles parallel image_generation calls. The Phase 0
# spike already saw 2 `response.rate_limits` events per call at concurrency 3,
# and real-world runs hit `server overloaded` retries regularly. Default is 2
# (safe under OAuth); opt into 3 via env if your ChatGPT tier allows it.
MAX_CONCURRENCY = int(os.getenv("SANGPYE_MAX_CONCURRENCY", "2"))

MAX_RETRIES = 5
# Shorter initial backoffs so a burst of overload events recovers in ~2-3 min,
# not ~14 min. Still exponential. Overload signals are multiplied by 1.5x below.
RETRY_BACKOFF_SEC = [10, 30, 60, 90, 150]
OVERLOAD_SIGNALS = (
    "rate_limit", "429", "overloaded", "server overloaded",
    "UNAVAILABLE", "RESOURCE_EXHAUSTED",
)


class JobCancelled(Exception): ...


# Event-callback helper — used by render_bundles_parallel to emit per-bundle
# lifecycle events (start/retry/done) without forcing callers to subscribe.
def _emit(event_callback: Callable[[dict], None] | None, event: dict) -> None:
    if event_callback is not None:
        try:
            event_callback(event)
        except Exception:  # noqa: BLE001 — never let a callback bug halt the pipeline
            logger.debug("event_callback raised for %s", event, exc_info=True)


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
        event_callback: Callable[[dict], None] | None = None,
    ) -> bytes:
        bundle_id = bundle["bundle_id"]
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            if cancel_check and cancel_check():
                raise JobCancelled()
            _emit(event_callback, {
                "type": "bundle_start", "bundle_id": bundle_id,
                "attempt": attempt, "max_attempts": MAX_RETRIES,
            })
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
                               bundle_id, attempt, MAX_RETRIES, delay, e)
                _emit(event_callback, {
                    "type": "bundle_retry", "bundle_id": bundle_id,
                    "attempt": attempt, "max_attempts": MAX_RETRIES,
                    "reason": "overloaded" if is_overload else "error",
                    "delay_sec": delay, "error": str(e)[:200],
                })
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
        event_callback: Callable[[dict], None] | None = None,
    ) -> list[dict]:
        """Generate all bundles concurrently (bounded by MAX_CONCURRENCY).

        Graceful partial: one bundle's permanent failure does NOT cancel the
        others. Each bundle's result dict carries either `path` (on success) or
        `error` (after MAX_RETRIES exhausted). Callers should check both.

        Returns (in input order): [
            {"bundle_id": ..., "path": Path, "elapsed_sec": float},
            {"bundle_id": ..., "path": None, "error": "...", "elapsed_sec": float},
            ...
        ]

        If `event_callback` is supplied, it receives lifecycle event dicts:
          {"type": "bundle_start",  "bundle_id": str, "attempt": int, ...}
          {"type": "bundle_retry",  "bundle_id": str, "delay_sec": int, "reason": ..., ...}
          {"type": "bundle_done",   "bundle_id": str, "elapsed_sec": float, "path": str}
          {"type": "bundle_failed", "bundle_id": str, "error": str, "elapsed_sec": float}
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        sem = asyncio.Semaphore(MAX_CONCURRENCY)
        completed = [0]

        async def run_one(bundle: dict) -> dict:
            bundle_id = bundle["bundle_id"]
            async with sem:
                t0 = time.time()
                try:
                    img_bytes = await asyncio.to_thread(
                        self._generate_single_bundle,
                        master_image, bundle, cancel_check, event_callback,
                    )
                except Exception as e:
                    # Permanent failure — after MAX_RETRIES exhausted in
                    # _generate_single_bundle. Don't cancel the siblings;
                    # report partial and let pipeline decide.
                    elapsed = round(time.time() - t0, 1)
                    completed[0] += 1
                    _emit(event_callback, {
                        "type": "bundle_failed", "bundle_id": bundle_id,
                        "error": str(e)[:300], "elapsed_sec": elapsed,
                    })
                    if progress_callback:
                        progress_callback(completed[0], len(bundles))
                    return {"bundle_id": bundle_id, "path": None,
                            "error": str(e)[:300], "elapsed_sec": elapsed}

                out = output_dir / f"{bundle_id}.png"
                out.write_bytes(img_bytes)
                completed[0] += 1
                elapsed = round(time.time() - t0, 1)
                _emit(event_callback, {
                    "type": "bundle_done", "bundle_id": bundle_id,
                    "elapsed_sec": elapsed, "path": str(out),
                })
                if progress_callback:
                    progress_callback(completed[0], len(bundles))
                return {"bundle_id": bundle_id, "path": out, "elapsed_sec": elapsed}

        async def gather_all():
            return await asyncio.gather(*[run_one(b) for b in bundles])

        return asyncio.run(gather_all())
