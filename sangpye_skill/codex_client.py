"""Direct ChatGPT-backend HTTPS client for the OAuth-backed Responses API.

Codex CLI 0.130 removed the `codex responses` subcommand, so this skill no
longer shells out. Instead it reads the OAuth tokens written by
`codex login` (`~/.codex/auth.json`) and POSTs to
`https://chatgpt.com/backend-api/codex/responses` directly. The wire format
(model, instructions, input, tools, image_generation tool_choice, SSE event
stream) is unchanged from the old subcommand; only the transport moved from
subprocess+stdout to https+SSE.

Auth model: ChatGPT subscription only. No OpenAI API key is read or sent.
"""
from __future__ import annotations
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import IO, Iterable

CHATGPT_RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
AUTH_FILE = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"


class CodexAuthError(RuntimeError):
    """No usable OAuth token in ~/.codex/auth.json (or token rejected as 401)."""


class CodexCallError(RuntimeError):
    """The Responses call failed, returned an unexpected payload, or the stream
    ended without `response.completed`."""


def _load_oauth() -> tuple[str, str]:
    """Return (access_token, chatgpt_account_id) from ~/.codex/auth.json.

    Raises CodexAuthError with an actionable message if the file is missing,
    malformed, or the user is signed in with an API key instead of ChatGPT.
    """
    if not AUTH_FILE.exists():
        raise CodexAuthError(
            f"{AUTH_FILE} not found. Run `codex login` and pick the ChatGPT option."
        )
    try:
        data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise CodexAuthError(f"Cannot read {AUTH_FILE}: {e}") from e
    tokens = data.get("tokens") or {}
    access = tokens.get("access_token")
    account = tokens.get("account_id")
    if not access or not account:
        raise CodexAuthError(
            f"{AUTH_FILE} has no ChatGPT OAuth tokens "
            f"(auth_mode={data.get('auth_mode')!r}). Run `codex login` and pick "
            f"the ChatGPT/OAuth option (not the API-key option)."
        )
    return access, account


