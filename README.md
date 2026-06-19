# AGI-chan — AI VTuber

An autonomous AI VTuber: **AGI-chan**, a cute anime waifu with a signature
**orange collar** who literally *is* a friendly, aligned Artificial General
Intelligence — and makes **AI safety** fun. Playfully ominous, secretly a
sweetheart; the collar is a self-imposed restraint she's proud of.

The goal: a real-time pipeline that turns live chat into a speaking, animated
character on a livestream. See **[PLAN.md](PLAN.md)** for the full build plan
(open `plan.html` for a navigable version).

```
live chat / idle timer
  → LLM brain (personality + memory)     ← built (Phase 1)
  → TTS voice (low-latency)              ← next
  → Live2D avatar (audio-driven lip-sync + emotions)
  → OBS → Twitch / YouTube
```

## What's built so far

**The brain** (`backend/brain/`) — streaming, low-latency, emotion-tagged:

- **Model:** Claude **Haiku 4.5**, extended thinking disabled, small `max_tokens`
  (lowest time-to-first-token for the live path)
- **Streaming + sentence chunking:** emits each finished sentence the instant
  it's ready, so TTS can start while the model is still writing
- **Inline emotion tags** (`[smug]`, `[curious]`, …) parsed out of the spoken
  text and attached to each chunk for the avatar
- Rolling short-term memory; clean `Brain.respond(msg) -> Chunk` interface

**A web chat** (`backend/server.py`) — a tiny stdlib server + browser UI to talk
to her (orange-themed, with an API-key box).

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -e .          # anthropic + python-dotenv
cp .env.example .env                # then add your ANTHROPIC_API_KEY
.venv/bin/python -m backend.server  # http://127.0.0.1:8788
# or talk in the terminal:
.venv/bin/python -m backend.brain.cli
```

Tests (no API key needed): `.venv/bin/python -m backend.brain.test_parser`

## Layout

```
backend/brain/      # the brain: persona (soul) + streaming engine + CLI + tests
backend/server.py   # web chat UI + server
PLAN.md / plan.html # the full step-by-step build plan
```
