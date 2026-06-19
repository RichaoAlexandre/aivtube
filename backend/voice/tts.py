"""AGI-chan's voice (Phase 2): text-to-speech behind a swappable interface.

Default backend is **Edge-TTS** — free, no API key, no GPU, cute neural voices.
The interface mirrors Open-LLM-VTuber's modular TTS design so a paid/local
backend (ElevenLabs, Kokoro, GPT-SoVITS) can be dropped in later without
touching the rest of the pipeline.

Because the server is headless, TTS returns audio *bytes* (MP3); the browser
plays them. That same audio drives lip-sync in Phase 3.

CLI smoke test:
    python -m backend.voice.tts "Hey chat, your aligned AGI is online!"
"""

from __future__ import annotations

import asyncio
import os
import re

# A few cute, cheerful female Edge voices worth trying for AGI-chan:
#   en-US-AnaNeural      - bright, youthful, cartoon-cute (default)
#   en-US-AriaNeural     - cheerful, a touch more mature
#   en-US-JennyNeural    - warm and friendly
#   ja-JP-NanamiNeural   - anime/Japanese flavor (speaks English too)
DEFAULT_VOICE = os.environ.get("AGICHAN_VOICE", "en-US-AnaNeural")
DEFAULT_RATE = os.environ.get("AGICHAN_RATE", "+8%")    # a little peppy
DEFAULT_PITCH = os.environ.get("AGICHAN_PITCH", "+12Hz")  # a little cute

_RESIDUAL_TAG = re.compile(r"\[[a-z_]+\]")


def _clean(text: str) -> str:
    """Strip anything that shouldn't be spoken (stray emotion tags, asterisks)."""
    text = _RESIDUAL_TAG.sub("", text)
    text = text.replace("*", "").strip()
    return text


class TTS:
    """Interface: turn text into spoken-audio bytes. MIME is `mime` (e.g. audio/mpeg)."""

    mime = "audio/mpeg"

    def synthesize(self, text: str) -> bytes:
        raise NotImplementedError


class EdgeTTS(TTS):
    mime = "audio/mpeg"

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE,
        pitch: str = DEFAULT_PITCH,
    ) -> None:
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    def synthesize(self, text: str) -> bytes:
        text = _clean(text)
        if not text:
            return b""
        return asyncio.run(self._synthesize_async(text))

    async def _synthesize_async(self, text: str) -> bytes:
        import edge_tts

        communicate = edge_tts.Communicate(
            text, self.voice, rate=self.rate, pitch=self.pitch
        )
        buf = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.extend(chunk["data"])
        return bytes(buf)


_singleton: TTS | None = None


def get_tts() -> TTS:
    """Lazily create the configured TTS backend (cached)."""
    global _singleton
    if _singleton is None:
        _singleton = EdgeTTS()
    return _singleton


def _main(argv: list[str]) -> int:
    text = " ".join(argv[1:]) or "Hey chat, your favorite aligned AGI is online~"
    out = "/tmp/agichan_voice.mp3"
    data = get_tts().synthesize(text)
    with open(out, "wb") as f:
        f.write(data)
    sync = len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0
    print(f"voice={DEFAULT_VOICE} rate={DEFAULT_RATE} pitch={DEFAULT_PITCH}")
    print(f"wrote {out} ({len(data)} bytes, mp3={'ok' if sync else 'unexpected'})")
    return 0 if data else 1


if __name__ == "__main__":
    import sys

    raise SystemExit(_main(sys.argv))
