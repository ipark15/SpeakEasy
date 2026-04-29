#!/usr/bin/env python3
"""
seed_demo.py — Create a demo account with realistic mock data for the SpeakEasy demo.

Usage:
    python seed_demo.py

Requires .env to be present with SUPABASE_URL and SUPABASE_KEY (service role key).
Prints the demo login credentials when done.
"""

from __future__ import annotations
import os, sys, uuid, random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

import httpx
from supabase import create_client, Client
from supabase.client import ClientOptions

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

DEMO_EMAIL    = "demo@speakeasy.health"
DEMO_PASSWORD = "SpeakEasy2026!"
DEMO_NAME     = "Alex Rivera"

# ── Score trajectory: 3 weeks of gradual improvement ──────────────────────────
# Each entry: (days_ago, overall, fluency, clarity, rhythm, prosody, voice_quality, pronunciation)
SESSION_TRAJECTORY = [
    # Week 1 — struggling baseline
    (21, 54, 52, 48, 44, 56, 60, 50),
    (19, 56, 54, 50, 47, 57, 61, 52),
    (17, 58, 56, 52, 49, 59, 62, 54),
    # Week 2 — steady gains
    (14, 62, 60, 57, 54, 63, 65, 59),
    (12, 65, 63, 60, 58, 66, 67, 62),
    (10, 68, 66, 63, 62, 68, 69, 65),
    (8,  70, 68, 66, 65, 70, 71, 68),
    # Week 3 — recent sessions (strong finish for demo)
    (5,  74, 72, 70, 69, 74, 74, 71),
    (3,  77, 75, 73, 72, 76, 76, 74),
    (1,  81, 79, 78, 76, 80, 79, 78),
]

# ── Feedback text per dimension (indexed by quartile: 0=bad, 1=ok, 2=good) ───
FEEDBACK_TEMPLATES = {
    "fluency": [
        "Speech rate is slower than typical, with frequent mid-sentence pauses. Focus on continuous phrasing.",
        "Pacing is improving. Some hesitations remain but overall flow is more consistent.",
        "Fluency is near-typical. Transitions between phrases are smooth.",
    ],
    "clarity": [
        "Word error rate is elevated. Several consonant clusters are being reduced or dropped.",
        "Clarity is improving. A few target words still show substitution patterns.",
        "Articulation is precise. Reference sentence was reproduced accurately.",
    ],
    "rhythm": [
        "DDK rate is below 5 syllables/sec. Timing irregularity suggests reduced oro-motor coordination.",
        "Syllable sequencing is more regular. Rate approaching normal range.",
        "Rhythm is strong. DDK rate and inter-syllable timing are within normal limits.",
    ],
    "prosody": [
        "Pitch variation is limited, producing a flattened, monotone quality.",
        "Some pitch modulation is emerging. Stress patterns are becoming more natural.",
        "Prosody is expressive. Pitch contour and rate variation reflect natural intonation.",
    ],
}

TIPS_POOL = {
    "fluency": [
        "Practice reading aloud for 5 minutes daily to build speech automaticity.",
        "Use chunking — break sentences into short phrases and pause between them.",
        "Record yourself and listen back to notice hesitation patterns.",
    ],
    "clarity": [
        "Over-articulate target consonants during practice, then fade to natural speech.",
        "Slow down slightly on multisyllabic words to ensure full articulation.",
        "Mirror practice: watch your mouth in a mirror to monitor lip and tongue placement.",
    ],
    "rhythm": [
        "Try the pa-ta-ka drill for 30 seconds each morning to warm up oro-motor circuits.",
        "Tap a finger in time with syllables to reinforce rhythmic regularity.",
        "Start slow and gradually increase rate — accuracy first, speed second.",
    ],
    "prosody": [
        "Read poetry or scripts with exaggerated emotion to build pitch range.",
        "Hum a melody before speaking to activate pitch flexibility.",
        "Record a 30-second monologue and check for variation in loudness and pitch.",
    ],
}


def _score_label(score: float) -> int:
    if score < 60:
        return 0
    if score < 73:
        return 1
    return 2


