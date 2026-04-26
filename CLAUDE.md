# SpeakEasy — Claude Context

## What This Is
AI-powered speech assessment + coaching platform. User completes a 3-task ~45s assessment, receives a scored profile across 6 dimensions, then gets routed to specialized AI coaching agents for interactive practice. Built for a hackathon.

## Team Split
- **You (Isaiah)**: Backend — FastAPI, feature extraction, scoring, agent definitions, DB
- **Teammate 2**: Frontend — React + Vite + Tailwind
- **Teammate 3**: Gemma agent prompts, ASI:One Agentverse deployment, WebSocket integration
- **Teammate 4**: Supabase schema + auth, integration, ElevenLabs, demo/pitch

## Assessment Tasks (3 tasks, ~45s total)
1. **Read Aloud** (~10s) — `"Please call Stella and ask her to bring these things with her from the store."` → WER, WPM, pauses, pitch std, per-word confidence
2. **Pa-ta-ka** (~8s) — DDK rate, rhythm regularity, voice quality
3. **Free Speech** (~20s) — WPM, fillers, pauses, pitch std, rate CV, per-word confidence, voice quality

## Score Dimensions → Agents

| Dimension | Metrics | Tasks | Agent |
|---|---|---|---|
| **Fluency** | WPM, filler rate, pause rate | read_sentence + free_speech | Fluency Coach |
| **Clarity** | WER vs reference sentence | read_sentence only | Clarity Coach |
| **Rhythm** | DDK rate + inter-syllable regularity | pataka only | Rhythm Coach |
| **Prosody** | Pitch std + speech rate CV | read_sentence (pitch only) + free_speech | Prosody Coach |
| **Pronunciation** | Per-word Whisper confidence (+ WER blend on read_sentence) | read_sentence + free_speech | Pronunciation Coach |
| **Voice Quality** | Jitter + shimmer + HNR via parselmouth | all tasks | (contributes to overall; no dedicated coach) |

## Scoring Weights Per Task
- **read_sentence**: clarity 35%, pronunciation 25%, fluency 20%, prosody 10%, voice_quality 10%
- **pataka**: rhythm 85%, voice_quality 15%
- **free_speech**: fluency 30%, prosody 28%, pronunciation 25%, voice_quality 17%

Implemented in `backend/services/scoring.py` — `_WEIGHTS` dict.

## Multi-Agent System (ASI:One Agentverse)
6 uAgents in `backend/agents/`: orchestrator + 5 specialized coaches (fluency, clarity, rhythm, prosody, pronunciation). Orchestrator reads scores, generates Gemma narrative, and produces the clinical PDF report.

## Tech Stack
| Tool | Role | Runs where |
|---|---|---|
| whisper.cpp `tiny.en` | Fast transcript + timestamps via Metal | M2 GPU subprocess |
| faster-whisper `tiny.en` | Per-word confidence scores (parallel thread) | CPU |
| parselmouth (Praat) | Pitch, jitter, shimmer, HNR | CPU signal processing |
| librosa | DDK onset detection, RMS energy | CPU signal processing |
| pydub + ffmpeg | Decode WebM/opus from browser | CPU |
| Gemma via Google AI Studio | Narrative generation inside agents | Google AI Studio API |
| uAgents / ASI:One Agentverse | Agent infrastructure + messaging | Agentverse cloud |
| ReportLab + matplotlib | Clinical PDF report generation | Backend |
| Supabase | Users, sessions, assessments, chat history, reports | Supabase cloud |
| Supabase Storage | WAV audio file storage (bucket: `audio`) | Supabase cloud |
| WebSockets (FastAPI) | Real-time frontend ↔ agent relay | Backend |
| ElevenLabs | TTS — reads coach messages aloud | ElevenLabs API |

## Audio Pipeline
Browser records via Web Audio API → raw PCM → resampled to 16kHz in-browser → WAV blob → sent to backend.

