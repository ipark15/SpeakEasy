# SpeakEasy (SpeechScore)

An AI-powered speech assessment app that records short speech samples and generates objective, interpretable metrics on speech quality — fluency, clarity, rhythm, and pacing.

## Overview

SpeakEasy transforms raw audio into structured features and produces visual insights + actionable feedback. It is not a diagnostic tool, but a quantitative speech assessment platform for education, accessibility, and communication skills.

## Assessment Tasks

1. **Read aloud** (~10s) — articulation, clarity, voice quality
2. **Pa-ta-ka** (~8s) — rhythm regularity, DDK rate
3. **Free speech** (~20s) — fluency, filler words, prosody

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | React + Tailwind + Recharts |
| Backend | Python + FastAPI |
| ASR | faster-whisper (`base.en`) |
| Audio Features | parselmouth (Praat), librosa |
| Pronunciation | HuBERT embeddings |
| LLM Feedback | Gemma (`gemma-2-9b-it`) via Google AI Studio |
| Agents | ASI:One Agentverse (uAgents) |
| Database | Supabase |
| TTS | ElevenLabs |

## Setup

```bash
cp .env.example .env
# Fill in your API keys in .env
```

**Required keys:**
- `GEMMA_API_KEY` — Google AI Studio
- `ELEVENLABS_API_KEY` — ElevenLabs
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon/service key

**System dependency:**
```bash
brew install ffmpeg
```
