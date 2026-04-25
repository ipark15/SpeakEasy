# SpeechScore — Claude Context

## What This Is
AI-powered speech assessment + therapy platform. User completes a 3-task ~60s assessment, receives a scored profile, then gets routed to specialized AI therapy agents for interactive coaching. Built for a hackathon.

## Team Split
- **You**: Backend — FastAPI, feature extraction, scoring, agent definitions
- **Teammate 2**: Frontend — React + Vite + Tailwind + ZETIC
- **Teammate 3**: Gemma agent prompts, ASI:One Agentverse deployment, WebSocket integration
- **Teammate 4**: Supabase schema + auth, integration, ElevenLabs, demo/pitch

## Assessment Structure (single unified assessment)
1. **Read aloud** (10s) — `"Please call Stella and ask her to bring these things with her from the store."` → WER, articulation, jitter/shimmer/HNR
2. **Pa-ta-ka** (8s) — DDK test → DDK rate, rhythm regularity, syllable interval variance
3. **Free speech** (20s) — *"Tell me one thing you did yesterday"* → WPM, fillers, pitch variation, pauses

## Multi-Agent Therapy Team (ASI:One Agentverse)
5 uAgents hosted on Agentverse, each powered by Gemma internally:

| Agent | Triggered by |
|---|---|
| **Orchestrator** | Assessment complete — routes to coaches by score priority |
| **Rhythm Coach** | Low DDK rate / rhythm regularity |
| **Clarity Coach** | High WER / articulation issues |
| **Fluency Coach** | High filler rate / hesitations |
| **Prosody Coach** | Low pitch variation / monotone |
| **Pronunciation Coach** | Low word confidence scores |

Frontend ↔ FastAPI WebSocket ↔ Agentverse agent (FastAPI is the bridge)

## Tech Stack
| Tool | Role | Runs where |
|---|---|---|
| faster-whisper `base.en` | ASR fallback | Backend local |
| parselmouth (Praat) | Pitch, formants, jitter, shimmer, HNR | Backend local — signal processing, not a neural model |
| librosa | DDK onset detection, RMS energy | Backend local |
| Gemma `gemma-2-9b-it` | Intelligence inside each agent | Google AI Studio API |
| uAgents / ASI:One Agentverse | Agent infrastructure + messaging | Agentverse cloud |
| Supabase | Users, sessions, assessment history, chat history | Supabase cloud |
| WebSockets (FastAPI) | Real-time frontend ↔ agent relay | Backend |
| ElevenLabs | TTS — reads coach messages aloud | ElevenLabs API |
| ZETIC | Whisper in-browser (teammate) | User's browser |

## Privacy Story
- Raw audio: stays on your server (or browser if ZETIC active)
- Gemma receives: anonymized numeric features only — never raw audio or transcript
- ElevenLabs receives: text string only
- Supabase stores: scores, features, conversation history — no audio files

## API Endpoints
- `POST /api/assess` — one call per task, runs full pipeline, saves to Supabase
- `POST /api/session/start` — creates session record, returns session_id
- `GET /api/session/{session_id}` — full session data
- `WS /ws/coach/{session_id}` — real-time coach chat relay
- `POST /api/tts` — ElevenLabs TTS
- `GET /api/health` — smoke test

## `/api/assess` Request Shape
```
multipart/form-data:
  audio             File    WebM/opus blob
  task              str     "read_sentence" | "pataka" | "free_speech"
  user_id           str     Supabase user ID
  transcript        str?    Pre-computed by ZETIC (skip faster-whisper if provided)
  word_timestamps   str?    JSON-encoded List[TranscriptWord] from ZETIC
```

## Reference Sentences
- Read aloud: `"Please call Stella and ask her to bring these things with her from the store."`
- Free speech prompt: `"Tell me one thing you did yesterday."`

## Scoring Weights (single assessment)
- fluency × 0.25, clarity × 0.25, rhythm × 0.25, prosody × 0.15, voice_quality × 0.10

## Environment Setup
```bash
brew install ffmpeg
pip install -r requirements.txt
cp .env.example .env   # fill in keys below
```

## Required .env Keys
```
GEMMA_API_KEY=...        # Google AI Studio
ELEVENLABS_API_KEY=...   # ElevenLabs
SUPABASE_URL=...         # Supabase project URL
SUPABASE_KEY=...         # Supabase anon key
```

## Running the Backend
```bash
python main.py
# or
uvicorn backend.app:app --reload --port 8000
```

## Key Architectural Decisions
- **parselmouth over librosa for pitch/voice quality**: Praat gives jitter/shimmer/HNR which librosa cannot; more accurate F0 for speech
- **librosa kept for DDK**: onset_detect is better suited for pa-ta-ka rhythm analysis than Praat
- **No HuBERT**: pronunciation scored via Whisper word confidence + WER — simpler, fast, no 90MB model
- **FastAPI as agent bridge**: frontend never talks to Agentverse directly; FastAPI holds agent addresses and proxies via uAgent protocol
- **Supabase for longitudinal context**: agents can reference past session scores to track improvement
- **faster-whisper is fallback**: primary ASR path is ZETIC (browser); backend skips if transcript provided

## Full Detailed Plan
`~/.claude/plans/speechscore-is-an-ai-powered-joyful-pine.md`
