"""Shared pytest fixtures."""
import json
import subprocess
from unittest.mock import MagicMock
import pytest


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["codex", "responses"], returncode=returncode, stdout=stdout, stderr=stderr
    )


@pytest.fixture
def fake_login_ok(monkeypatch):
    """Make `codex login status` return success."""
    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(stdout="logged in via OAuth (ChatGPT)\n", returncode=0)
        raise RuntimeError(f"unexpected subprocess call: {cmd}")
    monkeypatch.setattr(subprocess, "run", fake_run)


@pytest.fixture
def fake_login_fail(monkeypatch):
    """Make `codex login status` return failure."""
    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(stderr="not logged in\n", returncode=1)
        raise RuntimeError(f"unexpected subprocess call: {cmd}")
    monkeypatch.setattr(subprocess, "run", fake_run)


def jsonl_text_stream(parts: list[str]) -> str:
    """Build a fake JSONL stream of output_text deltas terminated by response.completed.

    NOTE: The real codex CLI does NOT emit response.output_text.done. The terminator
    is response.completed; consumers must concatenate deltas themselves.
    """
    lines = [json.dumps({"type": "response.created"})]
    for p in parts:
        lines.append(json.dumps({"type": "response.output_text.delta", "delta": p}))
    lines.append(json.dumps({"type": "response.completed"}))
    return "\n".join(lines) + "\n"


def jsonl_image_stream(b64_result: str) -> str:
    """Build a fake JSONL stream containing one image_generation_call.done."""
    return "\n".join([
        json.dumps({"type": "response.created"}),
        json.dumps({
            "type": "response.output_item.done",
            "item": {"type": "image_generation_call", "result": b64_result},
        }),
        json.dumps({"type": "response.completed"}),
    ]) + "\n"
