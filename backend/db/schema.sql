-- ============================================================
-- SpeakEasy — Supabase Schema
-- Run this once in the Supabase SQL Editor
-- ============================================================

-- ── Sessions ─────────────────────────────────────────────────
-- One row per full 3-task assessment run.
create table if not exists sessions (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid references auth.users(id) on delete cascade not null,
    status          text not null default 'in_progress'
                        check (status in ('in_progress', 'complete')),
    overall_score   real,           -- set after all 3 tasks complete
    created_at      timestamptz not null default now(),
    completed_at    timestamptz     -- set when status → complete
);

alter table sessions enable row level security;

create policy "users see own sessions"
    on sessions for all
    using (auth.uid() = user_id);


-- ── Assessments ───────────────────────────────────────────────
-- One row per task per session. Stores all features + scores + feedback.
create table if not exists assessments (
    id                      uuid primary key default gen_random_uuid(),
    session_id              uuid references sessions(id) on delete cascade not null,
    user_id                 uuid references auth.users(id) on delete cascade not null,
    task                    text not null
                                check (task in ('read_sentence', 'pataka', 'free_speech')),
    created_at              timestamptz not null default now(),

    -- Audio
    audio_duration          real not null,

    -- Transcription
    transcript              text,
    word_timestamps         jsonb,          -- List[TranscriptWord]

    -- Pauses (universal)
    pause_count             integer,
    avg_pause_duration      real,
    max_pause_duration      real,
    pauses                  jsonb,          -- List[PauseInfo]

    -- Fluency (read_sentence + free_speech)
    wpm                     real,
    filler_count            integer,
    filler_words            jsonb,          -- List[FillerEvent]
    speaking_time_ratio     real,

    -- Clarity (read_sentence)
    word_error_rate         real,

    -- Rhythm (pataka)
    syllable_intervals      jsonb,          -- List[float]
    rhythm_regularity       real,
    ddk_rate                real,

    -- Prosody — parselmouth (all tasks)
    pitch_mean              real,
    pitch_std               real,
    pitch_contour           jsonb,          -- List[float], downsampled
    pitch_times             jsonb,          -- List[float]
    jitter                  real,
    shimmer                 real,
    hnr                     real,
    energy_mean             real,
    energy_std              real,

    -- Pronunciation — Whisper confidence
    avg_word_confidence     real,
    low_confidence_words    jsonb,          -- List[{word, confidence, time}]

    -- Scores
    score_fluency           real,
    score_clarity           real,
    score_rhythm            real,
    score_prosody           real,
    score_voice_quality     real,
    score_pronunciation     real,
    score_overall           real not null,

    -- LLM feedback
    feedback                text,
    tips                    jsonb           -- List[str]
);

alter table assessments enable row level security;

create policy "users see own assessments"
    on assessments for all
    using (auth.uid() = user_id);

-- Fast lookups: session timeline, per-user history
create index if not exists assessments_session_id_idx on assessments(session_id);
create index if not exists assessments_user_id_created_idx on assessments(user_id, created_at desc);


-- ── User Profiles ────────────────────────────────────────────
-- Display name and per-metric goal targets. Streaks computed from session dates.
create table if not exists user_profiles (
    id           uuid primary key references auth.users(id) on delete cascade,
    display_name text,
    goals        jsonb,      -- e.g. {"fluency": 80, "clarity": 85, "overall": 75}
    created_at   timestamptz not null default now()
);

alter table user_profiles enable row level security;

create policy "users manage own profile"
    on user_profiles for all
    using (auth.uid() = id);


-- ── Coach Messages ────────────────────────────────────────────
-- Chat history between the user and therapy agents.
create table if not exists coach_messages (
    id          uuid primary key default gen_random_uuid(),
    session_id  uuid references sessions(id) on delete cascade not null,
    user_id     uuid references auth.users(id) on delete cascade not null,
    agent_type  text not null
                    check (agent_type in (
                        'orchestrator', 'rhythm_coach', 'clarity_coach',
                        'fluency_coach', 'prosody_coach', 'pronunciation_coach'
                    )),
    role        text not null check (role in ('user', 'assistant')),
    content     text not null,
    created_at  timestamptz not null default now()
);

alter table coach_messages enable row level security;

create policy "users see own messages"
    on coach_messages for all
    using (auth.uid() = user_id);

create index if not exists coach_messages_session_id_idx on coach_messages(session_id, created_at asc);


-- ── Reports ───────────────────────────────────────────────────
-- One row per generated clinical PDF report, keyed to a session.
create table if not exists reports (
    id           uuid primary key default gen_random_uuid(),
    session_id   uuid references sessions(id) on delete cascade not null unique,
    user_id      uuid references auth.users(id) on delete cascade not null,
    pdf_path     text not null,
    summary      text,
    generated_at timestamptz not null default now()
);

alter table reports enable row level security;

create policy "users see own reports"
    on reports for all
    using (auth.uid() = user_id);

create index if not exists reports_user_id_idx on reports(user_id, generated_at desc);
