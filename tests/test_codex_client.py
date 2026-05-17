"""Unit tests for sangpye_skill.codex_client (HTTPS-direct OAuth client)."""
from __future__ import annotations
import base64
import json

import pytest

from sangpye_skill.codex_client import (
    CodexAuthError, CodexCallError, CodexClient, CHATGPT_RESPONSES_URL,
)
from tests.conftest import patch_urlopen, sse_image_stream, sse_text_stream


# ── auth.json loading ─────────────────────────────────────────────────────────


def test_init_loads_auth(fake_auth_ok):
    """Constructor succeeds and remembers token + account from auth.json."""
    client = CodexClient()
    assert client._access_token == "fake.jwt.token"
    assert client._account_id == "fake-acct-uuid"


def test_init_raises_when_auth_missing(fake_auth_missing):
    with pytest.raises(CodexAuthError, match="not found"):
        CodexClient()


def test_init_raises_when_no_tokens(fake_auth_no_tokens):
    with pytest.raises(CodexAuthError, match="no ChatGPT OAuth tokens"):
        CodexClient()


# ── call_responses: text ──────────────────────────────────────────────────────


def test_call_responses_aggregates_text(monkeypatch, fake_auth_ok):
    """call_responses concatenates output_text.delta until response.completed,
    and the wire payload still honours the OAuth-only constraints."""
    captured: dict = {}
    patch_urlopen(monkeypatch, sse_text_stream(['{"k":', ' "v"}']), captured=captured)

    client = CodexClient()
    out = client.call_responses(
        model="gpt-5.5",
        instructions="Return a JSON object with key k.",
        messages=[{"role": "user", "content": "give me json"}],
        response_format={"type": "json_object"},
    )
    assert out == '{"k": "v"}'

    p = captured["payload"]
    assert p["model"] == "gpt-5.5"
    assert p["instructions"] == "Return a JSON object with key k."
    assert p["stream"] is True
    assert p["store"] is False
    assert p["text"] == {"format": {"type": "json_object"}}
    assert p["input"] == [{"role": "user", "content": "give me json"}]

    assert captured["url"] == CHATGPT_RESPONSES_URL
    headers_lower = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers_lower["authorization"] == "Bearer fake.jwt.token"
    assert headers_lower["chatgpt-account-id"] == "fake-acct-uuid"
    assert headers_lower["oai-product-sku"] == "codex"
    assert "event-stream" in headers_lower.get("accept", "")


def test_call_responses_raises_on_http_401(monkeypatch, fake_auth_ok):
    """401 from upstream → CodexAuthError (not CodexCallError) so callers can
    route the user to `codex login`."""
    patch_urlopen(monkeypatch, b'{"detail":"expired"}', raise_http_error=401)
    client = CodexClient()
    with pytest.raises(CodexAuthError, match="HTTP 401"):
        client.call_responses(
            model="gpt-5.5", instructions="x",
            messages=[{"role": "user", "content": "x json"}],
        )


def test_call_responses_raises_on_http_500(monkeypatch, fake_auth_ok):
    patch_urlopen(monkeypatch, b'{"detail":"boom"}', raise_http_error=500)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="HTTP 500"):
        client.call_responses(
            model="gpt-5.5", instructions="x",
            messages=[{"role": "user", "content": "x json"}],
        )


def test_call_responses_raises_on_missing_completed(monkeypatch, fake_auth_ok):
    """Stream ending without response.completed → CodexCallError."""
    body = (
        b"event: response.output_text.delta\n"
        b'data: {"type":"response.output_text.delta","delta":"x"}\n\n'
    )
    patch_urlopen(monkeypatch, body)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="response.completed"):
        client.call_responses(
            model="gpt-5.5", instructions="x",
            messages=[{"role": "user", "content": "x json"}],
        )


# ── generate_image_with_reference ─────────────────────────────────────────────


