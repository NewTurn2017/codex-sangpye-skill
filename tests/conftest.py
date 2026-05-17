"""Shared pytest fixtures.

The old `codex responses` subprocess path was removed in codex CLI 0.130.
Tests now stub the OAuth auth file + the urllib HTTPS call to
chatgpt.com/backend-api/codex/responses, mirroring real SSE wire format.
"""
from __future__ import annotations
import io
import json
from pathlib import Path
from typing import Iterable
from unittest.mock import MagicMock
import pytest

import sangpye_skill.codex_client as codex_client_mod


# ── auth.json fixtures ────────────────────────────────────────────────────────


def _write_auth(path: Path, *, with_tokens: bool = True) -> None:
    payload: dict = {"auth_mode": "chatgpt", "last_refresh": "2026-05-17T00:00:00Z"}
    if with_tokens:
        payload["tokens"] = {
            "access_token": "fake.jwt.token",
            "refresh_token": "fake_refresh",
            "account_id": "fake-acct-uuid",
            "id_token": "fake.id.token",
        }
    path.write_text(json.dumps(payload))


@pytest.fixture
def fake_auth_ok(tmp_path, monkeypatch):
    """Point AUTH_FILE at a temp file with a valid ChatGPT OAuth payload."""
    auth = tmp_path / "auth.json"
    _write_auth(auth, with_tokens=True)
    monkeypatch.setattr(codex_client_mod, "AUTH_FILE", auth)
    return auth


@pytest.fixture
def fake_auth_missing(tmp_path, monkeypatch):
    """Point AUTH_FILE at a path that doesn't exist."""
    monkeypatch.setattr(codex_client_mod, "AUTH_FILE", tmp_path / "missing.json")


@pytest.fixture
def fake_auth_no_tokens(tmp_path, monkeypatch):
    """auth.json exists but holds no ChatGPT tokens (e.g. API-key mode)."""
    auth = tmp_path / "auth.json"
    _write_auth(auth, with_tokens=False)
    monkeypatch.setattr(codex_client_mod, "AUTH_FILE", auth)
    return auth


# ── SSE stub fixtures ─────────────────────────────────────────────────────────


def sse_text_stream(parts: list[str]) -> bytes:
    """Build an SSE byte stream of output_text deltas terminated by response.completed."""
    blocks = [_sse_block("response.created", {"type": "response.created"})]
    for p in parts:
        blocks.append(_sse_block(
            "response.output_text.delta",
            {"type": "response.output_text.delta", "delta": p},
        ))
    blocks.append(_sse_block("response.completed", {"type": "response.completed"}))
    return ("".join(blocks)).encode("utf-8")


def sse_image_stream(b64_result: str) -> bytes:
    """Build an SSE stream containing one image_generation_call.done."""
    blocks = [
        _sse_block("response.created", {"type": "response.created"}),
        _sse_block("response.output_item.done", {
            "type": "response.output_item.done",
            "item": {"type": "image_generation_call", "result": b64_result},
        }),
        _sse_block("response.completed", {"type": "response.completed"}),
    ]
    return ("".join(blocks)).encode("utf-8")


def _sse_block(event_name: str, data_obj: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data_obj)}\n\n"


class _FakeHTTPResponse(io.BytesIO):
    """BytesIO subclass that quacks like urllib.response — iteration yields
    lines, and `.close()` is a no-op."""
    status = 200
    headers: dict[str, str] = {}

    def __enter__(self):  # contextmanager protocol (urlopen supports `with`)
        return self

    def __exit__(self, *a):  # noqa: D401
        self.close()


def patch_urlopen(monkeypatch, body: bytes, *, captured: dict | None = None,
                  status: int = 200, raise_http_error: int | None = None):
    """Patch urllib.request.urlopen used inside codex_client.

    If `captured` is supplied, the request body (parsed JSON) is stored under
    captured["payload"] and the headers under captured["headers"].
    If `raise_http_error` is set, raise urllib.error.HTTPError(<code>, ...).
    """
    import urllib.error
    import urllib.request as urllib_request

    def fake(req, timeout=None):
        if captured is not None:
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            captured["headers"] = dict(req.header_items())
            captured["url"] = req.full_url
        if raise_http_error is not None:
            raise urllib.error.HTTPError(
                req.full_url, raise_http_error, "Error",
                hdrs=None, fp=io.BytesIO(body),
            )
        resp = _FakeHTTPResponse(body)
        resp.status = status
        return resp

    monkeypatch.setattr(urllib_request, "urlopen", fake)
