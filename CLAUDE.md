# SpeakEasy — Claude Context

## What This Is
AI-powered speech assessment + therapy platform. User completes a 3-task ~45s assessment, receives a scored profile across 5 dimensions, then gets routed to specialized AI therapy agents for interactive coaching. Built for a hackathon.

## Team Split
- **You**: Backend — FastAPI, feature extraction, scoring, agent definitions
- **Teammate 2**: Frontend — React + Vite + Tailwind + ZETIC
- **Teammate 3**: Gemma agent prompts, ASI:One Agentverse deployment, WebSocket integration
- **Teammate 4**: Supabase schema + auth, integration, ElevenLabs, demo/pitch

## Assessment Tasks (3 tasks, ~45s total)
1. **Read Aloud** (~10s) — `"Please call Stella and ask her to bring these things with her from the store."` → WER, WPM, pauses, pitch std, per-word confidence
2. **Pa-ta-ka** (~8s) — DDK rate, rhythm regularity
3. **Free Speech** (~20s) — WPM, fillers, pauses, pitch std, rate CV, per-word confidence

## Score Dimensions → Agents (1:1 mapping)

| Dimension | Metrics | Tasks | Agent |
|---|---|---|---|
| **Fluency** | WPM, filler rate, pause rate | read_sentence + free_speech | Fluency Coach |
| **Clarity** | WER vs reference sentence | read_sentence only | Clarity Coach |
| **Rhythm** | DDK rate + inter-syllable regularity | pataka only | Rhythm Coach |
| **Prosody** | Pitch std + speech rate CV | read_sentence (pitch only) + free_speech | Prosody Coach |
| **Pronunciation** | Per-word Whisper confidence (+ WER blend on read_sentence) | read_sentence + free_speech | Pronunciation Coach |

## Scoring Weights Per Task
- **read_sentence**: clarity 40%, pronunciation 30%, fluency 20%, prosody 10%
- **pataka**: rhythm 100%
- **free_speech**: fluency 35%, prosody 35%, pronunciation 30%

## What We Dropped
- **Sustained vowel task** — removed (voice quality metrics unreliable on consumer hardware)
- **Voice quality dimension** (jitter/shimmer/HNR) — removed from scoring (too noisy on laptop/Bluetooth mics; still extracted but not scored)
- **Speaking time ratio** — redundant with pause count, removed
- **HuBERT** — replaced by Whisper confidence scores (simpler, no 90MB model)

## Multi-Agent Therapy Team (ASI:One Agentverse)
5 uAgents hosted on Agentverse, each powered by Gemma internally. Orchestrator reads all 5 scores and routes user to the 2-3 lowest-scoring agents.

## Tech Stack
| Tool | Role | Runs where |
|---|---|---|
| whisper.cpp `tiny.en` | Fast transcript + timestamps via Metal | M2 GPU subprocess |
| faster-whisper `tiny.en` | Per-word confidence scores (parallel thread) | CPU |
| parselmouth (Praat) | Pitch, jitter, shimmer, HNR | CPU signal processing |
| librosa | DDK onset detection, RMS energy | CPU signal processing |
| Gemma `gemma-2-9b-it` | Intelligence inside each agent | Google AI Studio API |
| uAgents / ASI:One Agentverse | Agent infrastructure + messaging | Agentverse cloud |
| Supabase | Users, sessions, assessment history, chat history | Supabase cloud |
| WebSockets (FastAPI) | Real-time frontend ↔ agent relay | Backend |
| ElevenLabs | TTS — reads coach messages aloud | ElevenLabs API |
| ZETIC | Whisper in-browser (teammate) | User's browser |

## Transcription Architecture
whisper.cpp (Metal, ~0.6s) and faster-whisper (CPU, ~3-5s) run in **parallel threads**:
- whisper.cpp → transcript text + approximate word timestamps
- faster-whisper → real per-word confidence scores
- Results merged: text from cpp, confidence from faster-whisper matched by word

## Privacy Story
- Raw audio: stays on your server (or browser if ZETIC active)
- Gemma receives: anonymized numeric scores only — never raw audio or transcript
- ElevenLabs receives: text string only
- Supabase stores: scores, features, conversation history — no audio files

## API Endpoints
- `POST /api/assess` — one call per task, runs full pipeline
- `POST /api/session/start` — creates session record, returns session_id
- `GET /api/session/{session_id}` — full session data
- `WS /ws/coach/{session_id}` — real-time coach chat relay
- `POST /api/tts` — ElevenLabs TTS
- `GET /api/health` — smoke test

## Frontend Call Sequence (per assessment)
```
1. POST /api/session/start        { user_id }
   ← { session_id }

2. POST /api/assess   (task="read_sentence", audio, user_id, session_id)
   ← AssessmentResponse + session_id + assessment_id

3. POST /api/assess   (task="pataka", audio, user_id, session_id)

4. POST /api/assess   (task="free_speech", audio, user_id, session_id)
   ← session auto-marked complete server-side after this call

5. GET /api/session/{session_id}
   ← full session + all 3 assessments
```

## `/api/assess` Request Shape
```
multipart/form-data:
  audio             File    WebM/opus blob
  task              str     "read_sentence" | "pataka" | "free_speech"
  user_id           str     Supabase user ID (from supabase.auth.getUser().id)
  session_id        str     From /api/session/start
  transcript        str?    Pre-computed by ZETIC (skips faster-whisper if provided)
  word_timestamps   str?    JSON-encoded List[TranscriptWord] from ZETIC
```

## Reference Sentence
Read aloud: `"Please call Stella and ask her to bring these things with her from the store."`

## Environment Setup
```bash
brew install ffmpeg whisper-cpp
pip install -r requirements.txt
cp .env.example .env
```

## Required .env Keys
```
GEMMA_API_KEY=...        # Google AI Studio
ELEVENLABS_API_KEY=...   # ElevenLabs
SUPABASE_URL=...         # Supabase project URL
SUPABASE_KEY=...         # Supabase service role key (bypasses RLS — backend only)
```

## Running
```bash
python main.py
# or
uvicorn backend.app:app --reload --port 8000
```

## Terminal Test
```bash
.venv/bin/python test_pipeline.py
```

## Key Architectural Decisions
- **whisper.cpp + faster-whisper in parallel**: cpp for speed (Metal), fw for confidence scores — merged result
- **No voice quality agent**: jitter/shimmer/HNR are too unreliable on consumer hardware for scoring
- **WER blended into pronunciation on read_sentence**: WER is the strongest articulation signal when a reference exists
- **Prosody on read_sentence is pitch-only**: rate CV not computed for scripted reading (unnatural constraint)
- **Pataka is rhythm-only**: Whisper can't transcribe pa-ta-ka; onset detection is the only valid signal
- **FastAPI as agent bridge**: frontend never talks to Agentverse directly
- **Supabase for longitudinal context**: agents can reference past session scores to track improvement
