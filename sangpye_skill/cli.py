"""sangpye CLI — argparse entry point for the codex-sangpye-skill package."""
from __future__ import annotations
import argparse
import json
import logging
import secrets
import sys
import time
import traceback
from pathlib import Path

from sangpye_skill import __version__
from sangpye_skill.codex_client import CodexAuthError, CodexCallError
from sangpye_skill.constants import MAX_UPLOAD_IMAGES
from sangpye_skill.pipeline import PipelineService

EXIT_OK = 0
EXIT_AUTH = 1
EXIT_INPUT = 2
EXIT_API = 3
EXIT_FS = 4

CATEGORIES = ["electronics", "fashion", "food", "beauty", "home", "general"]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sangpye",
        description=(
            "Generate a 13-section Korean 상세페이지(상폐) image set (1080x12720 combined) "
            "from product photos via Codex OAuth."
        ),
    )
    p.add_argument("--version", action="version", version=f"sangpye {__version__}")
    p.add_argument(
        "--image", action="append", required=True, metavar="PATH",
        help=f"Product image path (repeat 1-{MAX_UPLOAD_IMAGES} times).",
    )
    p.add_argument("--prompt", required=True, help="Korean product brief.")
    p.add_argument("--category", choices=CATEGORIES, default="general")
    p.add_argument(
        "--output", default="./sangpye-output", metavar="DIR",
        help="Parent output directory (default: ./sangpye-output).",
    )
    p.add_argument("--quality", choices=["standard", "high"], default="high")
    p.add_argument("--job-id", default=None, help="Override the auto-generated 8-char job id.")
    p.add_argument(
        "--codex-bin", default="codex",
        help="Path to the codex CLI binary (default: codex on PATH).",
    )
    return p


def _validate_inputs(args: argparse.Namespace) -> tuple[list[Path], Path, str]:
    images = [Path(s).expanduser().resolve() for s in args.image]
    if not (1 <= len(images) <= MAX_UPLOAD_IMAGES):
        raise SystemExit(
            f"--image: must provide 1 to {MAX_UPLOAD_IMAGES} images (got {len(images)})"
        )
    for img in images:
        if not img.exists() or not img.is_file():
            raise SystemExit(f"--image: not a file: {img}")
    job_id = args.job_id or secrets.token_hex(4)
    out_root = Path(args.output).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    output_dir = out_root / job_id
    return images, output_dir, job_id


def _stderr(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    parser = _build_parser()
    args = parser.parse_args()

    try:
        images, output_dir, job_id = _validate_inputs(args)
    except SystemExit as e:
        _stderr(f"error: {e}")
        return EXIT_INPUT
    except OSError as e:
        # Covers unwritable --output paths (e.g. /root/noaccess) whose mkdir
        # lives inside _validate_inputs.
        _stderr(f"error (filesystem): {e}")
        return EXIT_FS

    _stderr("codex login status: checking...")
    try:
        pipeline = PipelineService(quality=args.quality, codex_bin=args.codex_bin)
    except CodexAuthError as e:
        _stderr(f"error: {e}")
        return EXIT_AUTH

    _stderr(f"      OK ({len(images)} image(s), job_id={job_id})")

    def on_status(status: str, step: str) -> None:
        _stderr(f"      [{status}] {step}")

    def on_progress(done: int, total: int) -> None:
        _stderr(f"      progress: {done}/{total} bundles")

    def on_event(event: dict) -> None:
        etype = event.get("type", "?")
        bid = event.get("bundle_id", "?")
        if etype == "bundle_start":
            attempt = event.get("attempt", 1)
            if attempt == 1:
                _stderr(f"        ▶ {bid} generating...")
            else:
                _stderr(f"        ▶ {bid} retry {attempt}/{event.get('max_attempts')}...")
        elif etype == "bundle_retry":
            reason = event.get("reason", "error")
            delay = event.get("delay_sec", 0)
            _stderr(f"        ⟲ {bid} {reason}, backing off {delay}s (attempt {event.get('attempt')})")
        elif etype == "bundle_done":
            _stderr(f"        ✓ {bid} done in {event.get('elapsed_sec')}s")

    t0 = time.time()
    try:
        result = pipeline.run(
            user_images=images,
            prompt=args.prompt,
            category=args.category,
            output_dir=output_dir,
            job_id=job_id,
            progress_callback=on_progress,
            status_callback=on_status,
            event_callback=on_event,
        )
    except (CodexAuthError, CodexCallError) as e:
        _stderr(f"error (codex): {e}")
        return EXIT_API
    except OSError as e:
        _stderr(f"error (filesystem): {e}")
        return EXIT_FS
    except Exception as e:
        # Developer/programming errors — still map to EXIT_API so agents have
        # a stable failure code, but dump the traceback to stderr so humans
        # can diagnose the real cause.
        _stderr(f"error (pipeline): {e}")
        _stderr(traceback.format_exc())
        return EXIT_API

    elapsed = round(time.time() - t0, 1)
    _stderr(f"Done. Total: {elapsed}s")

    # analysis.json is written eagerly by pipeline.run() right after Step 1,
    # so it survives image-gen failures. We just surface its path in the JSON.
    payload = {
        "job_id": job_id,
        "output_dir": str(output_dir),
        "combined": str(result["combined_path"]),
        "sections": [str(p) for p in result["section_paths"]],
        "plan_path": str(result["plan_path"]),
        "elapsed_sec": elapsed,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
