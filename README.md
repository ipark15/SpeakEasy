# SpeakEasy

AI-powered speech assessment + coaching platform. Three short tasks (~45s total) produce a scored profile across 5 dimensions, then route the user to specialized AI coaching agents for interactive practice.

---

## Getting Started

### Prerequisites

Make sure you have the following installed before anything else:

- **Python 3.11+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **ffmpeg** — required for audio decoding

```bash
brew install ffmpeg
```

---

### 1. Clone the repo

```bash
git clone https://github.com/ipark15/SpeakEasy.git
cd SpeakEasy
```

---

### 2. Set up environment variables

The `.env` file is **not committed to git** (it contains secret API keys). Ask a teammate to share it with you, then place it in the root of the repo:

```
SpeakEasy/
├── .env          ← put it here
├── backend/
├── frontend/
└── ...
```

The file should contain:

```
GOOGLE_API_KEY=...       # Google AI Studio — Gemma for narrative generation
SUPABASE_URL=...         # Supabase project URL
SUPABASE_KEY=...         # Supabase service role key (backend only)
AGENT_SEED=...           # Any random string — seeds the uAgent identity
ASI1_API_KEY=...         # ASI:One Agentverse (optional)
```

The frontend also needs its own env file. Create `frontend/.env.local`:

```
VITE_SUPABASE_URL=...         # Same Supabase project URL
VITE_SUPABASE_ANON_KEY=...    # Supabase anon/public key (safe for browser)
VITE_API_URL=http://localhost:8000
```

> **Note:** `SUPABASE_KEY` (service role) is backend-only and bypasses row-level security — never put it in the frontend. The frontend uses the anon key instead.

---

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Set up the database

Run the schema once in the **Supabase SQL Editor** ([app.supabase.com](https://app.supabase.com) → your project → SQL Editor):

```bash
# Copy the contents of this file and paste into Supabase SQL Editor
backend/db/schema.sql
```

This creates the `sessions`, `assessments`, `user_profiles`, `coach_messages`, and `reports` tables with row-level security enabled.

---

### 5. Start the backend

```bash
python main.py
```

The API will be running at `http://localhost:8000`. Test it:

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

---

### 6. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be running at `http://localhost:5173`.

---

## Project Structure

```
SpeakEasy/
├── backend/
│   ├── agents/              # Gemma-powered coaching agents (orchestrator + 5 coaches)
│   ├── db/
│   │   ├── schema.sql       # Run once in Supabase SQL Editor
│   │   └── queries.py       # All database functions
│   ├── models/schemas.py    # Pydantic request/response models
│   ├── routers/
│   │   ├── assess.py        # POST /api/assess, GET /api/session, GET /api/report
│   │   └── dashboard.py     # Dashboard, history, profile, export endpoints
│   ├── services/
│   │   ├── feature_extraction.py   # Whisper, pause, filler, WER, DDK extraction
│   │   ├── scoring.py              # Score computation (0–100 per dimension)
│   │   └── transcription.py        # faster-whisper wrapper
│   └── utils/audio.py       # WebM → float32 conversion via pydub/ffmpeg
├── frontend/
│   └── src/
│       ├── pages/           # Landing, Auth, Dashboard, Assess, Results, History, Profile, Settings
│       ├── components/      # Navbar, Card, Button, ScoreBadge
│       ├── hooks/           # useAuth (Supabase), useRecorder (MediaRecorder)
│       └── lib/
│           ├── api.ts       # All backend API calls
│           └── supabase.ts  # Supabase client
├── main.py                  # Uvicorn entry point
└── requirements.txt
```

---

## Assessment Flow

| Step | Task | Duration | What it measures |
|---|---|---|---|
| 1 | **Read Aloud** | ~10s | Clarity (WER), Pronunciation, Fluency, Prosody |
| 2 | **Pa-Ta-Ka** | ~8s | Rhythm (DDK rate, inter-syllable regularity) |
| 3 | **Free Speech** | ~20s | Fluency (WPM, fillers), Prosody (pitch variation), Pronunciation |

---

## Scoring

| Dimension | Inputs | Weight |
|---|---|---|
| Fluency | WPM + filler rate + pause rate | 25% |
| Clarity | Word Error Rate vs reference | 25% |
| Rhythm | DDK rate + syllable regularity | 25% |
| Prosody | Pitch std + energy variation | 15% |
| Voice Quality | Jitter + shimmer + HNR | 10% |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Smoke test |
| `POST` | `/api/session/start` | Create a new session, returns `session_id` |
| `POST` | `/api/assess` | Submit audio for one task, returns scores |
| `GET` | `/api/session/{id}` | Full session + all assessments |
| `GET` | `/api/report/{id}` | Generate (or retrieve) the clinical PDF report |
| `GET` | `/api/dashboard/{user_id}` | Streak, avg score, weekly chart data |
| `GET` | `/api/history/{user_id}` | All past sessions with sub-scores |
| `GET` | `/api/profile/{user_id}` | User profile stats |
| `POST` | `/api/profile` | Update display name / goals |
| `GET` | `/api/reports/{user_id}` | List sessions that have generated reports |
| `GET` | `/api/export/{user_id}/csv` | Download all assessments as CSV |
| `GET` | `/api/export/{user_id}/pdf` | Download summary PDF |

---

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Python + FastAPI + uvicorn |
| Transcription | faster-whisper `base.en` |
| Pitch / Voice | parselmouth (Praat) |
| Rhythm | librosa |
| AI Narrative | Gemma via Google AI Studio |
| Agents | uAgents / ASI:One Agentverse |
| Database | Supabase (Postgres + Auth) |
| Audio decode | pydub + ffmpeg |