def _mk_assessment(
    session_id: str,
    user_id: str,
    task: str,
    created_at: str,
    s_fluency: float,
    s_clarity: float,
    s_rhythm: float,
    s_prosody: float,
    s_voice: float,
    s_pronun: float,
) -> dict:
    """Build a realistic assessment row for the given task and scores."""
    rng = random.Random(session_id + task)

    # Jitter scores per-task using the per-task weights from CLAUDE.md
    if task == "read_sentence":
        overall = (
            s_clarity  * 0.35 +
            s_pronun   * 0.25 +
            s_fluency  * 0.20 +
            s_prosody  * 0.10 +
            s_voice    * 0.10
        )
    elif task == "pataka":
        overall = s_rhythm * 0.85 + s_voice * 0.15
    else:  # free_speech
        overall = (
            s_fluency  * 0.30 +
            s_prosody  * 0.28 +
            s_pronun   * 0.25 +
            s_voice    * 0.17
        )

    wpm = rng.uniform(105, 135) if s_fluency > 70 else rng.uniform(75, 105)
    ddk = rng.uniform(5.5, 7.5) if s_rhythm > 70 else rng.uniform(3.5, 5.5)
    pitch_std = rng.uniform(28, 45) if s_prosody > 70 else rng.uniform(10, 28)
    wer = rng.uniform(0.02, 0.10) if s_clarity > 70 else rng.uniform(0.15, 0.35)
    avg_conf = rng.uniform(0.82, 0.95) if s_pronun > 70 else rng.uniform(0.60, 0.82)
    jitter = rng.uniform(0.005, 0.012) if s_voice > 70 else rng.uniform(0.015, 0.035)
    shimmer = rng.uniform(0.04, 0.08) if s_voice > 70 else rng.uniform(0.09, 0.18)
    hnr = rng.uniform(18, 26) if s_voice > 70 else rng.uniform(8, 18)

    dim = "fluency" if task != "pataka" else "rhythm"
    label = _score_label(s_fluency if dim == "fluency" else s_rhythm)
    feedback_text = FEEDBACK_TEMPLATES[dim][label]
    tips = rng.sample(TIPS_POOL[dim], k=2)

    row: dict = {
        "session_id": session_id,
        "user_id": user_id,
        "task": task,
        "created_at": created_at,
        "audio_duration": rng.uniform(8, 22),

        # Transcription
        "transcript": (
            "Please call Stella and ask her to bring these things with her from the store."
            if task == "read_sentence"
            else ("pa ta ka pa ta ka pa ta ka pa ta ka" if task == "pataka"
                  else "I've been working on my speech a lot lately and I think it's getting better overall.")
        ),
        "word_timestamps": [],

        # Pauses
        "pause_count": rng.randint(1, 4),
        "avg_pause_duration": round(rng.uniform(0.15, 0.55), 2),
        "max_pause_duration": round(rng.uniform(0.5, 1.2), 2),
        "pauses": [],

        # Fluency
        "wpm": round(wpm, 1) if task != "pataka" else None,
        "filler_count": rng.randint(0, 3) if task == "free_speech" else 0,
        "filler_words": [],
        "speaking_time_ratio": round(rng.uniform(0.72, 0.92), 2),

        # Clarity
        "word_error_rate": round(wer, 3) if task == "read_sentence" else None,

        # Rhythm
        "syllable_intervals": [],
        "rhythm_regularity": round(rng.uniform(0.78, 0.96) if s_rhythm > 70 else rng.uniform(0.45, 0.72), 3) if task == "pataka" else None,
        "ddk_rate": round(ddk, 2) if task == "pataka" else None,

        # Prosody
        "pitch_mean": round(rng.uniform(160, 220), 1),
        "pitch_std": round(pitch_std, 2),
        "pitch_contour": [],
        "pitch_times": [],
        "jitter": round(jitter, 4),
        "shimmer": round(shimmer, 4),
        "hnr": round(hnr, 2),
        "energy_mean": round(rng.uniform(0.03, 0.12), 4),
        "energy_std": round(rng.uniform(0.01, 0.04), 4),

        # Pronunciation
        "avg_word_confidence": round(avg_conf, 3),
        "low_confidence_words": [],

        # Scores
        "score_fluency": round(s_fluency + rng.uniform(-2, 2), 1) if task != "pataka" else None,
        "score_clarity": round(s_clarity + rng.uniform(-2, 2), 1) if task == "read_sentence" else None,
        "score_rhythm": round(s_rhythm + rng.uniform(-2, 2), 1) if task == "pataka" else None,
        "score_prosody": round(s_prosody + rng.uniform(-2, 2), 1),
        "score_voice_quality": round(s_voice + rng.uniform(-2, 2), 1),
        "score_pronunciation": round(s_pronun + rng.uniform(-2, 2), 1) if task != "pataka" else None,
        "score_overall": round(overall, 1),

        # Feedback
        "feedback": feedback_text,
        "tips": tips,
        "audio_url": None,
    }
    return row


