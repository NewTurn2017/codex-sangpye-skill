"""Subprocess wrapper around `codex responses`. Uses the user's OAuth session."""
from __future__ import annotations
import base64
import json
import mimetypes
import subprocess
from pathlib import Path


class CodexAuthError(RuntimeError):
    """Raised when `codex login status` indicates the user is not authenticated."""


class CodexCallError(RuntimeError):
    """Raised when a `codex responses` call fails or returns an unexpected payload."""


class CodexClient:
    def __init__(self, codex_bin: str = "codex", timeout_sec: int = 600):
        self.codex_bin = codex_bin
        self.timeout_sec = timeout_sec
        self._verify_login()

    def _verify_login(self) -> None:
        try:
            result = subprocess.run(
                [self.codex_bin, "login", "status"],
                capture_output=True, text=True, timeout=10,
            )
        except FileNotFoundError as e:
            raise CodexAuthError(
                f"`{self.codex_bin}` not found on PATH. Install the Codex CLI from "
                f"https://github.com/openai/codex"
            ) from e
        if result.returncode != 0:
            raise CodexAuthError(
                f"`codex login status` failed (exit={result.returncode}). "
                f"Run `codex login` first. stderr={result.stderr.strip()}"
            )

    def call_responses(
        self,
        *,
        model: str,
        instructions: str,
        messages: list[dict],
        response_format: dict | None = None,
    ) -> str:
        """Text/structured response. Returns aggregated output_text.

        Honours OAuth-only payload constraints discovered in the Phase 0 spike:
        - `instructions` is REQUIRED at top level (server 400 without it).
        - `store: false` is REQUIRED (server defaults true and rejects).
        - `stream: true` is REQUIRED.
        - When `response_format = {"type":"json_object"}`, the caller is responsible
          for ensuring the user-role messages contains the literal word "json"
          (OpenAI's own Responses API constraint, surfaced as 400).
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
        return self._run_and_extract_text(payload)

    def _run_and_extract_text(self, payload: dict) -> str:
        """Accumulate response.output_text.delta events until response.completed.

        The codex CLI (verified against openai/codex @ rust-v0.123.0 source) does
        NOT emit response.output_text.done. Terminator is response.completed.
        """
        try:
            proc = subprocess.run(
                [self.codex_bin, "responses"],
                input=json.dumps(payload),
                capture_output=True, text=True, timeout=self.timeout_sec,
            )
        except FileNotFoundError as e:
            raise CodexCallError(
                f"`{self.codex_bin}` not found on PATH (install from https://github.com/openai/codex)"
            ) from e
        if proc.returncode != 0:
            raise CodexCallError(
                f"codex responses exit={proc.returncode}: {proc.stderr.strip()[:500]}"
            )
        deltas: list[str] = []
        completed = False
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = event.get("type", "")
            if etype == "response.output_text.delta":
                deltas.append(event.get("delta", ""))
            elif etype == "response.completed":
                completed = True
                break
        if not completed:
            raise CodexCallError(
                f"stream ended without response.completed (got {len(proc.stdout)} bytes)"
            )
        return "".join(deltas)

    # Fixed art-director instructions for image calls — keeps identity of the
    # referenced subject and renders Korean text legibly. Tuned during Phase 0 spike.
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

        Phase 0 spike established that `model="gpt-image-2"` is rejected by
        ChatGPT OAuth ("not supported"). The working pattern is an orchestrator
        chat model (e.g. gpt-5.5) that invokes the image_generation tool:
        the chat model passes the reference image and prompt through to the
        tool, and the tool emits the PNG in a `response.output_item.done` event.

        Returns decoded image bytes.
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
        return self._run_and_extract_image(payload)

    def _run_and_extract_image(self, payload: dict) -> bytes:
        try:
            proc = subprocess.run(
                [self.codex_bin, "responses"],
                input=json.dumps(payload),
                capture_output=True, text=True, timeout=self.timeout_sec,
            )
        except FileNotFoundError as e:
            raise CodexCallError(
                f"`{self.codex_bin}` not found on PATH (install from https://github.com/openai/codex)"
            ) from e
        if proc.returncode != 0:
            raise CodexCallError(
                f"codex responses exit={proc.returncode}: {proc.stderr.strip()[:500]}"
            )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "response.output_item.done":
                item = event.get("item", {})
                if item.get("type") == "image_generation_call" and item.get("result"):
                    return base64.b64decode(item["result"])
        raise CodexCallError(
            f"no image_generation_call.result in stdout (got {len(proc.stdout)} bytes)"
        )
