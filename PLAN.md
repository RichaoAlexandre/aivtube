# AI VTuber — Build Plan

A step-by-step plan to build an autonomous AI VTuber that runs live, built up
from a minimal talking head to a full autonomous streamer. Each phase produces
something you can run and see/hear, so you're never building blind.

> **Guiding principle**: get a vertical slice working end-to-end *early*
> (text → speech → moving mouth on screen), then add inputs, memory, and autonomy.

---

## Phase 0 — Decisions & setup

Lock these before writing code; they shape everything downstream.

1. **Avatar type**: **Live2D (2D)** recommended to start — cheaper, lighter,
   runs on low-spec hardware, easiest lip-sync. (3D/VRM later if you want full body.)
2. **Brain**: start with a **hosted frontier LLM (Claude)** for the best
   personality with least effort; keep an **Ollama** local path as fallback/offline.
3. **TTS**: start with **Edge-TTS** (free, instant) for prototyping, plan to upgrade
   to **ElevenLabs Flash / Cartesia** (cloud, ~100ms) or **GPT-SoVITS / CosyVoice**
   (open source, voice-cloneable) for the real voice.
4. **Language/stack**: **Python** orchestrator + **web frontend** (browser) for the
   Live2D renderer. Event-driven core.
5. **Repo hygiene**: `git init`, set up a virtualenv (`uv`), `.env` for API keys,
   `.gitignore` for models/keys/audio.
6. **Decide voice-input?**: For a chat-driven streamer, ASR is optional. Skip at first.

**Deliverable**: empty project skeleton, deps installable, keys in `.env`.

---

## Phase 1 — The Brain (LLM + personality)

7. Pick an LLM client (Anthropic SDK for Claude / OpenAI-compatible / Ollama).
8. Write a **character system prompt**: name, personality, speaking style, do/don'ts,
   output constraints (short spoken lines, no markdown, inline emotion tags like
   `[happy]`, `[surprised]`).
9. Build a `brain` module: `respond(context) -> {text, emotion}`. Parse emotion tags
   out of the reply for later use by the avatar.
10. Test in a plain terminal REPL: type a message, get an in-character reply.

**Deliverable**: a CLI you can chat with that stays in character.

---

## Phase 2 — The Voice (TTS)

11. Wrap a TTS backend behind a simple `speak(text) -> audio` interface so backends
    are swappable (Edge-TTS now, ElevenLabs/GPT-SoVITS later).
12. Stream/playback audio locally; measure latency (target: speech starts <1s after
    LLM finishes; ideally stream TTS as the LLM streams tokens).
13. (Later) **Voice cloning / custom voice**: fine-tune GPT-SoVITS or use an
    ElevenLabs custom voice to give the character a unique identity.

**Deliverable**: type text → hear the character speak it.

---

## Phase 3 — The Face (Live2D avatar + lip-sync)

14. Get a **Live2D model**: buy/commission, use a free sample model, or make one in
    **Live2D Cubism** (rig art into a `.model3.json`).
15. Render it in a **web frontend** using `pixi-live2d-display` (PixiJS + Live2D
    Cubism SDK for Web). This runs in a browser/Electron — no VTube Studio needed.
16. **Audio-driven lip-sync**: feed the TTS audio's amplitude (or visemes) to the
    model's `MouthOpenY` parameter so the mouth moves while speaking.
17. **Expressions**: map the LLM emotion tags (`[happy]`, `[angry]`…) to Live2D
    expressions/motions.

**Deliverable**: avatar on screen whose mouth moves and expression changes as it speaks.

---

## Phase 4 — Wire the core loop (the vertical slice)