`bytes_to_array()` in `backend/utils/audio.py`: pydub decodes the WAV, then **librosa** resamples to 16kHz using a high-quality sinc filter (same as `test_pipeline.py`). Avoids pydub's low-quality resampler which caused muffled/distorted output.

## Transcription Architecture
whisper.cpp (Metal, ~0.6s) and faster-whisper (CPU, ~3-5s) run in **parallel threads**:
- whisper.cpp → transcript text + approximate word timestamps
- faster-whisper → real per-word confidence scores
- Results merged: text from cpp, confidence from faster-whisper matched by word
Falls back to pure faster-whisper if `whisper-cli` binary or model not found.

## Privacy Story
- Raw audio: stored in Supabase Storage (bucket: `audio`, private) keyed by `session_id/task.wav`
- Gemma receives: anonymized numeric scores + features only — never raw audio
- ElevenLabs receives: text string only
- Supabase stores: scores, features, transcripts, audio URLs, report summaries

## API Endpoints

### Assessment
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/session/start` | Create session, returns `session_id` |
| `POST` | `/api/assess` | Submit audio for one task, runs full pipeline, saves to DB |
| `GET` | `/api/session/{session_id}` | Full session + all 3 assessments (with nested `scores` object) |
| `POST` | `/api/assess_drill` | Single drill recording scored across all dimensions — used by coach agents |
| `GET` | `/api/report/{session_id}` | Generate (or serve cached) clinical PDF via Gemma + ReportLab |

### Dashboard / History / Profile
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/dashboard/{user_id}` | Streak, avg score, weekly chart, recent sessions |
| `GET` | `/api/history/{user_id}` | Last 20 sessions with per-dimension sub-scores |
| `GET` | `/api/profile/{user_id}` | Display name, joined date, best score, improvement |
| `POST` | `/api/profile` | Upsert display name + goal targets |
| `GET` | `/api/reports/{user_id}` | List sessions that have generated PDF reports |

### Export
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/export/{user_id}/csv` | All assessments as CSV |
| `GET` | `/api/export/{user_id}/pdf` | Summary PDF (ReportLab, no Gemma) |

### Utility
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Smoke test |
| `WS` | `/ws/coach/{session_id}` | Real-time coach chat relay |

## Frontend Routes
```
/                    Landing (marketing page)
/auth                Sign in / Sign up
/dashboard           Main hub after login
/assess              3-task assessment flow
/results/:sessionId  Scores + breakdown + report download
/coach               Coach selection grid
/coach/:type         Live coaching session (WebSocket)
/history             Past sessions with sub-scores + report buttons
/profile             User profile + stats + name edit
/settings            Preferences + sign out
/settings/data       Data & privacy
```

## Frontend Call Sequence (per assessment)
```
1. POST /api/session/start  { user_id }
   ← { session_id }

2. POST /api/assess  (task="read_sentence", audio WAV, user_id, session_id)
   ← AssessmentResponse

3. POST /api/assess  (task="pataka", ...)

4. POST /api/assess  (task="free_speech", ...)
   ← session auto-marked complete + overall_score computed server-side

5. GET /api/session/{session_id}
   ← full session + assessments (each with nested scores object)
```

## `/api/assess` Request Shape
```
multipart/form-data:
  audio             File    WAV blob (16kHz PCM, from Web Audio API in browser)
  task              str     "read_sentence" | "pataka" | "free_speech"
  user_id           str     Supabase user ID
  session_id        str     From /api/session/start
  transcript        str?    Pre-computed transcript (skips Whisper if provided)
  word_timestamps   str?    JSON-encoded List[TranscriptWord]
