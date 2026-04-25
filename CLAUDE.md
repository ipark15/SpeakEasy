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
- `POST /api/session/start` — creates session record, returns `session_id`
- `POST /api/assess` — one call per task, runs full pipeline, saves to Supabase; auto-marks session complete after all 3 tasks
- `GET /api/session/{session_id}` — full session + all assessments
- `GET /api/dashboard/{user_id}` — trend data, streaks, goals
- `POST /api/profile` — upsert display name + goal targets
- `GET /api/export/{user_id}/csv` — downloadable CSV of all scores
- `GET /api/export/{user_id}/pdf` — PDF report (summary for general clinicians + detailed SLP table)
- `WS /ws/coach/{session_id}` — real-time coach chat relay (not yet implemented)
- `POST /api/tts` — ElevenLabs TTS (not yet implemented)
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

## `/api/assess` Response Shape (AssessmentResponse)
```json
{
  "task": "read_sentence",
  "features": { ...all FeatureResult fields... },
  "scores": { "fluency": 72.0, "clarity": 85.0, ..., "overall": 79.0 },
  "feedback": "",
  "tips": [],
  "audio_duration": 9.8,
  "session_id": "uuid",
  "assessment_id": "uuid"
}
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
SUPABASE_KEY=...         # Supabase service role key (bypasses RLS — backend only)
```

## Supabase Schema
4 tables — run `backend/db/schema.sql` once in the Supabase SQL Editor to create them.

| Table | Purpose |
|---|---|
| `sessions` | One per 3-task assessment run. Tracks status + composite score. |
| `assessments` | One per task per session. All features + scores + feedback. |
| `coach_messages` | Chat history with therapy agents (role: user/assistant). |
| `user_profiles` | Display name + per-metric goal targets (JSONB). |

RLS enabled on all tables — users see only their own rows. Backend uses service role key to bypass RLS.

## DB Query Functions (`backend/db/queries.py`)
- `create_session(user_id)` → `session_id`
- `save_assessment(session_id, user_id, response)` → `assessment_id`
- `complete_session(session_id, overall_score)`
- `get_session(session_id)` → session + assessments
- `save_coach_message(session_id, user_id, agent_type, role, content)`
- `get_coach_history(session_id)`
- `upsert_profile(user_id, display_name, goals)`
- `get_profile(user_id)`
- `get_dashboard_data(user_id)` → sessions, assessments, streaks, goals

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

## Frontend Notes
- Supabase anon/publishable key is safe for the browser (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`)
- Service role key stays server-side only — never expose in frontend
- `user_id` = `supabase.auth.getUser()` → `user.id`
- ZETIC handles in-browser Whisper; passes `transcript` + `word_timestamps` to `/api/assess` so backend skips faster-whisper

## Dashboard & Export (future UI)
- Trend lines, streaks, goals fed by `GET /api/dashboard/{user_id}`
- PDF export = two sections: summary (general clinician) + detailed SLP table
- CSV export = one row per assessment with all scalar metrics

## Full Detailed Plan
`~/.claude/plans/speechscore-is-an-ai-powered-joyful-pine.md`
`~/.claude/plans/also-we-want-to-synthetic-kahan.md` (dashboard + export plan)