18. Stand up a **backend server** (FastAPI) + **WebSocket** to the frontend.
19. Flow: `input → brain → tts → {audio + emotion} → frontend plays audio + animates`.
20. Add **subtitles/captions** in the frontend (and/or to a text file for OBS).
21. Handle **interruption** and a clean speaking queue (don't overlap lines).

**Deliverable**: end-to-end — send text to the backend, watch+hear the avatar respond. This is the MVP.

---

## Phase 5 — Inputs (live chat + optional voice)

22. **Live chat ingestion**: connect to **Twitch** (IRC/EventSub) and/or **YouTube
    Live Chat API**. (Or use **Social Stream Ninja** to capture 120+ platforms via webhook.)
23. Normalize chat events into the core loop; add **selection logic** (don't reply to
    every message — pick interesting ones, batch, rate-limit).
24. **Moderation/safety filter** on both incoming chat and outgoing speech
    (block slurs, prompt-injection, doxxing; keep the character on-brand).
25. (Optional) **Voice input** via ASR (Faster-Whisper) with voice-activity detection
    and barge-in interruption — for collabs or talking to a human co-host.

**Deliverable**: avatar reads and responds to real live chat.

---

## Phase 6 — Memory & autonomy

26. **Short-term memory**: rolling conversation/chat context window.
27. **Long-term memory**: vector DB (e.g. Chroma) RAG or MemGPT-style — remember
    regulars, recurring jokes, facts about itself.
28. **Proactive / idle engine**: when chat is quiet, generate self-initiated talk
    (commentary, musings, reacting to what's on screen) so there's never dead air.
29. **Director/state machine**: decide *when* to read chat, idle-talk, run a bit, etc.
    (Neuro-sama-style: separate "talk" loop from any "play game" loop.)

**Deliverable**: avatar talks on its own, remembers things, never goes silent.

---

## Phase 7 — Going live (streaming)

30. Install **OBS Studio**. Add the avatar frontend as a **Browser Source**;
    add captions; design the scene (background, overlays, chat box).
31. **Audio routing**: route TTS audio into OBS (virtual audio cable / monitor) so it's
    captured in the broadcast.
32. Connect OBS to **Twitch / YouTube / Kick** (stream key) and do a **private test stream**.
33. Add stream furniture: starting screen, BRB, alerts (follows/subs/donations) that the
    AI can react to.

**Deliverable**: a working private livestream of the AI VTuber.

---

## Phase 8 — Polish & advanced features

34. **Singing**: separate singing voice model (voice clone / RVC) triggered on request.
35. **Vision**: let it "see" the game/screen via screenshots → multimodal LLM, and react.
36. **Mini-games / interactivity**: chat commands, polls, games it can play.
37. **Reliability**: crash recovery, watchdog, rate/cost monitoring, logging, latency budget.
38. **Persona tuning**: iterate on the system prompt + memories from real stream footage.
39. **Cost & latency optimization**: cache, stream tokens→TTS, pick cheaper models for
    low-stakes lines.

**Deliverable**: a polished, robust, entertaining autonomous streamer.

---

## Suggested repo layout

```
aivtube/
├── CLAUDE.md
├── PLAN.md
├── .env.example
├── pyproject.toml
├── backend/
│   ├── main.py            # FastAPI + WebSocket server
│   ├── brain/             # LLM client + personality + emotion parsing
│   ├── voice/             # TTS adapters (edge, elevenlabs, gptsovits…)
│   ├── ears/              # (optional) ASR adapters
│   ├── inputs/            # twitch/youtube chat ingestion
│   ├── memory/            # short + long term memory
│   ├── director/          # autonomy / idle / state machine
│   └── safety/            # moderation filters
├── frontend/              # Live2D renderer (PixiJS + pixi-live2d-display)
│   └── models/            # .model3.json avatar assets
└── obs/                   # scene notes / browser-source config
```

## Fast path vs. from scratch

- **Fastest**: clone **Open-LLM-VTuber**, swap in your model/voice/persona — running
  in a day, then customize.
- **From scratch** (this plan): more work, full control and understanding. Recommended
  to *read* Open-LLM-VTuber's code as a reference while building.

## Key references

- Open-LLM-VTuber — open-source Neuro-sama-style base: https://github.com/Open-LLM-VTuber/Open-LLM-VTuber
- awesome-ai-vtubers — curated project/tool list: https://github.com/proj-airi/awesome-ai-vtubers
- AIRI — comprehensive AI character container: (in awesome list)
- pixi-live2d-display — Live2D in the browser
- Social Stream Ninja — multi-platform chat capture
- TTS options: ElevenLabs Flash v2.5, Cartesia Sonic, GPT-SoVITS, CosyVoice, Kokoro, Edge-TTS
- ASR options: Faster-Whisper, sherpa-onnx
