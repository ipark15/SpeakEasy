from __future__ import annotations
from backend.models.schemas import FeatureResult, ScoreBreakdown


def _tier(val: float, tiers: list[tuple[float, float, float]]) -> float:
    """
    Stepped gradient scorer. tiers is a list of (lo, hi, score) sorted by score desc.
    Returns the score of the first tier whose range contains val.
    val outside all tiers returns 0.
    """
    for lo, hi, pts in tiers:
        if lo <= val <= hi:
            return pts
    return 0.0


def score_fluency(f: FeatureResult, is_read_sentence: bool = False) -> float | None:
    if f.wpm is None:
        return None
    wpm = f.wpm
    duration = max(f.audio_duration, 1.0)

    # WPM (0–50 pts). Research norm: 120–160 optimal for clear speech.
    # Tiers: 100→85→70→50→0
    if is_read_sentence:
        wpm_pts = _tier(wpm, [
            (110, 180, 50.0),   # wider ideal — scripted reading varies more
            (95,  110, 37.5),
            (180, 205, 37.5),   # fast-but-clear still gets 75%
            (80,   95, 25.0),
            (205, 225, 25.0),
            (60,   80, 12.5),
            (225, 250, 12.5),
            (0,    60,  0.0),
        ])
    else:
        wpm_pts = _tier(wpm, [
            (120, 160, 50.0),
            (105, 120, 37.5),
            (160, 175, 37.5),
            (90,  105, 25.0),
            (175, 195, 25.0),
            (70,   90, 12.5),
            (195, 215, 12.5),
            (0,    70,  0.0),
        ])

    # Pause rate penalty (0–30 pts). Pauses per minute:
    # read_sentence: any pause mid-sentence is a hesitation signal
    # free_speech: some pauses are natural thinking time
    pause_rate = f.pause_count / (duration / 60.0)
    if is_read_sentence:
        # read_sentence: 1 pause/min is ok (natural breath), penalize beyond that
        pause_pts = _tier(pause_rate, [
            (0,   3, 30.0),
            (3,   6, 20.0),
            (6,  10, 10.0),
            (10, 999,  0.0),
        ])
    else:
        pause_pts = _tier(pause_rate, [
            (0,   2, 30.0),
            (2,   5, 18.0),
            (5,   9,  9.0),
            (9,  13,  3.0),
            (13, 999,  0.0),
        ])

    # Filler rate penalty (0–20 pts). Only meaningful for free_speech.
    filler_pts = 20.0
    if not is_read_sentence:
        transcript_fillers = f.filler_count or 0
        acoustic_fillers = f.acoustic_filler_count or 0
        filler_count = max(transcript_fillers, acoustic_fillers)
        filler_rate = filler_count / (duration / 60.0)
        filler_pts = _tier(filler_rate, [
            (0,   1, 20.0),
            (1,   3, 12.0),
            (3,   6,  5.0),
            (6,  10,  1.0),
            (10, 999,  0.0),
        ])

    return round(min(100.0, wpm_pts + pause_pts + filler_pts), 1)


def score_clarity(f: FeatureResult) -> float | None:
    if f.word_error_rate is None:
        return None
    wer = f.word_error_rate * 100.0
    return _tier(wer, [
        (0,   1, 100.0),
        (1,   4,  80.0),
        (4,   9,  58.0),
        (9,  16,  35.0),
        (16, 25,  15.0),
        (25, 999,  0.0),
    ])


def score_rhythm(f: FeatureResult) -> float | None:
    if f.rhythm_regularity is None or f.ddk_rate is None:
        return None

    # Regularity (0–60 pts). After median filter, good speech = 0.75–0.95.
    reg = f.rhythm_regularity
    reg_pts = _tier(reg, [
        (0.85, 1.00, 60.0),
        (0.72, 0.85, 45.0),
        (0.58, 0.72, 30.0),
        (0.45, 0.58, 15.0),
        (0.00, 0.45,  0.0),
    ])

    # DDK rate (0–40 pts). Clinical norm: 5.0–7.0 syl/sec.
    ddk = f.ddk_rate
    rate_pts = _tier(ddk, [
        (5.0, 7.0, 40.0),
        (4.2, 5.0, 28.0),
        (7.0, 8.2, 28.0),
        (3.5, 4.2, 16.0),
        (8.2, 9.0, 16.0),
        (0.0, 3.5,  0.0),
        (9.0, 999,  0.0),
    ])

    return round(min(100.0, reg_pts + rate_pts), 1)


def score_prosody(f: FeatureResult, weight_cv: bool = True) -> float | None:
    if f.pitch_std is None:
        return None

    # Pitch std (0–60 pts for read_sentence, 0–70 pts for free_speech).
    # Research norm for natural speech: 20–50 Hz std.
    # Reading aloud is more constrained: 15–40 Hz is natural.
    p = f.pitch_std
    if weight_cv:
        pitch_pts = _tier(p, [
            (20,  55, 70.0),
            (14,  20, 52.5),  # -25%
            (55,  68, 52.5),
            (8,   14, 35.0),  # -50%
            (68,  82, 35.0),
            (4,    8, 17.5),  # -75%
            (82,  96, 17.5),
            (0,    4,  0.0),
            (96, 999,  0.0),
        ])
    else:
        pitch_pts = _tier(p, [
            (15,  45, 60.0),
            (9,   15, 45.0),
            (45,  58, 45.0),
            (5,    9, 30.0),
            (58,  72, 30.0),
            (2,    5, 15.0),
            (72,  85, 15.0),
            (0,    2,  0.0),
            (85, 999,  0.0),
        ])

    if not weight_cv or f.speech_rate_cv is None:
        # read_sentence: pitch only. Max tier = 60pts → map to 85 max so it
        # doesn't trivially reach 100 — monotone speech still gets penalised.
        return round(min(100.0, (pitch_pts / 60.0) * 85.0), 1)

    # free_speech: pitch (70 pts) + rate CV (30 pts)
    cv = f.speech_rate_cv
    cv_pts = _tier(cv, [
        (0.20, 0.60, 30.0),
        (0.12, 0.20, 22.5),  # -25%
        (0.60, 0.85, 22.5),
        (0.06, 0.12, 15.0),  # -50%
        (0.85, 1.10, 15.0),
        (0.02, 0.06,  7.5),  # -75%
        (1.10, 1.40,  7.5),
        (0.00, 0.02,  0.0),
        (1.40, 999,   0.0),
    ])

    return round(min(100.0, pitch_pts + cv_pts), 1)


