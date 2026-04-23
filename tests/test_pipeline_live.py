"""Live integration test — hits real codex OAuth. Marked `live`, skipped by default.

Run manually with: `uv run pytest -m live tests/test_pipeline_live.py -v`
Cost: counts against ChatGPT subscription quota (one full pipeline run).
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
import pytest
from PIL import Image

from sangpye_skill.composer import TOTAL_HEIGHT, WIDTH

REPO = Path(__file__).parent.parent
SAMPLE = REPO / "examples" / "sample_product.jpg"


@pytest.mark.live
def test_full_pipeline_via_cli(tmp_path):
    """End-to-end: run the sangpye CLI against a real codex OAuth session.

    Asserts:
    - CLI exits 0
    - Stdout's last line is valid JSON with the 6 required keys
    - combined.png exists and has dimensions WIDTH x TOTAL_HEIGHT (1080 x 12720)
    - All 13 section PNGs exist and are WIDTH pixels wide
    """
    if not SAMPLE.exists():
        pytest.skip(f"sample missing at {SAMPLE}")

    proc = subprocess.run(
        [
            sys.executable, "-m", "sangpye_skill.cli",
            "--image", str(SAMPLE),
            "--prompt", "프리미엄 무선 이어폰, ANC, 30시간 배터리. 라이브 통합 테스트.",
            "--category", "electronics",
            "--output", str(tmp_path),
            "--quality", "standard",  # cheaper for tests
        ],
        capture_output=True, text=True, timeout=900,
    )
    assert proc.returncode == 0, f"CLI failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Parse the single JSON line on stdout (last non-empty line)
    stdout_lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    result = json.loads(stdout_lines[-1])

    for key in ("job_id", "output_dir", "combined", "sections", "plan_path", "elapsed_sec"):
        assert key in result, f"missing key '{key}' in stdout JSON"
    assert len(result["sections"]) == 13, f"expected 13 sections, got {len(result['sections'])}"

    combined = Path(result["combined"])
    assert combined.exists(), f"combined.png missing at {combined}"
    with Image.open(combined) as im:
        assert im.size == (WIDTH, TOTAL_HEIGHT), (
            f"combined size = {im.size}, expected ({WIDTH}, {TOTAL_HEIGHT})"
        )

    for section_path in result["sections"]:
        p = Path(section_path)
        assert p.exists(), f"missing section {p}"
        with Image.open(p) as im:
            assert im.width == WIDTH, f"section {p.name} width = {im.width}, expected {WIDTH}"
