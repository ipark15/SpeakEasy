from __future__ import annotations
from backend.models.schemas import FeatureResult, ScoreBreakdown


def score_fluency(f: FeatureResult) -> float:
    wpm = f.wpm or 0.0
    # Use acoustic filler count if Whisper missed them (acoustic >= transcript count)
    transcript_fillers = f.filler_count or 0
    acoustic_fillers = f.acoustic_filler_count or 0
    filler_count = max(transcript_fillers, acoustic_fillers)
    duration = max(f.audio_duration, 1.0)

    # WPM (0–40 pts). Target 130–160 wpm
    if 130 <= wpm <= 160:
        wpm_pts = 40.0
    elif wpm < 130:
        wpm_pts = max(0.0, 40.0 * (wpm / 130.0))
    else:
        wpm_pts = max(0.0, 40.0 * (1.0 - (wpm - 160.0) / 100.0))

    # Filler rate penalty (0–30 pts)
    filler_rate = filler_count / (duration / 60.0)
    filler_pts = max(0.0, 30.0 - filler_rate * 3.0)

    # Pause rate penalty (0–30 pts)
    pause_rate = f.pause_count / (duration / 60.0)
    pause_pts = max(0.0, 30.0 - pause_rate * 2.0)

    return round(min(100.0, wpm_pts + filler_pts + pause_pts), 1)


def score_clarity(f: FeatureResult) -> float | None:
    if f.word_error_rate is None:
        return None
    return round(max(0.0, 100.0 * (1.0 - min(f.word_error_rate, 1.0))), 1)


def score_rhythm(f: FeatureResult) -> float | None:
    if f.rhythm_regularity is None or f.ddk_rate is None:
        return None
    reg_pts = f.rhythm_regularity * 60.0
    ddk = f.ddk_rate
    if 5.0 <= ddk <= 7.0:
        rate_pts = 40.0
    elif ddk < 5.0:
        rate_pts = max(0.0, 40.0 * (ddk / 5.0))
    else:
        rate_pts = max(0.0, 40.0 * (1.0 - (ddk - 7.0) / 5.0))
    return round(min(100.0, reg_pts + rate_pts), 1)


def score_prosody(f: FeatureResult) -> float | None:
    if f.pitch_std is None:
        return None

    # Pitch variation (0–60 pts). Target: 20–60 Hz std = expressive speech
    p = f.pitch_std
    if 20.0 <= p <= 60.0:
        pitch_pts = 60.0
    elif p < 20.0:
        pitch_pts = max(0.0, 60.0 * (p / 20.0))
    else:
        pitch_pts = max(0.0, 60.0 * (1.0 - (p - 60.0) / 60.0))

    # Speech rate variation (0–40 pts). CV 0.15–0.35 = natural pacing variation
    # Too flat (robotic) or too erratic both score lower
    cv = f.speech_rate_cv or 0.0
    if 0.15 <= cv <= 0.35:
        rate_pts = 40.0
    elif cv < 0.15:
        rate_pts = max(0.0, 40.0 * (cv / 0.15))
    else:
        rate_pts = max(0.0, 40.0 * (1.0 - (cv - 0.35) / 0.35))

    return round(min(100.0, pitch_pts + rate_pts), 1)


def score_voice_quality(f: FeatureResult) -> float | None:
    if f.jitter is None or f.shimmer is None or f.hnr is None:
        return None
    # Jitter: normal <1% (0–34 pts)
    jitter_pts = max(0.0, 34.0 * (1.0 - max(0.0, f.jitter - 1.0) / 5.0))
    # Shimmer: normal <3% (0–33 pts)
    shimmer_pts = max(0.0, 33.0 * (1.0 - max(0.0, f.shimmer - 3.0) / 10.0))
    # HNR: normal >20 dB (0–33 pts)
    hnr_pts = min(33.0, max(0.0, (f.hnr / 20.0) * 33.0))
    return round(min(100.0, jitter_pts + shimmer_pts + hnr_pts), 1)


def score_pronunciation(f: FeatureResult) -> float | None:
    if f.avg_word_confidence is None:
        return None
    return round(min(100.0, max(0.0, f.avg_word_confidence * 100.0)), 1)


_WEIGHTS: dict[str, dict[str, float]] = {
    "read_sentence":   {"clarity": 0.40, "voice_quality": 0.30, "fluency": 0.20, "pronunciation": 0.10},
    "pataka":          {"rhythm": 0.70, "voice_quality": 0.30},
    "sustained_vowel": {"voice_quality": 1.0},
    "free_speech":     {"fluency": 0.35, "prosody": 0.35, "pronunciation": 0.20, "voice_quality": 0.10},
}


def compute_scores(features: FeatureResult, task: str) -> ScoreBreakdown:
    fluency = clarity = rhythm = prosody = voice_quality = pronunciation = None

    if task in ("read_sentence", "free_speech"):
        fluency = score_fluency(features)
    if task == "read_sentence":
        clarity = score_clarity(features)
    if task == "pataka":
        rhythm = score_rhythm(features)
    if task == "free_speech":
        prosody = score_prosody(features)
    # sustained_vowel: voice_quality only (jitter/shimmer/HNR from parselmouth)

    voice_quality = score_voice_quality(features)
    pronunciation = score_pronunciation(features)

    partial = ScoreBreakdown(
        fluency=fluency, clarity=clarity, rhythm=rhythm,
        prosody=prosody, voice_quality=voice_quality,
        pronunciation=pronunciation, overall=0.0,
    )

    weights = _WEIGHTS.get(task, _WEIGHTS["free_speech"])
    score_map = {
        "fluency": fluency, "clarity": clarity, "rhythm": rhythm,
        "prosody": prosody, "voice_quality": voice_quality, "pronunciation": pronunciation,
    }
    total = weight_sum = 0.0
    for key, w in weights.items():
        val = score_map.get(key)
        if val is not None:
            total += val * w
            weight_sum += w
    partial.overall = round(total / weight_sum, 1) if weight_sum > 0 else 0.0
    return partial
