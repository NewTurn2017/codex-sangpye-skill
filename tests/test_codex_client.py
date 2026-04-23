"""Unit tests for sangpye_skill.codex_client."""
from __future__ import annotations
import pytest
from sangpye_skill.codex_client import CodexClient, CodexAuthError


def test_verify_login_success(fake_login_ok):
    """Constructor returns successfully when codex login status exits 0."""
    client = CodexClient()
    assert isinstance(client, CodexClient)


def test_verify_login_raises_on_failure(fake_login_fail):
    """Constructor raises CodexAuthError when codex login status exits non-zero."""
    with pytest.raises(CodexAuthError, match="codex login"):
        CodexClient()


import json
import subprocess
from tests.conftest import jsonl_text_stream, _completed


def test_call_responses_aggregates_text(monkeypatch, fake_login_ok):
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
        input=[{"role": "user", "content": "give me json"}],
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


import base64
from tests.conftest import jsonl_image_stream


def test_generate_image_with_reference(tmp_path, monkeypatch, fake_login_ok):
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