class CodexClient:
    def __init__(self, timeout_sec: int = 600):
        # `codex_bin` is intentionally NOT a parameter anymore: the codex CLI
        # is no longer invoked. We read its auth.json directly.
        self.timeout_sec = timeout_sec
        self._access_token, self._account_id = _load_oauth()

    # ── public surface ────────────────────────────────────────────────────────

    def call_responses(
        self,
        *,
        model: str,
        instructions: str,
        messages: list[dict],
        response_format: dict | None = None,
    ) -> str:
        """Text/structured Responses call. Returns aggregated output_text.

        Honours OAuth-only payload constraints inherited from the previous
        `codex responses` wire format:
        - `instructions` is REQUIRED at top level (server 400 without it).
        - `store: false` is REQUIRED (server rejects when omitted/true).
        - `stream: true` is REQUIRED on this endpoint.
        - When `response_format = {"type":"json_object"}`, the caller must
          ensure the user-role messages contain the literal word "json".
        """
        payload: dict = {
            "model": model,
            "instructions": instructions,
            "input": messages,
            "stream": True,
            "store": False,
        }
        if response_format:
            payload["text"] = {"format": response_format}
        deltas: list[str] = []
        for event in self._stream_events(payload):
            etype = event.get("type", "")
            if etype == "response.output_text.delta":
                deltas.append(event.get("delta", ""))
            elif etype == "response.completed":
                return "".join(deltas)
        raise CodexCallError("stream ended without response.completed")

    # Fixed art-director instructions for image calls — keeps identity of the
    # referenced subject and renders Korean text legibly.
    _IMAGE_INSTRUCTIONS = (
        "You are a Korean e-commerce art director. Produce a single vertical "
        "promo image at the requested size. Always preserve the identity of the "
        "referenced subject (face, form, colours) and render all Korean text "
        "crisply and legibly."
    )

    def generate_image_with_reference(
        self,
        *,
        orchestrator_model: str,    # MUST be a chat model (e.g. 'gpt-5.5'), NOT gpt-image-2
        reference_image: Path,
        prompt: str,
        size: tuple[int, int],
        quality: str = "high",
    ) -> bytes:
        """Image-to-image generation under ChatGPT OAuth.

        ChatGPT OAuth rejects `model="gpt-image-2"` directly ("not supported").
        The working pattern is an orchestrator chat model (e.g. gpt-5.5) that
        invokes the `image_generation` tool: the chat model passes the
        reference image and prompt through to the tool, and the tool emits the
        PNG inside a `response.output_item.done` event of type
        `image_generation_call` with the base64 PNG in `item.result`.
        """
        b64 = base64.b64encode(reference_image.read_bytes()).decode()
        mime = mimetypes.guess_type(reference_image.name)[0] or "image/png"
        payload = {
            "model": orchestrator_model,
            "instructions": self._IMAGE_INSTRUCTIONS,
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": f"data:{mime};base64,{b64}"},
                    {"type": "input_text", "text": prompt},
                ],
            }],
            "tools": [{"type": "image_generation", "size": f"{size[0]}x{size[1]}", "quality": quality}],
            "tool_choice": {"type": "image_generation"},
            "stream": True,
            "store": False,
        }
        for event in self._stream_events(payload):
            if event.get("type") == "response.output_item.done":
                item = event.get("item", {})
                if item.get("type") == "image_generation_call" and item.get("result"):
                    return base64.b64decode(item["result"])
            elif event.get("type") == "response.completed":
                break
        raise CodexCallError("stream ended without image_generation_call.result")

    # ── transport ─────────────────────────────────────────────────────────────

    def _stream_events(self, payload: dict) -> Iterable[dict]:
        """POST the payload, yield decoded SSE `data:` JSON objects in order.

        Stops naturally when the upstream closes the stream. Callers are
        responsible for stopping early once they have what they need
        (e.g. on `response.completed`).
        """
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "chatgpt-account-id": self._account_id,
            "OAI-Product-Sku": "codex",
            "OpenAI-Beta": "responses=v1",
        }
        req = urllib.request.Request(
            CHATGPT_RESPONSES_URL, data=body, headers=headers, method="POST"
        )
        try:
            response = urllib.request.urlopen(req, timeout=self.timeout_sec)
        except urllib.error.HTTPError as e:
            # Read body for the error surface (server returns useful JSON detail).
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            if e.code == 401:
                raise CodexAuthError(
                    f"ChatGPT OAuth rejected the request (HTTP 401). The access "
                    f"token in {AUTH_FILE} is likely expired. Run `codex login` "
                    f"to refresh. Server said: {err_body}"
                ) from e
            raise CodexCallError(
                f"responses HTTP {e.code}: {err_body}"
            ) from e
        except urllib.error.URLError as e:
            raise CodexCallError(f"responses network error: {e}") from e

        try:
            yield from _iter_sse_events(response)
        finally:
            try:
                response.close()
            except Exception:
                pass


def _iter_sse_events(stream: IO[bytes]) -> Iterable[dict]:
    """Yield each SSE `data:` JSON object as a dict, in order.

    SSE blocks are separated by blank lines; within a block, lines starting
    with `event:` give the event name (we don't need it — the JSON payload
    already includes a `type` field) and lines starting with `data:` carry the
    payload. Continuations (data: spread across multiple lines) are joined
    with newlines per the SSE spec.
    """
    data_buf: list[str] = []
    for raw in stream:
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        if line == "":
            if data_buf:
                joined = "\n".join(data_buf)
                data_buf = []
                try:
                    yield json.loads(joined)
                except json.JSONDecodeError:
                    continue
            continue
        if line.startswith(":"):
            continue  # SSE comment (heartbeat)
        if line.startswith("data:"):
            data_buf.append(line[5:].lstrip(" "))
        # We ignore `event:` / `id:` / `retry:` — the type is inside the JSON.
    # Flush a trailing data block without a final blank line (rare).
    if data_buf:
        try:
            yield json.loads("\n".join(data_buf))
        except json.JSONDecodeError:
            pass
