"""Unit tests for sangpye_skill.codex_client."""
from __future__ import annotations
import base64
import json
import subprocess

import pytest

from sangpye_skill.codex_client import CodexAuthError, CodexCallError, CodexClient
from tests.conftest import _completed, jsonl_image_stream, jsonl_text_stream


def test_verify_login_success(fake_login_ok):
    """Constructor returns successfully when codex login status exits 0."""
    client = CodexClient()
    assert isinstance(client, CodexClient)


def test_verify_login_raises_on_failure(fake_login_fail):
    """Constructor raises CodexAuthError when codex login status exits non-zero."""
    with pytest.raises(CodexAuthError, match="codex login"):
        CodexClient()


def test_verify_login_binary_not_found(monkeypatch):
    """Constructor raises CodexAuthError with helpful message when binary is missing."""
    def fake_run(cmd, **kw):
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(CodexAuthError, match="not found on PATH"):
        CodexClient(codex_bin="nonexistent-codex-binary-xyz")


def test_call_responses_aggregates_text(monkeypatch):
    """call_responses returns concatenated output_text AND builds a payload
    that honours all OAuth-only constraints discovered in Phase 0 spike:
    instructions top-level, store:false, stream:true.
    """
    captured = {}

    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            captured["payload"] = json.loads(kw["input"])
            return _completed(stdout=jsonl_text_stream(['{"k":', ' "v"}']))
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    out = client.call_responses(
        model="gpt-5.4",
        instructions="Return a JSON object with key k.",
        messages=[{"role": "user", "content": "give me json"}],
        response_format={"type": "json_object"},
    )
    assert out == '{"k": "v"}'
    p = captured["payload"]
    assert p["model"] == "gpt-5.4"
    assert p["instructions"] == "Return a JSON object with key k."
    assert p["stream"] is True
    assert p["store"] is False
    assert p["text"] == {"format": {"type": "json_object"}}
    assert p["input"] == [{"role": "user", "content": "give me json"}]


def test_generate_image_with_reference(tmp_path, monkeypatch):
    """generate_image_with_reference returns decoded PNG bytes and builds a payload
    that honours OAuth-only constraints: orchestrator chat model (NOT gpt-image-2),
    top-level instructions, store:false, image_generation tool + tool_choice.
    """
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    fake_b64 = base64.b64encode(b"fakepngbytes").decode()

    captured = {}

    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            captured["payload"] = json.loads(kw["input"])
            return _completed(stdout=jsonl_image_stream(fake_b64))
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    img = client.generate_image_with_reference(
        orchestrator_model="gpt-5.4",
        reference_image=ref,
        prompt="hero shot",
        size=(1088, 1600),
        quality="high",
    )
    assert img == b"fakepngbytes"

    p = captured["payload"]
    assert p["model"] == "gpt-5.4"  # orchestrator, NOT gpt-image-2
    assert "instructions" in p and len(p["instructions"]) > 0
    assert p["stream"] is True
    assert p["store"] is False
    assert p["tools"] == [{"type": "image_generation", "size": "1088x1600", "quality": "high"}]
    assert p["tool_choice"] == {"type": "image_generation"}
    content = p["input"][0]["content"]
    assert content[0]["type"] == "input_image"
    assert content[0]["image_url"].startswith("data:image/png;base64,")
    assert content[1] == {"type": "input_text", "text": "hero shot"}


def test_generate_image_with_reference_jpeg(tmp_path, monkeypatch):
    """generate_image_with_reference uses image/jpeg MIME for .jpg reference files."""
    ref = tmp_path / "product.jpg"
    ref.write_bytes(b"\xff\xd8\xff\xe0fake_jpeg")
    fake_b64 = base64.b64encode(b"fakejpegbytes").decode()

    captured = {}

    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            captured["payload"] = json.loads(kw["input"])
            return _completed(stdout=jsonl_image_stream(fake_b64))
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    img = client.generate_image_with_reference(
        orchestrator_model="gpt-5.4",
        reference_image=ref,
        prompt="product shot",
        size=(1080, 1350),
    )
    assert img == b"fakejpegbytes"

    content = captured["payload"]["input"][0]["content"]
    assert content[0]["image_url"].startswith("data:image/jpeg;base64,")


# ── Error-path tests ──────────────────────────────────────────────────────────


def test_call_responses_raises_on_subprocess_error(monkeypatch, fake_login_ok):
    """Non-zero codex exit surfaces as CodexCallError with the stderr snippet."""
    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            return _completed(returncode=1, stderr="some api error")
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="some api error"):
        client.call_responses(
            model="gpt-5.4",
            instructions="x",
            messages=[{"role": "user", "content": "x json"}],
        )


def test_call_responses_raises_on_missing_completed(monkeypatch, fake_login_ok):
    """Stream ending without response.completed → CodexCallError."""
    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            stdout = json.dumps({"type": "response.output_text.delta", "delta": "x"}) + "\n"
            return _completed(stdout=stdout)
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="response.completed"):
        client.call_responses(
            model="gpt-5.4",
            instructions="x",
            messages=[{"role": "user", "content": "x json"}],
        )


def test_generate_image_raises_on_subprocess_error(tmp_path, monkeypatch, fake_login_ok):
    """Non-zero codex exit during image gen surfaces as CodexCallError."""
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"fake")

    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            return _completed(returncode=1, stderr="rate limit")
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="rate limit"):
        client.generate_image_with_reference(
            orchestrator_model="gpt-5.4",
            reference_image=ref,
            prompt="x",
            size=(1088, 1600),
        )


def test_generate_image_raises_on_no_image_result(tmp_path, monkeypatch, fake_login_ok):
    """Stream ending without image_generation_call.result → CodexCallError."""
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"fake")

    def fake_run(cmd, **kw):
        if cmd[:3] == ["codex", "login", "status"]:
            return _completed(returncode=0)
        if cmd == ["codex", "responses"]:
            stdout = "\n".join([
                json.dumps({"type": "response.created"}),
                json.dumps({"type": "response.completed"}),
            ]) + "\n"
            return _completed(stdout=stdout)
        raise RuntimeError(f"unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="image_generation_call"):
        client.generate_image_with_reference(
            orchestrator_model="gpt-5.4",
            reference_image=ref,
            prompt="x",
            size=(1088, 1600),
        )
