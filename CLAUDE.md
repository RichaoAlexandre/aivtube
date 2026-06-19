# AI VTuber — Project Goal

Build an **AI VTuber from scratch**: an autonomous virtual streamer with an
animated avatar that talks, reacts to live chat, and runs live on
Twitch/YouTube — no human puppeteer.

## What it is

A real-time pipeline that turns text (live chat or self-generated thoughts)
into a *speaking, animated character* on a livestream:

```
input (live chat / voice / idle timer)
   → LLM "brain" (personality + memory)
   → TTS "voice" (low-latency speech audio)
   → Live2D avatar (audio-driven lip-sync + emotion expressions)
   → OBS → Twitch / YouTube / Kick
```

Unlike a human VTuber, lip-sync is driven by the **generated TTS audio**, not a
webcam — so no face-tracking hardware is needed.

## Reference architecture (chosen stack)

- **Brain**: Claude (latest Opus/Sonnet) via API, or local LLM via Ollama for offline.
- **Voice (TTS)**: ElevenLabs Flash v2.5 / Cartesia (cloud, low latency) or
  GPT-SoVITS / CosyVoice / Kokoro / Edge-TTS (open source).
- **Ears (ASR, optional)**: Faster-Whisper / sherpa-onnx — only if voice input wanted.
- **Face**: Live2D Cubism model rendered in a web frontend; mouth driven by audio
  amplitude/visemes; expressions set from LLM emotion tags.
- **Chat ingestion**: Twitch/YouTube chat APIs (or Social Stream Ninja for multi-platform).
- **Memory**: vector DB (RAG) / MemGPT-style for long-term persistence.
- **Streaming**: OBS Studio captures the avatar + audio, broadcasts live.
- **Orchestrator**: Python, event-driven loop deciding when to read chat vs. idle-talk.

Key inspiration: [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)
(open-source Neuro-sama-style reference) and the
[awesome-ai-vtubers](https://github.com/proj-airi/awesome-ai-vtubers) list.

## Where to start

See **PLAN.md** for the full step-by-step build plan.

## Environment notes

- Dev box is Linux. Prefer the browser/Electron Live2D renderer (no VTube Studio
  needed) since the AI drives lip-sync from audio, not a camera.
- This is a greenfield repo (not yet a git repo).