def score_voice_quality(f: FeatureResult) -> float | None:
    if f.jitter is None or f.shimmer is None or f.hnr is None:
        return None

    # Jitter (0–34 pts). Clinical threshold: < 1.0% relative jitter.
    jitter_pts = _tier(f.jitter, [
        (0.0, 0.5, 34.0),
        (0.5, 1.0, 25.0),
        (1.0, 1.5, 15.0),
        (1.5, 2.5,  6.0),
        (2.5, 999,  0.0),
    ])

    # Shimmer (0–33 pts). Clinical threshold: < 3.0%.
    shimmer_pts = _tier(f.shimmer, [
        (0.0, 1.5, 33.0),
        (1.5, 3.0, 22.0),
        (3.0, 5.0, 11.0),
        (5.0, 7.0,  4.0),
        (7.0, 999,  0.0),
    ])

    # HNR (0–33 pts). Clinical norm: > 20 dB is healthy voice.
    hnr_pts = _tier(f.hnr, [
        (25, 999, 33.0),
        (20,  25, 22.0),
        (15,  20, 11.0),
        (10,  15,  4.0),
        ( 0,  10,  0.0),
    ])

    return round(min(100.0, jitter_pts + shimmer_pts + hnr_pts), 1)


def score_pronunciation(f: FeatureResult) -> float | None:
    if f.avg_word_confidence is None:
        return None

    conf = f.avg_word_confidence
    conf_score = _tier(conf, [
        (0.90, 1.00, 100.0),
        (0.82, 0.90,  78.0),
        (0.72, 0.82,  55.0),
        (0.58, 0.72,  30.0),
        (0.00, 0.58,   0.0),
    ])

    # Penalize for each low-confidence word (below 0.75 confidence threshold).
    # Each low-conf word deducts points — even if average conf is high.
    total_words = len(f.word_timestamps) if f.word_timestamps else 1
    low_conf_words = [
        w for w in (f.word_timestamps or [])
        if w.confidence < 0.75
    ]
    low_conf_rate = len(low_conf_words) / max(total_words, 1)
    low_conf_penalty = _tier(low_conf_rate, [
        (0.00, 0.05,  0.0),   # up to 1 in 20 words: no penalty
        (0.05, 0.12, 10.0),   # ~1 in 10 words
        (0.12, 0.22, 20.0),   # ~1 in 5 words
        (0.22, 0.35, 35.0),   # ~1 in 4 words
        (0.35, 1.00, 50.0),   # more than 1 in 3 words
    ])

    base = conf_score - low_conf_penalty

    # On read_sentence, also blend with WER
    if f.word_error_rate is not None:
        wer = f.word_error_rate * 100.0
        wer_score = _tier(wer, [
            (0,   1, 100.0),
            (1,   4,  80.0),
            (4,   9,  58.0),
            (9,  16,  35.0),
            (16, 25,  15.0),
            (25, 999,  0.0),
        ])
        return round(max(0.0, base * 0.5 + wer_score * 0.5), 1)

    return round(max(0.0, base), 1)


# 5 dimensions — one per therapy agent
_WEIGHTS: dict[str, dict[str, float]] = {
    "read_sentence": {"clarity": 0.35, "pronunciation": 0.25, "fluency": 0.20, "prosody": 0.10, "voice_quality": 0.10},
    "pataka":        {"rhythm": 0.85, "voice_quality": 0.15},
    "free_speech":   {"fluency": 0.30, "prosody": 0.28, "pronunciation": 0.25, "voice_quality": 0.17},
}


def compute_scores(features: FeatureResult, task: str) -> ScoreBreakdown:
    fluency = clarity = rhythm = prosody = pronunciation = None

    if task == "read_sentence":
        fluency = score_fluency(features, is_read_sentence=True)
        clarity = score_clarity(features)
        prosody = score_prosody(features, weight_cv=False)
        pronunciation = score_pronunciation(features)

    elif task == "pataka":
        rhythm = score_rhythm(features)

    elif task == "free_speech":
        fluency = score_fluency(features, is_read_sentence=False)
        prosody = score_prosody(features, weight_cv=True)
        pronunciation = score_pronunciation(features)

    voice_quality = score_voice_quality(features)

    partial = ScoreBreakdown(
        fluency=fluency, clarity=clarity, rhythm=rhythm,
        prosody=prosody, voice_quality=voice_quality,
        pronunciation=pronunciation, overall=0.0,
    )

    weights = _WEIGHTS.get(task, _WEIGHTS["free_speech"])
    score_map = {
        "fluency": fluency, "clarity": clarity, "rhythm": rhythm,
        "prosody": prosody, "pronunciation": pronunciation,
    }
    total = weight_sum = 0.0
    for key, w in weights.items():
        val = score_map.get(key)
        if val is not None:
            total += val * w
            weight_sum += w
    partial.overall = round(total / weight_sum, 1) if weight_sum > 0 else 0.0
    return partial
