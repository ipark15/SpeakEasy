# SpeakEasy

AI-powered speech assessment + coaching platform. Three short tasks (~45s total) produce a scored profile across 5 dimensions, then route the user to specialized AI therapy agents for interactive coaching.

## Assessment Tasks

| Task | What it measures |
|---|---|
| **Read Aloud** (~10s) | Clarity (WER), Pronunciation (confidence), Fluency (WPM, pauses), Prosody (pitch) |
| **Pa-ta-ka** (~8s) | Rhythm (DDK rate, regularity) |
| **Free Speech** (~20s) | Fluency (WPM, fillers, pauses), Prosody (pitch + rate variation), Pronunciation (confidence) |

## Score Dimensions → Coaching Agents

| Dimension | Source | Agent |
|---|---|---|
| **Fluency** | WPM + filler rate + pause rate | Fluency Coach |
| **Clarity** | Word Error Rate vs reference sentence | Clarity Coach |
| **Rhythm** | DDK rate + inter-syllable regularity | Rhythm Coach |
| **Prosody** | Pitch std + speech rate CV | Prosody Coach |
| **Pronunciation** | Per-word Whisper confidence (+ WER blend on read_sentence) | Pronunciation Coach |

## Scoring Weights Per Task

| Task | Weights |
|---|---|
| read_sentence | clarity 40%, pronunciation 30%, fluency 20%, prosody 10% |
| pataka | rhythm 100% |
| free_speech | fluency 35%, prosody 35%, pronunciation 30% |

## Tech Stack

| Layer | Tool | Role |
|---|---|---|
| Frontend | React + Tailwind + Recharts | UI, recording, visualization |
| Backend | Python + FastAPI | Pipeline orchestration, API |
| Transcription (fast) | whisper.cpp `tiny.en` via Metal | Transcript + word timestamps |
| Transcription (confidence) | faster-whisper `tiny.en` CPU | Per-word confidence scores |
| Pitch / Voice | parselmouth (Praat) | F0 pitch, jitter, shimmer, HNR |
| Rhythm | librosa | Pa-ta-ka onset detection |
| LLM Feedback | Gemma `gemma-2-9b-it` via Google AI Studio | Per-task feedback + coaching |
| Agents | ASI:One Agentverse (uAgents) | 5 specialist coaching agents |
| Database | Supabase | Sessions, scores, chat history |
| TTS | ElevenLabs | Reads coach messages aloud |

## Setup

```bash
brew install ffmpeg whisper-cpp
pip install -r requirements.txt
cp .env.example .env   # fill in API keys
python main.py
```

**Required `.env` keys:**
```
GEMMA_API_KEY=...        # Google AI Studio
ELEVENLABS_API_KEY=...   # ElevenLabs
SUPABASE_URL=...         # Supabase project URL
SUPABASE_KEY=...         # Supabase anon key
```

## Terminal Test (no frontend needed)

```bash
.venv/bin/python test_pipeline.py
```

## API

- `POST /api/assess` — one call per task, returns scores + features
- `GET /api/health` — smoke test
