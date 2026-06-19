"""AGI-chan's brain: streaming Claude Haiku 4.5 with sentence chunking + emotion tags.

Design goals (the live-stream latency path):
  - lowest time-to-first-token: Haiku 4.5, extended thinking DISABLED, short max_tokens.
  - speak as early as possible: stream tokens, flush complete sentences immediately
    so the TTS layer (Phase 2) can start talking while Claude is still writing.
  - emotion as inline tags ("[smug] ..."), parsed out of the spoken text and handed
    to the avatar (Phase 3); never sent to TTS.

Public surface:
    brain = Brain()
    for chunk in brain.respond("chat says: hi AGI-chan!"):
        chunk.text      # one clean spoken sentence (no tags)
        chunk.emotion   # current emotion for the avatar
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    import anthropic

DEFAULT_MODEL = os.environ.get("AGICHAN_MODEL", "claude-haiku-4-5")
DEFAULT_MAX_TOKENS = int(os.environ.get("AGICHAN_MAX_TOKENS", "200"))
HISTORY_TURNS = 20  # rolling short-term memory (user+assistant messages kept)

# A token is either an [emotion] tag or a sentence terminator.
# Mid-stream we require whitespace after the terminator (wait for the word to finish);
# on final flush we emit whatever remains.
_TOKEN_MID = re.compile(r"\[([a-z_]+)\]|[.!?~](?=\s)|\n+")
_TOKEN_END = re.compile(r"\[([a-z_]+)\]|[.!?~](?=\s|$)|\n+")


@dataclass
class Chunk:
    """One speakable unit: a clean sentence plus the emotion to show while saying it."""

    text: str
    emotion: str


class Brain:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        system_prompt: str | None = None,
        client: "anthropic.Anthropic | None" = None,
    ) -> None:
        from .persona import EMOTIONS, build_system_prompt

        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or build_system_prompt()
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self._emotions = set(EMOTIONS)
        self.history: list[dict] = []

    def reset(self) -> None:
        self.history.clear()

    def respond(self, user_message: str) -> Iterator[Chunk]:
        """Stream AGI-chan's reply as speakable, emotion-tagged sentence chunks."""
        self.history.append({"role": "user", "content": user_message})

        parser = _StreamParser(self._emotions)
        raw_reply: list[str] = []

        with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            thinking={"type": "disabled"},  # no reasoning delay on the live path
            messages=self.history,
        ) as stream:
            for delta in stream.text_stream:
                raw_reply.append(delta)
                yield from parser.feed(delta)
        yield from parser.flush()

        # Store the raw reply (tags included) so her style stays consistent.
        self.history.append({"role": "assistant", "content": "".join(raw_reply).strip()})
        self._trim_history()

    def _trim_history(self) -> None:
        if len(self.history) > HISTORY_TURNS:
            self.history = self.history[-HISTORY_TURNS:]
            # history must start on a user turn
            while self.history and self.history[0]["role"] != "user":
                self.history.pop(0)


class _StreamParser:
    """Incrementally turns a token stream into clean, emotion-tagged sentence Chunks."""

    def __init__(self, emotions: set[str]) -> None:
        self._emotions = emotions
        self._buf = ""
        self._spoken = ""
        self._emotion = "neutral"

    def feed(self, delta: str) -> Iterator[Chunk]:
        self._buf += delta
        # Only process up to an unclosed '[': a tag may be split across deltas.
        cut = self._unclosed_bracket()
        yield from self._consume(self._buf[:cut], _TOKEN_MID)
        self._buf = self._spoken + self._buf[cut:]
        self._spoken = ""

    def flush(self) -> Iterator[Chunk]:
        yield from self._consume(self._buf, _TOKEN_END)
        self._buf = ""
        tail = self._spoken.strip()
        self._spoken = ""
        if tail:
            yield Chunk(text=tail, emotion=self._emotion)

    def _consume(self, safe: str, token_re: "re.Pattern[str]") -> Iterator[Chunk]:
        """Walk `safe` left-to-right; emit a sentence at each terminator, with the
        emotion active at that point. Unflushed spoken text is left in self._spoken."""
        pos = 0
        for m in token_re.finditer(safe):
            self._spoken += safe[pos:m.start()]
            name = m.group(1)
            if name is not None:  # an [emotion] tag
                if name in self._emotions:
                    self._emotion = name
                else:  # unknown bracketed word — keep it in the spoken text
                    self._spoken += m.group(0)
            else:  # a sentence terminator (keep the punctuation)
                self._spoken += m.group(0)
                sentence = self._spoken.strip()
                self._spoken = ""
                if sentence:
                    yield Chunk(text=sentence, emotion=self._emotion)
            pos = m.end()
        self._spoken += safe[pos:]

    def _unclosed_bracket(self) -> int:
        """Index of the first '[' that has no matching ']' yet, else len(buf)."""
        i = 0
        while True:
            lb = self._buf.find("[", i)
            if lb == -1:
                return len(self._buf)
            rb = self._buf.find("]", lb)
            if rb == -1:
                return lb
            i = rb + 1