```

## Database Tables
Run `backend/db/schema.sql` once in Supabase SQL Editor.

| Table | Purpose |
|---|---|
| `sessions` | One per 3-task run. Tracks status + composite overall_score. |
| `assessments` | One per task per session. All features + scores + feedback + `audio_url`. |
| `user_profiles` | Display name + per-metric goal targets (JSONB). |
| `coach_messages` | Chat history with coaching agents (role: user/assistant). |
| `reports` | One per generated clinical PDF: session_id, user_id, pdf_path, summary. |

**Supabase Storage**: bucket `audio` (private) — stores `{session_id}/{task}.wav` for each assessment.

**New columns to add to existing DB** (if schema was already run before):
```sql
alter table assessments add column if not exists audio_url text;
```

## DB Query Functions (`backend/db/queries.py`)
- `create_session(user_id)` → `session_id`
- `save_assessment(session_id, user_id, response, audio_url=None)` → `assessment_id`
- `complete_session(session_id, overall_score)`
- `get_session(session_id)` → session + assessments
- `upload_audio(session_id, task, audio_bytes)` → Supabase Storage URL or None
- `save_report(session_id, user_id, pdf_path, summary)`
- `get_user_reports(user_id)` → list of report metadata
- `get_dashboard_data(user_id)` → sessions, assessments, streaks, goals
- `get_history_data(user_id)` → last 20 sessions with per-dimension sub-score averages
- `upsert_profile(user_id, display_name, goals)`
- `get_profile(user_id)` → profile row

## Report Generation Pipeline
```
GET /api/report/{session_id}
  ↓ db.get_session() → raw assessments
  ↓ _build_assessment_payload() → orchestrator-format JSON
  ↓ generate_narrative(gemma_input) → Gemma writes 6-section narrative
  ↓ generate_pdf(pdf_input, narrative, path) → ReportLab + matplotlib charts
  ↓ db.save_report() → persists to reports table
  → FileResponse (PDF)
```
Cached: if `backend/reports/{session_id}.pdf` exists, served immediately without re-running Gemma.

## Environment Setup
```bash
brew install ffmpeg
pip install -r requirements.txt  # includes uagents, matplotlib
cp .env.example .env             # fill in keys (ask teammate for values)
```

## Required .env Keys
```
GOOGLE_API_KEY=...       # Google AI Studio — Gemma narrative generation
SUPABASE_URL=...         # Supabase project URL
SUPABASE_KEY=...         # Supabase service role key (backend only, bypasses RLS)
AGENT_SEED=...           # Any string — seeds uAgent identity
ASI1_API_KEY=...         # ASI:One Agentverse (optional)
```

Frontend `.env.local`:
```
VITE_SUPABASE_URL=...         # Same Supabase URL
VITE_SUPABASE_ANON_KEY=...    # Supabase anon/public key (safe for browser)
VITE_API_URL=http://localhost:8000
```

## Running
```bash
# Backend (from repo root, with pipenv shell or virtualenv active)
python main.py

# Frontend
cd frontend && npm install && npm run dev

# Terminal test (no server needed)
python3 test_pipeline.py
```

## Key Architectural Decisions
- **whisper.cpp + faster-whisper in parallel**: cpp for speed (Metal), fw for confidence scores — merged result
- **librosa resampling in bytes_to_array**: pydub's built-in resampler has no anti-aliasing filter; librosa sinc resampler matches test_pipeline quality
- **Voice quality included in scoring**: jitter/shimmer/HNR contribute 10–17% of overall score per task
- **WER blended into pronunciation on read_sentence**: WER is the strongest articulation signal when a reference exists
- **Prosody on read_sentence is pitch-only**: rate CV not computed for scripted reading
- **Pataka is rhythm + voice_quality only**: Whisper can't transcribe pa-ta-ka; onset detection + parselmouth are the valid signals
- **FastAPI as agent bridge**: frontend never talks to Agentverse directly
- **Report PDF cached on disk**: Gemma call is ~15s; second request for same session is instant
- **Audio stored in Supabase Storage**: private bucket, keyed by session_id/task — useful for replay and clinical audit
