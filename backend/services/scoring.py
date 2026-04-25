from __future__ import annotations
from backend.models.schemas import FeatureResult, ScoreBreakdown


def score_fluency(f: FeatureResult) -> float | None:
    if f.wpm is None:
        return None
    wpm = f.wpm
    transcript_fillers = f.filler_count or 0
    acoustic_fillers = f.acoustic_filler_count or 0
    filler_count = max(transcript_fillers, acoustic_fillers)
    duration = max(f.audio_duration, 1.0)

    # WPM (0–40 pts). Target 120–180 wpm
    if 120 <= wpm <= 180:
        wpm_pts = 40.0
    elif wpm < 120:
        wpm_pts = max(0.0, 40.0 * (wpm / 120.0))
    else:
        wpm_pts = max(0.0, 40.0 * (1.0 - (wpm - 180.0) / 80.0))

    # Filler rate penalty (0–30 pts) — only meaningful for free_speech
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

    # Regularity (0–60 pts). Scaled: 0.6 → 60pts, 0.0 → 0pts.
    reg_pts = min(60.0, (f.rhythm_regularity / 0.6) * 60.0)

    # DDK rate (0–40 pts). Target 4.5–8.0 syl/sec
    ddk = f.ddk_rate
    if 4.5 <= ddk <= 8.0:
        rate_pts = 40.0
    elif ddk < 4.5:
        rate_pts = max(0.0, 40.0 * (ddk / 4.5))
    else:
        rate_pts = max(0.0, 40.0 * (1.0 - (ddk - 8.0) / 4.0))

    return round(min(100.0, reg_pts + rate_pts), 1)


def score_prosody(f: FeatureResult, weight_cv: bool = True) -> float | None:
    if f.pitch_std is None:
        return None

    # Pitch variation (0–70 pts if no CV, 0–70 pts if CV present). Target 15–70 Hz std
    p = f.pitch_std
    if 15.0 <= p <= 70.0:
        pitch_pts = 70.0
    elif p < 15.0:
        pitch_pts = max(0.0, 70.0 * (p / 15.0))
    else:
        pitch_pts = max(0.0, 70.0 * (1.0 - (p - 70.0) / 60.0))

    if not weight_cv or f.speech_rate_cv is None:
        # read_sentence: pitch only, rescale to 100
        return round(min(100.0, (pitch_pts / 70.0) * 100.0), 1)

    # free_speech: pitch (70 pts) + rate CV (30 pts)
    cv = min(f.speech_rate_cv, 1.5)
    if 0.10 <= cv <= 0.80:
        rate_pts = 30.0
    elif cv < 0.10:
        rate_pts = max(0.0, 30.0 * (cv / 0.10))
    else:
        rate_pts = max(0.0, 30.0 * (1.0 - (cv - 0.80) / 0.70))

    return round(min(100.0, pitch_pts + rate_pts), 1)


def score_pronunciation(f: FeatureResult) -> float | None:
    if f.avg_word_confidence is None:
        return None
    # Blend WER into pronunciation for read_sentence (both signal articulation accuracy)
    if f.word_error_rate is not None:
        conf_score = f.avg_word_confidence * 100.0
        wer_score = max(0.0, 100.0 * (1.0 - min(f.word_error_rate, 1.0)))
        return round(min(100.0, conf_score * 0.6 + wer_score * 0.4), 1)
    return round(min(100.0, max(0.0, f.avg_word_confidence * 100.0)), 1)


# 5 dimensions — one per therapy agent
# Sustained vowel removed; pataka is rhythm-only
_WEIGHTS: dict[str, dict[str, float]] = {
    "read_sentence": {"clarity": 0.40, "pronunciation": 0.30, "fluency": 0.20, "prosody": 0.10},
    "pataka":        {"rhythm": 1.0},
    "free_speech":   {"fluency": 0.35, "prosody": 0.35, "pronunciation": 0.30},
}


def compute_scores(features: FeatureResult, task: str) -> ScoreBreakdown:
    fluency = clarity = rhythm = prosody = pronunciation = None

    if task == "read_sentence":
        fluency = score_fluency(features)
        clarity = score_clarity(features)
        prosody = score_prosody(features, weight_cv=False)
        pronunciation = score_pronunciation(features)

    elif task == "pataka":
        rhythm = score_rhythm(features)

    elif task == "free_speech":
        fluency = score_fluency(features)
        prosody = score_prosody(features, weight_cv=True)
        pronunciation = score_pronunciation(features)

    partial = ScoreBreakdown(
        fluency=fluency, clarity=clarity, rhythm=rhythm,
        prosody=prosody, voice_quality=None,
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