def test_generate_image_with_reference(tmp_path, monkeypatch, fake_auth_ok):
    """generate_image_with_reference returns decoded PNG bytes and builds a
    payload that honours OAuth-only constraints: orchestrator chat model (NOT
    gpt-image-2), top-level instructions, store:false, image_generation tool
    + tool_choice."""
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    fake_b64 = base64.b64encode(b"fakepngbytes").decode()

    captured: dict = {}
    patch_urlopen(monkeypatch, sse_image_stream(fake_b64), captured=captured)

    client = CodexClient()
    img = client.generate_image_with_reference(
        orchestrator_model="gpt-5.5",
        reference_image=ref,
        prompt="hero shot",
        size=(1088, 1600),
        quality="high",
    )
    assert img == b"fakepngbytes"

    p = captured["payload"]
    assert p["model"] == "gpt-5.5"
    assert p["instructions"]
    assert p["stream"] is True
    assert p["store"] is False
    assert p["tools"] == [{"type": "image_generation", "size": "1088x1600", "quality": "high"}]
    assert p["tool_choice"] == {"type": "image_generation"}
    content = p["input"][0]["content"]
    assert content[0]["type"] == "input_image"
    assert content[0]["image_url"].startswith("data:image/png;base64,")
    assert content[1] == {"type": "input_text", "text": "hero shot"}


def test_generate_image_with_reference_jpeg(tmp_path, monkeypatch, fake_auth_ok):
    """JPEG reference triggers image/jpeg MIME in the data URL."""
    ref = tmp_path / "product.jpg"
    ref.write_bytes(b"\xff\xd8\xff\xe0fake_jpeg")
    fake_b64 = base64.b64encode(b"fakejpegbytes").decode()
    captured: dict = {}
    patch_urlopen(monkeypatch, sse_image_stream(fake_b64), captured=captured)

    client = CodexClient()
    img = client.generate_image_with_reference(
        orchestrator_model="gpt-5.5", reference_image=ref,
        prompt="product shot", size=(1080, 1350),
    )
    assert img == b"fakejpegbytes"
    assert captured["payload"]["input"][0]["content"][0]["image_url"].startswith(
        "data:image/jpeg;base64,"
    )


def test_generate_image_no_extension_defaults_to_png(tmp_path, monkeypatch, fake_auth_ok):
    """File without extension falls back to image/png MIME."""
    ref = tmp_path / "imagefile"
    ref.write_bytes(b"fake")
    fake_b64 = base64.b64encode(b"fakepng").decode()
    captured: dict = {}
    patch_urlopen(monkeypatch, sse_image_stream(fake_b64), captured=captured)

    CodexClient().generate_image_with_reference(
        orchestrator_model="gpt-5.5", reference_image=ref,
        prompt="x", size=(1088, 1600),
    )
    assert captured["payload"]["input"][0]["content"][0]["image_url"].startswith(
        "data:image/png;base64,"
    )


def test_generate_image_raises_on_http_500(tmp_path, monkeypatch, fake_auth_ok):
    ref = tmp_path / "ref.png"; ref.write_bytes(b"fake")
    patch_urlopen(monkeypatch, b'{"detail":"rate_limit"}', raise_http_error=500)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="HTTP 500"):
        client.generate_image_with_reference(
            orchestrator_model="gpt-5.5", reference_image=ref,
            prompt="x", size=(1088, 1600),
        )


def test_generate_image_raises_on_no_image_result(tmp_path, monkeypatch, fake_auth_ok):
    """Stream finishes without an image_generation_call.result → CodexCallError."""
    ref = tmp_path / "ref.png"; ref.write_bytes(b"fake")
    body = (
        b"event: response.created\ndata: {\"type\":\"response.created\"}\n\n"
        b"event: response.completed\ndata: {\"type\":\"response.completed\"}\n\n"
    )
    patch_urlopen(monkeypatch, body)
    client = CodexClient()
    with pytest.raises(CodexCallError, match="image_generation_call"):
        client.generate_image_with_reference(
            orchestrator_model="gpt-5.5", reference_image=ref,
            prompt="x", size=(1088, 1600),
        )