def main() -> None:
    db: Client = create_client(
        SUPABASE_URL, SUPABASE_KEY,
        options=ClientOptions(httpx_client=httpx.Client(http2=False)),
    )

    # ── 1. Create or reuse the demo auth user ────────────────────────────────
    print(f"Creating demo user: {DEMO_EMAIL} …")
    try:
        res = db.auth.admin.create_user({
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "email_confirm": True,
        })
        user_id = res.user.id
        print(f"  Created user id={user_id}")
    except Exception as e:
        msg = str(e)
        if "already been registered" in msg or "already exists" in msg or "duplicate" in msg.lower():
            # Find existing user
            users = db.auth.admin.list_users()
            found = next((u for u in users if u.email == DEMO_EMAIL), None)
            if not found:
                print(f"  ERROR: user exists but could not be found: {e}", file=sys.stderr)
                sys.exit(1)
            user_id = found.id
            print(f"  Reusing existing user id={user_id}")
        else:
            print(f"  ERROR creating user: {e}", file=sys.stderr)
            sys.exit(1)

    # ── 2. Upsert profile ────────────────────────────────────────────────────
    print("Upserting profile …")
    db.table("user_profiles").upsert({
        "id": user_id,
        "display_name": DEMO_NAME,
        "goals": {"fluency": 80, "clarity": 82, "rhythm": 78, "prosody": 80, "overall": 80},
    }).execute()

    # ── 3. Wipe any existing demo sessions for clean slate ───────────────────
    print("Clearing old demo sessions …")
    db.table("sessions").delete().eq("user_id", user_id).execute()

    # ── 4. Insert sessions + assessments ─────────────────────────────────────
    now = datetime.now(timezone.utc)
    tasks = ["read_sentence", "pataka", "free_speech"]

    for (days_ago, overall, s_flu, s_cla, s_rhy, s_pro, s_voi, s_pron) in SESSION_TRAJECTORY:
        session_ts = now - timedelta(days=days_ago)
        session_ts_str = session_ts.isoformat()

        # Insert session
        s_res = db.table("sessions").insert({
            "user_id": user_id,
            "status": "complete",
            "overall_score": float(overall),
            "created_at": session_ts_str,
            "completed_at": (session_ts + timedelta(minutes=2)).isoformat(),
        }).execute()
        session_id = s_res.data[0]["id"]

        # Insert 3 assessments
        for i, task in enumerate(tasks):
            task_ts = (session_ts + timedelta(seconds=30 * i)).isoformat()
            row = _mk_assessment(
                session_id, user_id, task, task_ts,
                s_flu, s_cla, s_rhy, s_pro, s_voi, s_pron,
            )
            db.table("assessments").insert(row).execute()

        print(f"  Session {days_ago:2d} days ago — overall={overall}")

    # ── 5. Done ──────────────────────────────────────────────────────────────
    print()
    print("=" * 50)
    print("Demo account ready!")
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")
    print(f"  Name:     {DEMO_NAME}")
    print(f"  User ID:  {user_id}")
    print("=" * 50)
    print("Narrative: 3 weeks of sessions, scores 54 → 81.")
    print("Lowest dimensions on latest session: Rhythm (76) and Clarity (78).")
    print()


if __name__ == "__main__":
    main()
